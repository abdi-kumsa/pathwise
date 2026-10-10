import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth import LoginResponse, UserOut
from schemas.users import PasswordChange
from schemas.signup import SignUpRequest
from services import auth_service

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
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Exchange username + password for a JWT.

    Accepts the standard OAuth2 password form so FastAPI's /docs "Authorize"
    button works against this endpoint with no extra configuration.

    Returns one generic 401 for both an unknown username and a wrong password,
    so the endpoint cannot be used to discover which accounts exist.
    """
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(
        username    = user["username"],
        role        = user["role"],
        institution = user.get("institution_name"),
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


@router.post("/change-password", status_code=204)
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
    """
    try:
        auth_service.change_own_password(
            user["username"], body.current_password, body.new_password
        )
    except auth_service.UserError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        log.error("Password change failed for %s: %s", user["username"], exc)
        raise HTTPException(status_code=500, detail="Could not change password.")


@router.get("/roles", tags=["Authentication"])
def list_roles():
    """Public: the role vocabulary, for the login page's demo-account hints."""
    return [
        {"role": r, "label": auth_service.ROLE_LABELS[r], "home": auth_service.ROLE_HOME[r]}
        for r in auth_service.ALL_ROLES
    ]


@router.post("/signup", response_model=LoginResponse, status_code=201)
def signup(body: SignUpRequest):
    """
    Self-registration: creates a STUDENT account and returns a signed-in session.

    No role picker, no institution — students get career exploration and market
    data but are never scoped to a university's internal metrics. Ministry,
    university and admin accounts are provisioned by an administrator.

    Returns 409 if the username is already taken, 422 on validation failure.
    """
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


_LEFTOVER_PATHS = {
    "/student/careers", "/student/evaluator", "/student/salary", "/student/market",
    "/university/expansion", "/university/benchmark", "/university/enrollment",
    "/moe/fields", "/moe/quadrant", "/moe/labour",
    "/mol/emerging", "/mol/supply-demand", "/mol/regional",
}


@router.post("/page-view")
def page_view(body: dict, user: dict = Depends(auth_service.get_current_user)):
    """DOC2 W.ADM.08 — record a widget-route view. Not a keystroke logger."""
    path = str((body or {}).get("path") or "")[:200]
    if not path.startswith("/"):
        raise HTTPException(status_code=422, detail="path must be an absolute route")
    if path in _LEFTOVER_PATHS:
        return {"logged": False, "reason": "leftover_tool"}
    auth_service.log_audit(user, "page_view", path)
    return {"logged": True}

