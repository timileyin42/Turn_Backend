"""
Router management for Turn Backend API.
"""
from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router
from app.routes.project_routes import router as project_router
from app.routes.job_routes import router as job_router
from app.routes.cv_routes import router as cv_routes_router
from app.api.learning import router as learning_router
from app.api.simulations import router as simulations_router
from app.api.cv_builder import router as cv_builder_router
from app.api.job_search import router as job_search_router
from app.api.dashboard import router as dashboard_router
from app.api.ai_coaching import router as ai_coaching_router
from app.api.auto_application import router as auto_application_router
from app.api.auto_application_dashboard import router as auto_application_dashboard_router

# List of all routers to be included in the main app
routers = [
    auth_router,
    user_router,
    project_router,
    job_router,
    cv_routes_router,
    learning_router,
    simulations_router,
    cv_builder_router,
    job_search_router,
    dashboard_router,
    ai_coaching_router,
    auto_application_router,
    auto_application_dashboard_router,
]