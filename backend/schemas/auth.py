from pydantic import BaseModel, Field
from typing import Optional


class UserOut(BaseModel):
    """The caller's identity as the frontend needs it.

    `home` is the route this role lands on after login — served from the API so
    the role→landing-page mapping lives in one place (services/auth_service.py)
    rather than being duplicated in the React router.
    """
    username:     str
    role:         str
    role_label:   str
    display_name: str
    institution:  Optional[str] = None
    home:         str


class LoginResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int = Field(..., description="Token lifetime in seconds")
    user:         UserOut
