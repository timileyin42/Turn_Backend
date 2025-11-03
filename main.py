"""
TURN - Project Manager Career Platform
FastAPI main application with PostgreSQL backend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.routes import routers
from app.core.rate_limiter import limiter, rate_limit_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.app_name}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    print(f"Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    TURN - A comprehensive web application for aspiring project managers.
    
    ## Features
    
    * **User Management** - Registration, authentication, and profile management
    * **Project Management** - Complete project lifecycle with AI coaching
    * **CV Builder** - Dynamic resume creation with export functionality
    * **Job Search** - Job listings, applications, and recommendations
    * **AI Integration** - Intelligent coaching and career guidance
    
    ## Authentication
    
    This App uses JWT (JSON Web Tokens) for authentication:
    1. Register or login to get an access token
    2. Include the token in the Authorization header: `Bearer <token>`
    3. Use the refresh endpoint to get new tokens when needed    
    """,
    version="1.0.0",
    contact={
        "name": "TURN Development Team",
        "email": "support@turn-platform.com",
    },
    lifespan=lifespan,
    debug=settings.debug
)


def custom_openapi():
    """Provide a custom OpenAPI schema that sets OAuth2 password flow as the primary security scheme.

    This ensures Swagger's Authorize modal shows username/password (password flow) instead of the
    HTTP Bearer input box.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app_name,
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )

    # Ensure components exists
    components = openapi_schema.setdefault("components", {})

    # Define OAuth2 Password flow as the primary security scheme
    components["securitySchemes"] = {
        "OAuth2Password": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/login",
                    "scopes": {}
                }
            },
            "description": "OAuth2 Password Flow - enter email as username and your password"
        }
    }

    # Set global security to use OAuth2Password only
    openapi_schema["security"] = [{"OAuth2Password": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Attach custom OpenAPI generator so Swagger UI will use OAuth2 password flow
app.openapi = custom_openapi

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://turn-platform.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["turn-platform.com", "*.turn-platform.com"]
    )

# Include all routers
for router in routers:
    app.include_router(router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api": "/api/v1"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    if settings.debug:
        # In debug mode, show the actual error
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        # In production, hide error details
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )