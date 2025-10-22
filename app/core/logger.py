"""
Structured logging configuration for the TURN application.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import FilteringBoundLogger

from app.core.config import settings


def configure_logging() -> FilteringBoundLogger:
    """
    Configure structured logging for the application.
    
    Returns:
        FilteringBoundLogger: Configured logger instance
    """
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add file and line information to log entries
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO", utc=True),
            structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


def get_logger(name: str = None) -> FilteringBoundLogger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        FilteringBoundLogger: Logger instance
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


def log_api_request(
    logger: FilteringBoundLogger,
    method: str,
    path: str,
    user_id: str = None,
    request_id: str = None,
    **kwargs: Any
) -> None:
    """
    Log API request information.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        user_id: User ID if authenticated
        request_id: Request ID for tracing
        **kwargs: Additional log context
    """
    logger.info(
        "API request",
        method=method,
        path=path,
        user_id=user_id,
        request_id=request_id,
        **kwargs
    )


def log_api_response(
    logger: FilteringBoundLogger,
    method: str,
    path: str,
    status_code: int,
    response_time_ms: float,
    user_id: str = None,
    request_id: str = None,
    **kwargs: Any
) -> None:
    """
    Log API response information.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: HTTP status code
        response_time_ms: Response time in milliseconds
        user_id: User ID if authenticated
        request_id: Request ID for tracing
        **kwargs: Additional log context
    """
    log_level = "info"
    if status_code >= 500:
        log_level = "error"
    elif status_code >= 400:
        log_level = "warning"
    
    getattr(logger, log_level)(
        "API response",
        method=method,
        path=path,
        status_code=status_code,
        response_time_ms=response_time_ms,
        user_id=user_id,
        request_id=request_id,
        **kwargs
    )


def log_database_operation(
    logger: FilteringBoundLogger,
    operation: str,
    table: str,
    record_id: str = None,
    user_id: str = None,
    **kwargs: Any
) -> None:
    """
    Log database operation.
    
    Args:
        logger: Logger instance
        operation: Database operation (CREATE, UPDATE, DELETE, SELECT)
        table: Database table name
        record_id: Record ID if applicable
        user_id: User ID performing operation
        **kwargs: Additional log context
    """
    logger.info(
        "Database operation",
        operation=operation,
        table=table,
        record_id=record_id,
        user_id=user_id,
        **kwargs
    )


def log_external_api_call(
    logger: FilteringBoundLogger,
    service: str,
    endpoint: str,
    method: str = "GET",
    status_code: int = None,
    response_time_ms: float = None,
    **kwargs: Any
) -> None:
    """
    Log external API call.
    
    Args:
        logger: Logger instance
        service: External service name
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        response_time_ms: Response time in milliseconds
        **kwargs: Additional log context
    """
    logger.info(
        "External API call",
        service=service,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        **kwargs
    )


# Initialize logger
logger = configure_logging()