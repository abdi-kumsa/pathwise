from sqlalchemy import Column, Integer, Numeric, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base


class AuditLog(Base):
    """Views, exports, queries, model runs and scenario actions (Wave 7)."""
    __tablename__ = "audit_log"

    id         = Column(Integer, primary_key=True)
    actor      = Column(String(64), nullable=False, index=True)
    role       = Column(String(16))
    action     = Column(String(64), nullable=False)
    resource   = Column(String(255))
    payload    = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))


class Scenario(Base):
    """Persisted what-if runs. Purpose: stop scenarios being mistaken for official forecasts."""
    __tablename__ = "scenarios"

    id           = Column(Integer, primary_key=True)
    name         = Column(String(120), nullable=False)
    owner        = Column(String(64), nullable=False, index=True)
    assumptions  = Column(JSONB, nullable=False)
    status       = Column(String(24), nullable=False, server_default=text("'draft'"), index=True)
    created_at   = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))


class AhpMatrix(Base):
    """DOC1 step 7 pairwise matrices. Never blended into a learner's loss."""
    __tablename__ = "ahp_matrices"

    id                 = Column(Integer, primary_key=True)
    model              = Column(String(8), nullable=False)
    matrix             = Column(JSONB, nullable=False)
    consistency_ratio  = Column(Numeric(8, 4))
    created_at         = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))


class ExpertValidation(Base):
    """DOC1 step 2 domain-expert sign-off per spec id."""
    __tablename__ = "expert_validations"

    id          = Column(Integer, primary_key=True)
    spec_id     = Column(String(32), nullable=False, index=True)
    expert_role = Column(String(64), nullable=False)
    verdict     = Column(String(24), nullable=False)
    notes       = Column(Text)
    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
