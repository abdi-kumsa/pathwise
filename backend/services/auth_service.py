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
import time
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

def _row_to_dict(row, include_hash: bool = False) -> dict:
    """ORM row -> plain dict. The hash is opt-in so it cannot leak by accident."""
    out = {
        "username":         row.username,
        "role":             row.role,
        "display_name":     row.display_name,
        "institution_name": row.institution_name,
        "is_active":        bool(row.is_active),
        "created_at":       row.created_at.isoformat() if row.created_at else None,
    }
    if include_hash:
        out["password_hash"] = row.password_hash
    return out


def get_user(username: str) -> Optional[dict]:
    """Fetch one user as a plain dict, or None.

    Reuses the SQLAlchemy session factory in db/database.py. Returns dicts
    rather than ORM instances so nothing downstream depends on a live session.
    Includes password_hash because authenticate() needs it — callers that
    return data to a client must use list_users/get_user_public instead.
    """
    from db.database import SessionLocal
    from models.user import User

    session = SessionLocal()
    try:
        row = session.query(User).filter(User.username == username).first()
        return _row_to_dict(row, include_hash=True) if row else None
    finally:
        session.close()


def get_user_public(username: str) -> Optional[dict]:
    """Same as get_user but without the password hash — safe to serialise."""
    user = get_user(username)
    if user is None:
        return None
    return {k: v for k, v in user.items() if k != "password_hash"}


def authenticate(username: str, password: str) -> Optional[dict]:
    """Return the user dict on success, None on any failure.

    Deliberately does not distinguish "no such user", "wrong password" and
    "deactivated account" — the caller returns one generic 401 for all three,
    so the endpoint cannot be used to enumerate valid usernames or to discover
    that a particular account has been disabled.
    """
    user = get_user(username)
    if user is None:
        return None
    if not user.get("is_active", True):
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


# ── Active-status gate ────────────────────────────────────────────────────────
# get_current_user authorises from token claims with no database hit, which is
# what keeps it fast and lets it survive a brief Postgres outage. That property
# has a cost here: with an 8-hour token lifetime, checking is_active only at
# login would let a deactivated user keep full access for up to 8 hours —
# revoking access would revoke nothing.
#
# So the status is checked per request, behind a short TTL cache. The cache
# bounds the worst-case revocation lag at _ACTIVE_TTL seconds while keeping the
# amortised cost to roughly one query per user per TTL window. Admin actions
# evict the entry immediately, so a deactivation made through the API takes
# effect at once; the TTL ceiling only applies to changes made directly in the
# database.
#
# On lookup failure the last known value is served (defaulting to active), so a
# database blip degrades to the previous behaviour rather than locking every
# user out of the platform.

_ACTIVE_TTL = 30            # seconds
_active_cache: dict = {}    # username -> (checked_at_monotonic, is_active)


def is_active(username: str) -> bool:
    """Whether this account may currently be used. Cached for _ACTIVE_TTL."""
    now = time.monotonic()
    entry = _active_cache.get(username)
    if entry and (now - entry[0]) < _ACTIVE_TTL:
        return entry[1]

    try:
        from db.database import SessionLocal
        from models.user import User

        session = SessionLocal()
        try:
            row = (
                session.query(User.is_active)
                .filter(User.username == username)
                .first()
            )
            # A missing row means the account was hard-deleted out from under
            # a live token; treat that as inactive.
            active = bool(row[0]) if row else False
        finally:
            session.close()
    except Exception as exc:
        # Serve the last known value rather than failing closed on every
        # endpoint at once.
        log.warning("Active-status lookup failed for %s: %s", username, exc)
        return entry[1] if entry else True

    _active_cache[username] = (now, active)
    return active


def invalidate_active(username: str) -> None:
    """Drop a cached status so the next request re-reads it immediately."""
    _active_cache.pop(username, None)


def clear_active_cache() -> None:
    """Drop every cached status. Used by tests."""
    _active_cache.clear()


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

    # A token stays cryptographically valid until it expires, so a deactivated
    # account would otherwise keep access for the rest of the token lifetime.
    # 401 rather than 403: the session itself is no longer valid, and the
    # frontend's 401 interceptor signs them out cleanly.
    if not is_active(username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

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


# ── User management ───────────────────────────────────────────────────────────
# CRUD for the admin console. Every guard lives here rather than in the router,
# so the rules hold no matter which caller reaches them.


class UserError(Exception):
    """A user-management rule was violated.

    Carries an HTTP status so routers can translate without re-deriving which
    kind of failure it was.
    """
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _valid_institutions() -> set:
    """The institutions a UNIVERSITY account may be scoped to.

    Read from the dataset rather than hard-coded: an account pointed at an
    institution that is not in the data would pass every check here and then
    return empty dashboards, which looks like a bug rather than a mistake.
    """
    try:
        from . import _datasets as ds
        return {i["name"] for i in ds.institutions()}
    except Exception as exc:
        log.warning("Could not load institution list for validation: %s", exc)
        return set()


def _validate_institution(role: str, institution: Optional[str]) -> Optional[str]:
    """Enforce the UNIVERSITY↔institution pairing in both directions."""
    if role == ROLE_UNIVERSITY:
        if not institution:
            raise UserError("A University account must be linked to an institution.", 422)
        valid = _valid_institutions()
        if valid and institution not in valid:
            raise UserError(
                f"Unknown institution '{institution}'. "
                f"Expected one of: {', '.join(sorted(valid))}.",
                422,
            )
        return institution

    # Any other role carries no institution; silently dropping it here keeps
    # the DB CHECK constraint and the app in agreement.
    return None


def _active_admin_count(session, excluding: Optional[str] = None) -> int:
    from models.user import User
    q = session.query(User).filter(User.role == ROLE_ADMIN, User.is_active.is_(True))
    if excluding:
        q = q.filter(User.username != excluding)
    return q.count()


def list_users() -> list:
    """Every account, active first then alphabetical. Never includes hashes."""
    from db.database import SessionLocal
    from models.user import User

    session = SessionLocal()
    try:
        rows = session.query(User).order_by(User.is_active.desc(), User.username).all()
        return [_row_to_dict(r) for r in rows]
    finally:
        session.close()


def create_user(username: str, password: str, role: str,
                display_name: str, institution: Optional[str] = None) -> dict:
    from db.database import SessionLocal
    from models.user import User

    if role not in ALL_ROLES:
        raise UserError(f"Unknown role '{role}'.", 422)

    institution = _validate_institution(role, institution)

    session = SessionLocal()
    try:
        if session.query(User).filter(User.username == username).first():
            raise UserError(f"Username '{username}' is already taken.", 409)

        row = User(
            username         = username,
            password_hash    = hash_password(password),
            role             = role,
            display_name     = display_name,
            institution_name = institution,
            is_active        = True,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        log.info("User created: %s (%s)", username, role)
        return _row_to_dict(row)
    except UserError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_user(username: str, *, actor: str,
                role: Optional[str] = None,
                display_name: Optional[str] = None,
                institution: Optional[str] = None,
                active: Optional[bool] = None) -> dict:
    """Update a user. `actor` is the caller, for the self-lockout guards.

    Username is deliberately not updatable: it is the JWT `sub`, so changing it
    would orphan every token already issued to that person.
    """
    from db.database import SessionLocal
    from models.user import User

    session = SessionLocal()
    try:
        row = session.query(User).filter(User.username == username).first()
        if row is None:
            raise UserError(f"No such user '{username}'.", 404)

        # ── Guards ────────────────────────────────────────────────────────
        losing_admin = (
            row.role == ROLE_ADMIN
            and ((role is not None and role != ROLE_ADMIN) or active is False)
        )

        if losing_admin and username == actor:
            raise UserError(
                "You cannot remove your own administrator access — "
                "ask another administrator to do it.",
                400,
            )

        if losing_admin and _active_admin_count(session, excluding=username) == 0:
            raise UserError(
                "This is the only active administrator. Promote another account "
                "to administrator first, or the platform becomes unmanageable.",
                400,
            )

        # ── Apply ─────────────────────────────────────────────────────────
        new_role = role if role is not None else row.role
        if new_role not in ALL_ROLES:
            raise UserError(f"Unknown role '{new_role}'.", 422)

        # Re-validate whenever role or institution moves, so a role change
        # cannot leave a UNIVERSITY account without an institution.
        if role is not None or institution is not None:
            candidate = institution if institution is not None else row.institution_name
            row.institution_name = _validate_institution(new_role, candidate)

        row.role = new_role
        if display_name is not None:
            row.display_name = display_name
        if active is not None:
            row.is_active = active

        session.commit()
        session.refresh(row)

        # Role, institution and active status all affect authorisation, so the
        # cached status must not outlive the change.
        invalidate_active(username)
        log.info("User updated: %s by %s", username, actor)
        return _row_to_dict(row)

    except UserError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def set_active(username: str, active: bool, *, actor: str) -> dict:
    """Deactivate or reactivate. Soft delete — the row survives."""
    return update_user(username, actor=actor, active=active)


def delete_user(username: str, *, actor: str) -> None:
    """Permanently remove an account. Not reachable from the admin console UI.

    Deactivation is the normal path — it is reversible and keeps the record.
    This exists for genuine erasure (a mistyped account, a data-removal
    request) and for test teardown, which must be able to free a username so
    the suite can run repeatedly against the same database.

    Carries the same self-lockout and last-admin guards as deactivation: this
    is strictly more destructive, so it cannot be a way around them.
    """
    from db.database import SessionLocal
    from models.user import User

    session = SessionLocal()
    try:
        row = session.query(User).filter(User.username == username).first()
        if row is None:
            raise UserError(f"No such user '{username}'.", 404)

        if username == actor:
            raise UserError("You cannot delete your own account.", 400)

        if row.role == ROLE_ADMIN and _active_admin_count(session, excluding=username) == 0:
            raise UserError(
                "This is the only active administrator and cannot be deleted.",
                400,
            )

        session.delete(row)
        session.commit()
        invalidate_active(username)
        log.info("User permanently deleted: %s by %s", username, actor)
    except UserError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def set_password(username: str, new_password: str) -> dict:
    """Set a password without knowing the current one. Admin reset path."""
    from db.database import SessionLocal
    from models.user import User

    session = SessionLocal()
    try:
        row = session.query(User).filter(User.username == username).first()
        if row is None:
            raise UserError(f"No such user '{username}'.", 404)

        row.password_hash = hash_password(new_password)
        session.commit()
        session.refresh(row)
        invalidate_active(username)
        log.info("Password reset for %s", username)
        return _row_to_dict(row)
    except UserError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def change_own_password(username: str, current_password: str, new_password: str) -> None:
    """Self-service change. Requires the current password.

    Verifying the current password is what stops a stolen or unattended session
    from being used to lock the real owner out of their own account.
    """
    user = get_user(username)
    if user is None:
        raise UserError("No such user.", 404)

    if not verify_password(current_password, user["password_hash"]):
        raise UserError("Current password is incorrect.", 401)

    if current_password == new_password:
        raise UserError("The new password must be different from the current one.", 422)

    set_password(username, new_password)
