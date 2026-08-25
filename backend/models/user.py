from sqlalchemy import Column, Integer, String, TIMESTAMP, text
from db.database import Base


class User(Base):
    """Authentication + role-based access control.

    The only table on the API request path — see the note in db/schema.sql.

    institution_name scopes a UNIVERSITY user to their own institution's rows.
    It is always read from the JWT, never from a request parameter, so one
    university cannot ask for another's data.
    """
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    username         = Column(String(64), nullable=False, unique=True, index=True)
    password_hash    = Column(String(255), nullable=False)
    role             = Column(String(16), nullable=False, index=True)
    display_name     = Column(String(120), nullable=False)
    institution_name = Column(String(120), nullable=True)
    created_at       = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
