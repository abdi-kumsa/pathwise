"""
User management — administrator only.

Thin router: every rule (self-lockout, last-admin, institution pairing,
username immutability) lives in services/auth_service.py so it holds regardless
of caller. This layer translates UserError into the right HTTP status.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from schemas.users import (
    UserOut, UserCreate, UserUpdate, PasswordReset, InstitutionOption,
)
from services import auth_service
from services.auth_service import UserError, log_audit, require_roles, ROLE_ADMIN

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)

# The admin's own identity, for the self-lockout guards.
_admin = require_roles(ROLE_ADMIN)


def _raise(exc: UserError):
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("")
def list_users():
    """Every account, active first. Password hashes are never returned.

    Wrapped in an object so provenance middleware can stamp the payload.
    """
    try:
        rows = auth_service.list_users()
        return {"n": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, actor: dict = Depends(_admin)):
    """Create an account. 409 if the username is taken."""
    try:
        row = auth_service.create_user(
            username     = body.username,
            password     = body.password,
            role         = body.role,
            display_name = body.display_name,
            institution  = body.institution_name,
        )
        log_audit(actor, "user_create", body.username, {"role": body.role})
        return row
    except UserError as e:
        _raise(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{username}", response_model=UserOut)
def update_user(username: str, body: UserUpdate, actor: dict = Depends(_admin)):
    """Update role, display name, institution or active status.

    The username itself cannot be changed — it is the JWT subject.
    """
    try:
        row = auth_service.update_user(
            username,
            actor        = actor["username"],
            role         = body.role,
            display_name = body.display_name,
            institution  = body.institution_name,
            active       = body.is_active,
        )
        action = "user_role_change" if body.role is not None else (
            "user_deactivate" if body.is_active is False else "user_update"
        )
        log_audit(actor, action, username, {
            "role": body.role, "is_active": body.is_active,
        })
        return row
    except UserError as e:
        _raise(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{username}/password", response_model=UserOut)
def reset_password(username: str, body: PasswordReset, actor: dict = Depends(_admin)):
    """Set a user's password without knowing the current one."""
    try:
        row = auth_service.set_password(username, body.new_password)
        log_audit(actor, "user_password_reset", username)
        return row
    except UserError as e:
        _raise(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{username}", response_model=UserOut)
def deactivate_user(username: str, actor: dict = Depends(_admin)):
    """Deactivate an account.

    A soft delete: the row survives, the action is reversible via PATCH, and
    the record that the account existed is preserved. The user cannot obtain a
    new token, and any token they already hold stops working within the
    status-cache TTL (see services/auth_service.py).

    Returns the updated account rather than 204 so the client can re-render the
    row without a second request.
    """
    try:
        row = auth_service.set_active(username, False, actor=actor["username"])
        log_audit(actor, "user_deactivate", username)
        return row
    except UserError as e:
        _raise(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{username}/permanent", status_code=204)
def delete_user_permanently(username: str, actor: dict = Depends(_admin)):
    """Erase an account and free its username.

    Deactivation (DELETE /api/users/{username}) is the normal path — reversible
    and keeps the record. This is for genuine erasure, and is deliberately not
    surfaced as a button in the admin console: an irreversible action one click
    away from a reversible one is a trap.

    Same self-lockout and last-admin guards apply.
    """
    try:
        auth_service.delete_user(username, actor=actor["username"])
        log_audit(actor, "user_delete", username)
    except UserError as e:
        _raise(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta/institutions", response_model=List[InstitutionOption])
def list_institutions():
    """Institutions a UNIVERSITY account may be scoped to.

    Read from the dataset, so the create form cannot offer an institution that
    would yield empty dashboards.

    Nested under /meta/ so it cannot collide with a username in /{username}.
    """
    try:
        from services import _datasets as ds
        return ds.institutions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
