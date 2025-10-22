"""
Business logic services package.
All services use async PostgreSQL operations with SQLAlchemy 2.0+.
"""

from .auth_service import auth_service
from .user_service import user_service  
# from .project_service import project_service  # TODO: Fix project service schema mismatches
# from .cv_service import cv_service  # TODO: Fix CV service model name mismatches
# from .job_service import job_service  # TODO: Fix job service import issues

__all__ = [
    "auth_service",
    "user_service",
    # "project_service",  # TODO: Fix schema mismatches
    # "cv_service",      # TODO: Fix model name mismatches  
    # "job_service"      # TODO: Fix import issues
]
