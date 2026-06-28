from sqlalchemy import Column, Integer, SmallInteger, String, Numeric, TIMESTAMP, text
from backend.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(120), nullable=False)
    gpa                 = Column(Numeric(3, 2), nullable=False)
    internships         = Column(SmallInteger, nullable=False, server_default="0")
    projects            = Column(SmallInteger, nullable=False, server_default="0")
    communication_score = Column(SmallInteger, nullable=False)
    program             = Column(String(80), nullable=False)
    enrollment_year     = Column(SmallInteger, nullable=False)
    created_at          = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
