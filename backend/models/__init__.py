from .student import Student
from .enrollment import Enrollment
from .job_posting import JobPosting
from .placement import Placement
from .user import User
from .governance import AuditLog, Scenario, AhpMatrix, ExpertValidation

# Importing this package registers every table with Base.metadata, which is
# what main.py relies on for create_all(). The names are the public surface.
__all__ = [
    "Student", "Enrollment", "JobPosting", "Placement", "User",
    "AuditLog", "Scenario", "AhpMatrix", "ExpertValidation",
]
