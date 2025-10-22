"""
Pydantic schemas package.
All schemas use Pydantic v2 with from_attributes=True for SQLAlchemy compatibility.
"""

# Re-export all schemas
from .user_schemas import *
from .project_schemas import *
from .industry_schemas import *
from .cv_schemas import *
from .job_schemas import *
from .portfolio_schemas import *
from .community_schemas import *
