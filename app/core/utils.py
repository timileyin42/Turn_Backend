"""
Utility functions and helpers for the TURN application.
"""
import uuid
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import secrets
import string


def generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def generate_random_string(length: int = 32) -> str:
    """
    Generate a random string of specified length.
    
    Args:
        length: Length of the string to generate
        
    Returns:
        str: Random string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Dict[str, Union[bool, List[str]]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Dict with validation results
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove path traversal attempts
    filename = Path(filename).name
    
    # Replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = f"file_{generate_random_string(8)}"
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: File name
        
    Returns:
        str: File extension (without dot)
    """
    return Path(filename).suffix.lstrip('.').lower()


def is_valid_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Check if file type is allowed.
    
    Args:
        filename: File name
        allowed_extensions: List of allowed extensions (without dots)
        
    Returns:
        bool: True if allowed, False otherwise
    """
    extension = get_file_extension(filename)
    return extension in [ext.lower() for ext in allowed_extensions]


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
        
    Returns:
        str: URL-friendly slug
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_skill_level(level_str: str) -> int:
    """
    Parse skill level from string to integer.
    
    Args:
        level_str: Skill level as string (beginner, intermediate, advanced, expert)
        
    Returns:
        int: Skill level as integer (1-4)
    """
    level_mapping = {
        "beginner": 1,
        "intermediate": 2,
        "advanced": 3,
        "expert": 4
    }
    
    return level_mapping.get(level_str.lower(), 1)


def format_skill_level(level_int: int) -> str:
    """
    Format skill level from integer to string.
    
    Args:
        level_int: Skill level as integer (1-4)
        
    Returns:
        str: Skill level as string
    """
    level_mapping = {
        1: "beginner",
        2: "intermediate", 
        3: "advanced",
        4: "expert"
    }
    
    return level_mapping.get(level_int, "beginner")