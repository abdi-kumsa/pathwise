import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth import LoginResponse, UserOut
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


@router.get("/roles", tags=["Authentication"])
def list_roles():
    """Public: the role vocabulary, for the login page's demo-account hints."""
    return [
        {"role": r, "label": auth_service.ROLE_LABELS[r], "home": auth_service.ROLE_HOME[r]}
        for r in auth_service.ALL_ROLES
    ]
