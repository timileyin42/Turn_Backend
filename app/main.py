"""
TURN - Project Manager Career Platform
FastAPI main application with PostgreSQL backend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routes import routers


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
    * **AI PM Teacher** - Intelligent coaching, personalized learning paths, and career guidance
    * **Project Management** - Complete project lifecycle with AI coaching
    * **CV Builder** - Dynamic resume creation with export functionality
    * **Job Search** - Job listings, applications, and recommendations
    * **Learning Hub** - Courses from top platforms like Coursera, edX, YouTube
    * **Project Simulations** - Real-world case studies from Netflix, Spotify, Tesla
    * **Portfolio Builder** - Showcase your PM projects and achievements
    
    ## AI-Powered Learning
    
    * **Personalized Learning Paths** - 12-week customized programs based on your level
    * **AI Coaching Sessions** - One-on-one mentorship with expert AI PM teacher
    * **Scenario Analysis** - Get feedback on your PM decisions and strategies
    * **Interview Preparation** - Practice with AI-generated interview questions
    * **Career Guidance** - Personalized advice for PM career advancement
    

    """,
    version="1.0.0",
    contact={
        "name": "TURN Development Team",
        "email": "support@turn-platform.com",
    },

    lifespan=lifespan,
    debug=settings.debug
)

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
        "message": f"Welcome to {settings.app_name} API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )