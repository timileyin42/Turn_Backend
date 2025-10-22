"""
API routes package.
All routes use FastAPI with comprehensive validation, error handling, and OpenAPI documentation.
"""

from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .gamification_routes import router as gamification_router
# from .project_routes import router as project_router  # TODO: Fix project service imports
# from .cv_routes import router as cv_router  # TODO: Fix CV service schema mismatches
# from .job_routes import router as job_router  # TODO: Fix job service imports

# List of all routers to be included in the main app
routers = [
    auth_router,
    user_router,
    gamification_router,
    # project_router,  # TODO: Fix project service imports
    # cv_router,       # TODO: Fix CV service schema mismatches
    # job_router       # TODO: Fix job service imports
]

__all__ = [
    "auth_router",
    "user_router", 
    "project_router",
    "cv_router",
    "job_router",
    "routers"
]
