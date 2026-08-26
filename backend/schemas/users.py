from pydantic import BaseModel, Field
from typing import Optional, Literal

# Mirrors the CHECK constraint on users.role in db/schema.sql. Using a Literal
# means an invalid role is rejected by validation with a clear message, before
# it ever reaches the database.
RoleName = Literal["ADMIN", "STUDENT", "MOE", "MOL", "UNIVERSITY"]

# Lowercase, no spaces — the username is the JWT `sub` and appears in URLs.
USERNAME_PATTERN = r"^[a-z0-9_.-]{3,64}$"

# Minimum only. No composition rules: length is the property that actually
# resists guessing, and character-class requirements mostly produce
# "Password1!" and a sticky note.
MIN_PASSWORD = 8


class UserOut(BaseModel):
    """An account as the admin console sees it. Never carries the hash."""
    username:         str
    role:             str
    display_name:     str
    institution_name: Optional[str] = None
    is_active:        bool
    created_at:       Optional[str] = None


class UserCreate(BaseModel):
    username:     str = Field(..., pattern=USERNAME_PATTERN,
                              description="Lowercase letters, digits, dot, dash or underscore")
    password:     str = Field(..., min_length=MIN_PASSWORD, max_length=128)
    role:         RoleName
    display_name: str = Field(..., min_length=1, max_length=120)
    # Required when role is UNIVERSITY; the service rejects the pairing
    # mismatch in both directions.
    institution_name: Optional[str] = Field(None, max_length=120)


class UserUpdate(BaseModel):
    """Every field optional — this is a PATCH.

    `username` is absent by design: it is the JWT subject, so changing it would
    orphan every token already issued to that account.
    """
    role:             Optional[RoleName] = None
    display_name:     Optional[str] = Field(None, min_length=1, max_length=120)
    institution_name: Optional[str] = Field(None, max_length=120)
    is_active:        Optional[bool] = None


class PasswordReset(BaseModel):
    """Admin path — sets a password without knowing the current one."""
    new_password: str = Field(..., min_length=MIN_PASSWORD, max_length=128)


class PasswordChange(BaseModel):
    """Self-service path — proves ownership with the current password."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password:     str = Field(..., min_length=MIN_PASSWORD, max_length=128)


class InstitutionOption(BaseModel):
    name:  str
    type:  str
    state: str
