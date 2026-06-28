from sqlalchemy import Column, Integer, SmallInteger, String, TIMESTAMP, UniqueConstraint, text
from backend.db.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id         = Column(Integer, primary_key=True, index=True)
    program    = Column(String(80), nullable=False)
    year       = Column(SmallInteger, nullable=False)
    count      = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))

    __table_args__ = (UniqueConstraint("program", "year", name="uq_enrollments_program_year"),)
