"""
Logging middleware for request/response and database query tracking.
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses with timing.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("request_logger")
        self.logger.setLevel(logging.INFO if settings.debug else logging.WARNING)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        """
        # Skip health check and docs endpoints to reduce noise
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Log request
        if settings.debug:
            self.logger.info("=" * 100)
            self.logger.info(f" INCOMING REQUEST")
            self.logger.info(f"   Method: {request.method}")
            self.logger.info(f"   Path: {request.url.path}")
            self.logger.info(f"   Query Params: {dict(request.query_params)}")
            self.logger.info(f"   Client: {request.client.host if request.client else 'Unknown'}")
            
            # Log headers (exclude sensitive ones)
            safe_headers = {
                k: v for k, v in request.headers.items() 
                if k.lower() not in ['authorization', 'cookie', 'x-api-key']
            }
            if safe_headers:
                self.logger.info(f"   Headers: {safe_headers}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Log response
            if settings.debug:
                status_emoji = "OK" if response.status_code < 400 else "WARN" if response.status_code < 500 else "ERROR"
                self.logger.info(f"\n{status_emoji} RESPONSE")
                self.logger.info(f"   Status: {response.status_code}")
                self.logger.info(f"   Duration: {duration_ms:.2f}ms")
                
                # Add performance warning for slow requests
                if duration_ms > 1000:
                    self.logger.warning(f"    SLOW REQUEST! Took {duration_ms:.2f}ms (> 1 second)")
                elif duration_ms > 500:
                    self.logger.warning(f"    Moderately slow request: {duration_ms:.2f}ms")
                
                self.logger.info("=" * 100 + "\n")
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(duration_ms)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            self.logger.error("=" * 100)
            self.logger.error(f" REQUEST FAILED")
            self.logger.error(f"   Method: {request.method}")
            self.logger.error(f"   Path: {request.url.path}")
            self.logger.error(f"   Duration: {duration_ms:.2f}ms")
            self.logger.error(f"   Error: {str(e)}")
            self.logger.error("=" * 100 + "\n")
            
            raise


class DatabaseQueryLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track database queries per request.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("db_query_logger")
        self.logger.setLevel(logging.INFO if settings.debug else logging.WARNING)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Track database queries during request.
        """
        # Skip non-debug mode
        if not settings.debug:
            return await call_next(request)
        
        # Skip health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Mark start of request queries
        self.logger.info(f"\n{'' * 40}")
        self.logger.info(f" DATABASE QUERIES FOR: {request.method} {request.url.path}")
        self.logger.info(f"{'' * 40}")
        
        # Process request (SQL queries will be logged by SQLAlchemy)
        response = await call_next(request)
        
        # Mark end of request queries
        self.logger.info(f"{'' * 40}")
        self.logger.info(f" END OF QUERIES FOR: {request.method} {request.url.path}")
        self.logger.info(f"{'' * 40}\n")
        
        return response
