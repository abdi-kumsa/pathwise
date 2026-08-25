"""
Authentication and role-based access control.

Password hashing (bcrypt via passlib) + stateless JWTs (HS256 via python-jose).
There is no server-side session store: the token carries the caller's role and
institution, so any worker can authorise a request without a database round-trip
after login.

Two dependencies are exported for routers to use:

    get_current_user            -- 401 unless a valid Bearer token is present
    require_roles("MOE", ...)   -- 403 unless the caller holds one of the roles

ADMIN satisfies every require_roles check by design; see _ADMIN below.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

log = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
# JWT_SECRET must be overridden in any real deployment. The fallback exists so a
# fresh clone boots without configuration; it is logged as a warning at startup.
_DEFAULT_SECRET = "pathwise-dev-secret-change-me"
JWT_SECRET     = os.getenv("JWT_SECRET", _DEFAULT_SECRET)
JWT_ALGORITHM  = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))   # 8h — a working day

# ── Roles ─────────────────────────────────────────────────────────────────────
ROLE_ADMIN      = "ADMIN"
ROLE_STUDENT    = "STUDENT"
ROLE_MOE        = "MOE"
ROLE_MOL        = "MOL"
ROLE_UNIVERSITY = "UNIVERSITY"

ALL_ROLES = (ROLE_ADMIN, ROLE_STUDENT, ROLE_MOE, ROLE_MOL, ROLE_UNIVERSITY)

# ADMIN is a superset of every other role rather than a role with its own
# permission list. Keeping this in one place means a new router cannot
# accidentally lock the administrator out of its own system.
_ADMIN = ROLE_ADMIN

ROLE_LABELS = {
    ROLE_ADMIN:      "Administrator",
    ROLE_STUDENT:    "Student",
    ROLE_MOE:        "Ministry of Education",
    ROLE_MOL:        "Ministry of Labour",
    ROLE_UNIVERSITY: "University",
}

# Where each role lands after login. The frontend reads this from /api/auth/me
# so the landing route is defined once, on the server.
ROLE_HOME = {
    ROLE_ADMIN:      "/admin/overview",
    ROLE_STUDENT:    "/student/careers",
    ROLE_MOE:        "/moe/overview",
    ROLE_MOL:        "/mol/overview",
    ROLE_UNIVERSITY: "/university/overview",
}

# ── Password hashing ──────────────────────────────────────────────────────────
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time compare. Returns False rather than raising on a malformed
    hash, so a corrupt row cannot 500 the login endpoint."""
    try:
        return _pwd.verify(plain, hashed)
    except Exception:
        return False


# ── Tokens ────────────────────────────────────────────────────────────────────

def create_access_token(username: str, role: str, institution: Optional[str] = None) -> str:
    """Mint a signed JWT.

    `institution` is embedded in the token, not looked up per request, because
    it is the row-scoping key for UNIVERSITY users — putting it in the signed
    payload means it cannot be tampered with client-side.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub":  username,
        "role": role,
        "institution": institution,
        "iat":  now,
        "exp":  now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate. Raises JWTError on a bad signature or expiry."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ── User lookup ───────────────────────────────────────────────────────────────

def get_user(username: str) -> Optional[dict]:
    """Fetch one user as a plain dict, or None.

    Reuses the SQLAlchemy session factory in db/database.py. Returns dicts
    rather than ORM instances so nothing downstream depends on a live session.
    """
    from db.database import SessionLocal
    from models.user import User

    session = SessionLocal()
    try:
        row = session.query(User).filter(User.username == username).first()
        if row is None:
            return None
        return {
            "username":         row.username,
            "password_hash":    row.password_hash,
            "role":             row.role,
            "display_name":     row.display_name,
            "institution_name": row.institution_name,
        }
    finally:
        session.close()


def authenticate(username: str, password: str) -> Optional[dict]:
    """Return the user dict on success, None on any failure.

    Deliberately does not distinguish "no such user" from "wrong password" —
    the caller returns one generic 401 either way, so the endpoint cannot be
    used to enumerate valid usernames.
    """
    user = get_user(username)
    if user is None:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


# ── FastAPI dependencies ──────────────────────────────────────────────────────
# auto_error=False so we raise our own 401 with a consistent body shape rather
# than FastAPI's default, which differs between "no header" and "bad scheme".
_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_UNAUTHORISED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: Optional[str] = Depends(_oauth2)) -> dict:
    """Resolve the caller from their Bearer token, or 401.

    The returned dict is built from token claims only — no database hit — so
    authorisation stays fast and works even if Postgres is briefly unavailable
    after login.
    """
    if not token:
        raise _UNAUTHORISED

    try:
        claims = decode_token(token)
    except JWTError:
        raise _UNAUTHORISED

    username = claims.get("sub")
    role     = claims.get("role")
    if not username or role not in ALL_ROLES:
        raise _UNAUTHORISED

    return {
        "username":    username,
        "role":        role,
        "institution": claims.get("institution"),
    }


def require_roles(*roles: str):
    """Dependency factory: allow only the listed roles (plus ADMIN).

        @router.get("/x", dependencies=[Depends(require_roles(ROLE_MOE))])

    Returns the user dict, so a route can also take it as a parameter when it
    needs the caller's institution for row scoping.
    """
    allowed = set(roles) | {_ADMIN}

    def _guard(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role {user['role']} cannot access this resource. "
                    f"Requires one of: {', '.join(sorted(allowed))}."
                ),
            )
        return _guard_scope_check(user)

    return _guard


def _guard_scope_check(user: dict) -> dict:
    """A UNIVERSITY token with no institution claim cannot be row-scoped, so it
    is rejected rather than silently falling back to all-institution access."""
    if user["role"] == ROLE_UNIVERSITY and not user.get("institution"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="University account is not linked to an institution.",
        )
    return user


def warn_if_insecure() -> None:
    """Called once at startup so a default signing key is never silent."""
    if JWT_SECRET == _DEFAULT_SECRET:
        log.warning(
            "JWT_SECRET is unset — using the built-in development key. "
            "Set JWT_SECRET in .env before deploying anywhere real."
        )
