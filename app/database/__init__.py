"""
Database models package.
Import all models to ensure they're registered with SQLAlchemy.
"""

# Import all models to register them with SQLAlchemy
from app.database.user_models import *  # noqa
from app.database.platform_models import *  # noqa
from app.database.project_models import *  # noqa
from app.database.cv_models import *  # noqa
from app.database.job_models import *  # noqa
from app.database.portfolio_models import *  # noqa
from app.database.community_models import *  # noqa
from app.database.industry_models import *  # noqa
from app.database.gamification_models import *  # noqa