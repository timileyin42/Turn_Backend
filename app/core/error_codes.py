"""
Centralized error codes for the TURN application.
"""
from enum import Enum


class ErrorCode(str, Enum):
    """Application error codes."""
    
    # Authentication & Authorization
    INVALID_CREDENTIALS = "AUTH001"
    TOKEN_EXPIRED = "AUTH002"
    TOKEN_INVALID = "AUTH003"
    INSUFFICIENT_PERMISSIONS = "AUTH004"
    USER_ALREADY_EXISTS = "AUTH005"
    EMAIL_ALREADY_REGISTERED = "AUTH006"
    
    # User Management
    USER_NOT_FOUND = "USER001"
    USER_INACTIVE = "USER002"
    PROFILE_INCOMPLETE = "USER003"
    
    # Projects & AI Coaching
    PROJECT_NOT_FOUND = "PROJECT001"
    PROJECT_ACCESS_DENIED = "PROJECT002"
    AI_SERVICE_UNAVAILABLE = "PROJECT003"
    SIMULATION_ERROR = "PROJECT004"
    
    # CV Builder
    CV_NOT_FOUND = "CV001"
    CV_GENERATION_FAILED = "CV002"
    CV_EXPORT_FAILED = "CV003"
    
    # Job Search
    JOB_NOT_FOUND = "JOB001"
    JOB_APPLICATION_FAILED = "JOB002"
    JOB_SCRAPING_ERROR = "JOB003"
    
    # Portfolio
    PORTFOLIO_NOT_FOUND = "PORTFOLIO001"
    PORTFOLIO_EXPORT_FAILED = "PORTFOLIO002"
    ARTIFACT_UPLOAD_FAILED = "PORTFOLIO003"
    
    # Community & Mentorship
    FORUM_POST_NOT_FOUND = "COMMUNITY001"
    MENTOR_NOT_AVAILABLE = "COMMUNITY002"
    MENTORSHIP_REQUEST_FAILED = "COMMUNITY003"
    
    # File Operations
    FILE_NOT_FOUND = "FILE001"
    FILE_UPLOAD_FAILED = "FILE002"
    FILE_TOO_LARGE = "FILE003"
    INVALID_FILE_FORMAT = "FILE004"
    
    # External Services
    EMAIL_SERVICE_ERROR = "EXTERNAL001"
    STORAGE_SERVICE_ERROR = "EXTERNAL002"
    AI_API_ERROR = "EXTERNAL003"
    
    # General
    VALIDATION_ERROR = "GENERAL001"
    INTERNAL_SERVER_ERROR = "GENERAL002"
    RESOURCE_NOT_FOUND = "GENERAL003"
    RATE_LIMIT_EXCEEDED = "GENERAL004"
    
    
# Error messages mapping
ERROR_MESSAGES = {
    ErrorCode.INVALID_CREDENTIALS: "Invalid username or password",
    ErrorCode.TOKEN_EXPIRED: "Access token has expired",
    ErrorCode.TOKEN_INVALID: "Invalid access token",
    ErrorCode.INSUFFICIENT_PERMISSIONS: "Insufficient permissions to perform this action",
    ErrorCode.USER_ALREADY_EXISTS: "User with this username already exists",
    ErrorCode.EMAIL_ALREADY_REGISTERED: "Email address is already registered",
    
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.USER_INACTIVE: "User account is inactive",
    ErrorCode.PROFILE_INCOMPLETE: "User profile is incomplete",
    
    ErrorCode.PROJECT_NOT_FOUND: "Project not found",
    ErrorCode.PROJECT_ACCESS_DENIED: "Access denied to this project",
    ErrorCode.AI_SERVICE_UNAVAILABLE: "AI service is currently unavailable",
    ErrorCode.SIMULATION_ERROR: "Error occurred during project simulation",
    
    ErrorCode.CV_NOT_FOUND: "CV not found",
    ErrorCode.CV_GENERATION_FAILED: "Failed to generate CV",
    ErrorCode.CV_EXPORT_FAILED: "Failed to export CV",
    
    ErrorCode.JOB_NOT_FOUND: "Job listing not found",
    ErrorCode.JOB_APPLICATION_FAILED: "Failed to submit job application",
    ErrorCode.JOB_SCRAPING_ERROR: "Error occurred while fetching job listings",
    
    ErrorCode.PORTFOLIO_NOT_FOUND: "Portfolio not found",
    ErrorCode.PORTFOLIO_EXPORT_FAILED: "Failed to export portfolio",
    ErrorCode.ARTIFACT_UPLOAD_FAILED: "Failed to upload artifact",
    
    ErrorCode.FORUM_POST_NOT_FOUND: "Forum post not found",
    ErrorCode.MENTOR_NOT_AVAILABLE: "Mentor is not available",
    ErrorCode.MENTORSHIP_REQUEST_FAILED: "Failed to create mentorship request",
    
    ErrorCode.FILE_NOT_FOUND: "File not found",
    ErrorCode.FILE_UPLOAD_FAILED: "File upload failed",
    ErrorCode.FILE_TOO_LARGE: "File size exceeds the maximum allowed limit",
    ErrorCode.INVALID_FILE_FORMAT: "Invalid file format",
    
    ErrorCode.EMAIL_SERVICE_ERROR: "Email service error",
    ErrorCode.STORAGE_SERVICE_ERROR: "Storage service error",
    ErrorCode.AI_API_ERROR: "AI API error",
    
    ErrorCode.VALIDATION_ERROR: "Validation error",
    ErrorCode.INTERNAL_SERVER_ERROR: "Internal server error",
    ErrorCode.RESOURCE_NOT_FOUND: "Resource not found",
    ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",
}