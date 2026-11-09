from pydantic import BaseModel, Field, field_validator
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

# bcrypt reads only the first 72 bytes of a password and silently ignores the
# rest, so a longer password would *look* stronger than it is. Oversize input is
# rejected with 422 instead (it previously surfaced as a 500 from bcrypt).
MAX_PASSWORD_BYTES = 72

# Small deny-list of the passwords most often tried first. Applied to every new
# password, signup included. Not a substitute for a breached-password API, but
# it removes the guesses that succeed in the first seconds of an attack.
COMMON_PASSWORDS = frozenset({
    "12345678", "123456789", "1234567890", "password", "password1", "password12",
    "password123", "qwerty123", "qwertyuiop", "11111111", "00000000", "abc12345",
    "iloveyou", "admin123", "welcome1", "letmein1", "pathwise", "pathwise1",
    "pathwise123", "changeme", "passw0rd", "87654321", "asdfghjk", "zaq12wsx",
})


def check_password(value: str) -> str:
    """Shared rules for every password a user or admin sets."""
    if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")
    if value.strip().lower() in COMMON_PASSWORDS:
        raise ValueError("That password is too common. Choose a less predictable one.")
    if len(set(value)) < 3:
        raise ValueError("Password must use at least three different characters.")
    return value


class UserOut(BaseModel):
    """An account as the admin console sees it. Never carries the hash."""
    username:         str
    role:             str
    display_name:     str
    institution_name: Optional[str] = None
    is_active:        bool
    cross_institution: bool = False
    created_at:       Optional[str] = None


class UserCreate(BaseModel):
    username:     str = Field(..., pattern=USERNAME_PATTERN,
                              description="Lowercase letters, digits, dot, dash or underscore")
    password:     str = Field(..., min_length=MIN_PASSWORD, max_length=128)
    role:         RoleName

    _password = field_validator("password")(classmethod(lambda cls, v: check_password(v)))
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
    # SCOPE.UNI.R2 elevated grant. UNIVERSITY accounts only; every change is
    # audited and takes effect on the next request (it is read from the DB,
    # not the token).
    cross_institution: Optional[bool] = None


class PasswordReset(BaseModel):
    """Admin path — sets a password without knowing the current one."""
    new_password: str = Field(..., min_length=MIN_PASSWORD, max_length=128)

    _password = field_validator("new_password")(classmethod(lambda cls, v: check_password(v)))


class PasswordChange(BaseModel):
    """Self-service path — proves ownership with the current password."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password:     str = Field(..., min_length=MIN_PASSWORD, max_length=128)

    _password = field_validator("new_password")(classmethod(lambda cls, v: check_password(v)))


class InstitutionOption(BaseModel):
    name:  str
    type:  str
    state: str
