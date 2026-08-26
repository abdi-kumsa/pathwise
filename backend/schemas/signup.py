"""
Self-registration schemas.

Always creates a STUDENT account. No role picker, no institution — students get
career exploration and market data but are never scoped to a university's
internal metrics. Ministry/university/admin accounts are provisioned by an
administrator from the console.
"""
from pydantic import BaseModel, Field, field_validator


class SignUpRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=200)

    @field_validator('username')
    @classmethod
    def username_lowercase_and_valid(cls, v: str) -> str:
        import re
        if not re.match(r'^[a-z0-9_.-]+$', v):
            raise ValueError(
                'Username may only contain lowercase letters, digits, dot, dash or underscore'
            )
        return v.lower()
