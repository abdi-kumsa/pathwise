from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP, text
from db.database import Base


class User(Base):
    """Authentication + role-based access control.

    On the API request path together with the Wave 1.5 governance tables
    (see db/schema.sql). Dashboard analytics still read parquet/CSV.

    institution_name scopes a UNIVERSITY user to their own institution's rows.
    It is always read from the JWT, never from a request parameter, so one
    university cannot ask for another's data.

    is_active is a soft delete: accounts are deactivated rather than removed so
    the record survives and the action is reversible. An inactive user cannot
    obtain a token, and an already-issued one stops working within the
    status-cache TTL in services/auth_service.py.
    """
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    username         = Column(String(64), nullable=False, unique=True, index=True)
    password_hash    = Column(String(255), nullable=False)
    role             = Column(String(16), nullable=False, index=True)
    display_name     = Column(String(120), nullable=False)
    institution_name = Column(String(120), nullable=True)
    is_active        = Column(Boolean, nullable=False, server_default=text("TRUE"), index=True)
    cross_institution = Column(Boolean, nullable=False, server_default=text("FALSE"))
    program          = Column(String(120), nullable=True)
    field            = Column(String(120), nullable=True)
    enrollment_year  = Column(Integer, nullable=True)
    # Incremented on any change that must end existing sessions: password,
    # role or institution. Tokens carry the version they were issued under.
    token_version    = Column(Integer, nullable=False, server_default=text("0"))
    created_at       = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
