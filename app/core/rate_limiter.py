"""
Rate Limiting Middleware for TURN Backend API
Implements tiered rate limiting to protect resources and external API quotas.
Uses slowapi (compatible with FastAPI) for in-memory rate limiting.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Initialize limiter with remote address as identifier
limiter = Limiter(key_func=get_remote_address)


# Rate limit tiers for different endpoint types
class RateLimitTiers:
    """
    Rate limit configurations for different API endpoint categories.
    Format: "requests/period" where period can be second, minute, hour, day
    """
    
    # Authentication endpoints (strictest)
    AUTH_LOGIN = "5/minute"  # 5 login attempts per minute
    AUTH_REGISTER = "3/hour"  # 3 registrations per hour
    AUTH_PASSWORD_RESET = "3/hour"  # 3 password reset requests per hour
    AUTH_OTP = "10/hour"  # 10 OTP requests per hour
    
    # AI-powered endpoints (protect expensive operations)
    AI_GENERATION = "20/minute"  # 20 AI requests per minute per user
    AI_COACHING = "30/hour"  # 30 coaching sessions per hour
    AI_COVER_LETTER = "10/hour"  # 10 cover letter generations per hour
    
    # Learning endpoints (moderate)
    LEARNING_CONTENT = "60/minute"  # 60 content requests per minute
    LEARNING_PROGRESS = "30/minute"  # 30 progress updates per minute
    EXTERNAL_COURSES = "30/minute"  # 30 external API calls per minute
    
    # Job search endpoints (protect external APIs)
    JOB_SEARCH_EXTERNAL = "30/minute"  # 30 external job searches per minute
    JOB_APPLICATIONS = "20/hour"  # 20 job applications per hour
    
    # Auto-application endpoints (critical limits)
    AUTO_APPLY_SCAN = "10/hour"  # 10 job scans per hour
    AUTO_APPLY_SUBMIT = "10/day"  # 10 auto-applications per day
    AUTO_APPLY_SETTINGS = "20/minute"  # 20 settings changes per minute
    
    # CV/Resume endpoints
    CV_GENERATION = "20/hour"  # 20 CV generations per hour
    CV_EXPORT = "30/hour"  # 30 exports per hour
    CV_ATS_CHECK = "15/hour"  # 15 ATS checks per hour
    
    # Dashboard and general endpoints
    DASHBOARD = "60/minute"  # 60 dashboard requests per minute
    GENERAL_READ = "100/minute"  # 100 read operations per minute
    GENERAL_WRITE = "60/minute"  # 60 write operations per minute
    
    # Admin endpoints (very strict)
    ADMIN = "30/minute"  # 30 admin operations per minute


def get_rate_limit_message(retry_after: int) -> str:
    """Generate user-friendly rate limit message."""
    if retry_after < 60:
        return f"Rate limit exceeded. Please try again in {retry_after} seconds."
    elif retry_after < 3600:
        minutes = retry_after // 60
        return f"Rate limit exceeded. Please try again in {minutes} minute(s)."
    else:
        hours = retry_after // 3600
        return f"Rate limit exceeded. Please try again in {hours} hour(s)."


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exception handler with detailed error messages."""
    retry_after = int(exc.detail.split("Retry after")[1].split("seconds")[0].strip())
    
    logger.warning(
        f"Rate limit exceeded for {request.client.host} on {request.url.path}. "
        f"Retry after: {retry_after}s"
    )
    
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": get_rate_limit_message(retry_after),
            "retry_after": retry_after,
            "endpoint": str(request.url.path)
        }
    )


# Decorator helpers for common use cases
def auth_rate_limit(limit: str = RateLimitTiers.AUTH_LOGIN):
    """Apply rate limit to authentication endpoints."""
    return limiter.limit(limit)


def ai_rate_limit(limit: str = RateLimitTiers.AI_GENERATION):
    """Apply rate limit to AI-powered endpoints."""
    return limiter.limit(limit)


def learning_rate_limit(limit: str = RateLimitTiers.LEARNING_CONTENT):
    """Apply rate limit to learning endpoints."""
    return limiter.limit(limit)


def job_search_rate_limit(limit: str = RateLimitTiers.JOB_SEARCH_EXTERNAL):
    """Apply rate limit to job search endpoints."""
    return limiter.limit(limit)


def auto_apply_rate_limit(limit: str = RateLimitTiers.AUTO_APPLY_SETTINGS):
    """Apply rate limit to auto-application endpoints."""
    return limiter.limit(limit)


def cv_rate_limit(limit: str = RateLimitTiers.CV_GENERATION):
    """Apply rate limit to CV/resume endpoints."""
    return limiter.limit(limit)


def general_rate_limit(limit: str = RateLimitTiers.GENERAL_READ):
    """Apply rate limit to general endpoints."""
    return limiter.limit(limit)


# IP-based rate limits for public endpoints (no authentication required)
def public_rate_limit(limit: str = "30/minute"):
    """Apply rate limit to public endpoints without authentication."""
    return limiter.limit(limit)


# User-specific rate limits (uses user ID instead of IP)
def get_user_identifier(request: Request) -> str:
    """
    Get user identifier for rate limiting.
    Uses user ID if authenticated, otherwise falls back to IP address.
    """
    try:
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.id}"
    except Exception:
        pass
    
    # Fallback to IP address
    return get_remote_address(request)


# User-based limiter for authenticated endpoints
user_limiter = Limiter(key_func=get_user_identifier)


def user_rate_limit(limit: str):
    """Apply rate limit based on user ID (for authenticated endpoints)."""
    return user_limiter.limit(limit)


# Export all components
__all__ = [
    'limiter',
    'user_limiter',
    'RateLimitTiers',
    'rate_limit_handler',
    'auth_rate_limit',
    'ai_rate_limit',
    'learning_rate_limit',
    'job_search_rate_limit',
    'auto_apply_rate_limit',
    'cv_rate_limit',
    'general_rate_limit',
    'public_rate_limit',
    'user_rate_limit',
    'get_user_identifier'
]
