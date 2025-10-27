from logging.config import fileConfig
from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection
from alembic import context

# Import all your models here to ensure they are registered with SQLAlchemy
from app.database.user_models import *  # noqa
from app.database.project_models import *  # noqa  
from app.database.cv_models import *  # noqa
from app.database.job_models import *  # noqa
from app.database.portfolio_models import *  # noqa
from app.database.community_models import *  # noqa
from app.database.industry_models import *  # noqa
from app.database.auto_application_models import *  # noqa
from app.database.platform_models import *  # noqa
from app.database.gamification_models import *  # noqa

# Import the database base and configuration
from app.core.database import Base
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Set the database URL from settings (use sync URL for Alembic)
config.set_main_option("sqlalchemy.url", settings.database_url_sync)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()