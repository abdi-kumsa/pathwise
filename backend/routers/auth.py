import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth import LoginResponse, UserOut
from schemas.users import PasswordChange
from schemas.signup import SignUpRequest
from services import auth_service
from services import rate_limit

# Only failed sign-ins count, so legitimate users are never throttled — even a
# whole lecture hall signing in from one campus IP at the start of class.
#   per (IP, username): 10 failures / 5 min  — guessing one account
#   per IP:             50 failures / 5 min  — stuffing many accounts
_LOGIN_FAIL_LIMIT = 10
_LOGIN_FAIL_IP_LIMIT = 50
_LOGIN_FAIL_WINDOW = 300.0

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_out(user: dict) -> UserOut:
    role = user["role"]
    return UserOut(
        username     = user["username"],
        role         = role,
        role_label   = auth_service.ROLE_LABELS.get(role, role),
        display_name = user.get("display_name") or user["username"],
        institution  = user.get("institution_name") or user.get("institution"),
        home         = auth_service.ROLE_HOME.get(role, "/"),
    )


@router.post("/login", response_model=LoginResponse)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    """Exchange username + password for a JWT.

    Accepts the standard OAuth2 password form so FastAPI's /docs "Authorize"
    button works against this endpoint with no extra configuration.

    Returns one generic 401 for both an unknown username and a wrong password,
    so the endpoint cannot be used to discover which accounts exist.
    """
    ip = rate_limit.client_ip(request)
    fail_key = f"login-fail:{ip}:{form.username.strip().lower()}"
    ip_fail_key = f"login-fail-ip:{ip}"
    retry = (
        rate_limit.is_blocked(fail_key, _LOGIN_FAIL_LIMIT, _LOGIN_FAIL_WINDOW)
        or rate_limit.is_blocked(ip_fail_key, _LOGIN_FAIL_IP_LIMIT, _LOGIN_FAIL_WINDOW)
    )
    if retry is not None:
        # Checked before the password so a locked-out guesser learns nothing,
        # even from a correct guess.
        log.warning("Login locked out for %s", fail_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed sign-in attempts. Please wait and try again.",
            headers={"Retry-After": str(retry)},
        )

    try:
        user = auth_service.authenticate(form.username, form.password)
    except Exception as exc:
        # The users table is the only thing on the request path that needs
        # Postgres. Surface an outage as 503 rather than a misleading 401.
        log.error("Login failed — user store unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable. Is the database running?",
        )

    if user is None:
        rate_limit.record(fail_key)
        rate_limit.record(ip_fail_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(
        username    = user["username"],
        role        = user["role"],
        institution = user.get("institution_name"),
        version     = user.get("token_version", 0),
    )

    log.info("Login: %s (%s)", user["username"], user["role"])

    return LoginResponse(
        access_token = token,
        expires_in   = auth_service.JWT_EXPIRE_MINUTES * 60,
        user         = _user_out(user),
    )


@router.get("/me", response_model=UserOut)
def read_me(user: dict = Depends(auth_service.get_current_user)):
    """Echo the current caller. The frontend calls this on boot to rehydrate a
    session from a stored token without asking for credentials again.

    Built from token claims, so it stays available if Postgres is down after
    login. display_name is re-read from the store when reachable, falling back
    to the username otherwise.
    """
    try:
        stored = auth_service.get_user(user["username"])
    except Exception:
        stored = None

    merged = {**user, "display_name": (stored or {}).get("display_name") or user["username"]}
    return _user_out(merged)


@router.post("/refresh", response_model=LoginResponse)
def refresh(user: dict = Depends(auth_service.get_current_user)):
    """Exchange a still-valid token for a fresh one.

    Lets the frontend keep an active session going without a long token
    lifetime. The new token carries the account's *current* role, institution
    and version, so a refresh can never extend permissions that were revoked.
    """
    stored = auth_service.get_user(user["username"]) or {}
    token = auth_service.create_access_token(
        username=user["username"], role=user["role"],
        institution=user.get("institution"),
        version=stored.get("token_version", 0),
    )
    return LoginResponse(
        access_token=token,
        expires_in=auth_service.JWT_EXPIRE_MINUTES * 60,
        user=_user_out({**stored, **user}),
    )


@router.post("/change-password", response_model=LoginResponse)
def change_password(
    body: PasswordChange,
    user: dict = Depends(auth_service.get_current_user),
):
    """Change your own password. Any role.

    Lives on the auth router rather than /api/users because it is about the
    caller's own account, not administration — every role needs it, including
    the four that can never reach the admin console.

    The current password is required: without it, an unattended session could
    be used to lock the real owner out of their own account.

    Changing the password ends every existing session, so this returns a
    fresh token for the caller's own session.
    """
    # Throttle wrong *current* passwords only: that is the guessing attack a
    # stolen session enables. Validation failures and successes do not count.
    fail_key = f"change-password-fail:{user['username']}"
    retry = rate_limit.is_blocked(fail_key, 5, 300)
    if retry is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many incorrect current-password attempts. Please wait and try again.",
            headers={"Retry-After": str(retry)},
        )
    try:
        auth_service.change_own_password(
            user["username"], body.current_password, body.new_password
        )
        auth_service.log_audit(user, "password_change", user["username"], {"self_service": True})
    except auth_service.UserError as exc:
        if exc.status_code == 401:
            rate_limit.record(fail_key)
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        log.error("Password change failed for %s: %s", user["username"], exc)
        raise HTTPException(status_code=500, detail="Could not change password.")
    stored = auth_service.get_user(user["username"]) or {}
    token = auth_service.create_access_token(
        username=user["username"], role=user["role"],
        institution=user.get("institution"),
        version=stored.get("token_version", 0),
    )
    return LoginResponse(
        access_token=token,
        expires_in=auth_service.JWT_EXPIRE_MINUTES * 60,
        user=_user_out({**stored, **user}),
    )


@router.get("/roles", tags=["Authentication"])
def list_roles():
    """Public: the role vocabulary, for the login page's demo-account hints."""
    return [
        {"role": r, "label": auth_service.ROLE_LABELS[r], "home": auth_service.ROLE_HOME[r]}
        for r in auth_service.ALL_ROLES
    ]


@router.post("/signup", response_model=LoginResponse, status_code=201)
def signup(body: SignUpRequest, request: Request):
    """
    Self-registration: creates a STUDENT account and returns a signed-in session.

    No role picker, no institution — students get career exploration and market
    data but are never scoped to a university's internal metrics. Ministry,
    university and admin accounts are provisioned by an administrator.

    Returns 409 if the username is already taken, 422 on validation failure,
    429 after 20 valid attempts per minute (100 per hour) from one client IP.
    The limit is applied after body validation: a 422 costs nothing, while a
    valid attempt costs a bcrypt hash and possibly an account. It is sized for
    a class registering together from one campus network (one shared IP), not
    for a single person.
    """
    ip = rate_limit.client_ip(request)
    rate_limit.hit(f"signup:ip:{ip}", 20, 60)
    rate_limit.hit(f"signup-hour:ip:{ip}", 100, 3600)
    try:
        user = auth_service.create_user(
            username=body.username,
            password=body.password,
            role="STUDENT",
            display_name=body.display_name,
            institution=None,
        )
    except auth_service.UserError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        log.error("Sign-up failed for %s: %s", body.username, exc)
        raise HTTPException(status_code=500, detail="Could not create account.")

    # Sign them in immediately rather than making them re-type credentials.
    token = auth_service.create_access_token(
        user["username"], user["role"], user.get("institution")
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=auth_service.JWT_EXPIRE_MINUTES * 60,
        user=_user_out(user),
    )


# Routes a page-view may name. Anything else is acknowledged but not stored,
# so the audit log cannot be filled with arbitrary strings (audit S9).
_PAGE_VIEW_ROUTE = re.compile(r"^/(account|(student|university|moe|mol|admin)/[a-z0-9-]{2,40})$")

_LEFTOVER_PATHS = {
    "/student/careers", "/student/evaluator", "/student/salary", "/student/market",
    "/university/expansion", "/university/benchmark", "/university/enrollment",
    "/moe/fields", "/moe/quadrant", "/moe/labour",
    "/mol/emerging", "/mol/supply-demand", "/mol/regional",
}


@router.post("/page-view")
def page_view(body: dict, user: dict = Depends(rate_limit.per_user("page-view", 60, 60))):
    """DOC2 W.ADM.08 — record a widget-route view. Not a keystroke logger."""
    path = str((body or {}).get("path") or "")[:200]
    if not path.startswith("/"):
        raise HTTPException(status_code=422, detail="path must be an absolute route")
    if path in _LEFTOVER_PATHS:
        return {"logged": False, "reason": "leftover_tool"}
    if not _PAGE_VIEW_ROUTE.match(path):
        return {"logged": False, "reason": "unknown_route"}
    auth_service.log_audit(user, "page_view", path)
    return {"logged": True}

