from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from backend.db.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id              = Column(Integer, primary_key=True, index=True)
    company         = Column(String(120), nullable=False)
    title           = Column(String(150), nullable=False)
    location        = Column(String(100), nullable=False)
    skills_required = Column(ARRAY(TEXT), nullable=False, server_default=text("'{}'"))
    salary_min      = Column(Numeric(10, 2), nullable=True)
    salary_max      = Column(Numeric(10, 2), nullable=True)
    source          = Column(String(80), nullable=True)
    posted_date     = Column(Date, nullable=False)
    is_internship   = Column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at      = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
