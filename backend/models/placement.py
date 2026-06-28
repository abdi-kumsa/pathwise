from sqlalchemy import Column, Integer, SmallInteger, String, Numeric, Boolean, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from backend.db.database import Base


class Placement(Base):
    __tablename__ = "placements"

    id               = Column(Integer, primary_key=True, index=True)
    student_id       = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    company          = Column(String(120), nullable=True)
    role             = Column(String(150), nullable=True)
    salary           = Column(Numeric(10, 2), nullable=True)
    time_to_hire     = Column(SmallInteger, nullable=True)
    placed           = Column(Boolean, nullable=False, server_default=text("FALSE"))
    placement_status = Column(String(20), nullable=True)
    created_at       = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))

    student = relationship("Student", backref="placements")
