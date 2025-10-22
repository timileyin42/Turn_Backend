"""
Cloudinary Storage Service with FREE tier support.
FREE: 25GB storage, 25GB bandwidth, 25,000 transformations per month.
"""
import os
import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path
import mimetypes
from datetime import datetime, timedelta

try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.utils
    from cloudinary.exceptions import Error as CloudinaryError
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

from app.core.config import settings


class CloudinaryService:
    """Free Cloudinary storage service for file uploads and management."""
    
    def __init__(self):
        """Initialize Cloudinary service."""
        if not CLOUDINARY_AVAILABLE:
            raise ImportError("Cloudinary package not installed. Run: pip install cloudinary")
        
        if not all([settings.cloudinary_cloud_name, settings.cloudinary_api_key, settings.cloudinary_api_secret]):
            raise ValueError("Cloudinary credentials not configured. Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True
        )
        
        self.cloud_name = settings.cloudinary_cloud_name
    
    async def upload_file(
        self, 
        file_content: bytes, 
        filename: str, 
        folder: str = "turn-platform",
        resource_type: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Upload file to Cloudinary.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            folder: Cloudinary folder (default: "turn-platform")
            resource_type: "auto", "image", "video", "raw" 
            **kwargs: Additional Cloudinary upload parameters
            
        Returns:
            Upload result with public_id, secure_url, etc.
        """
        try:
            # Generate unique filename
            file_extension = Path(filename).suffix
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Determine resource type if auto
            if resource_type == "auto":
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type:
                    if mime_type.startswith('image/'):
                        resource_type = "image"
                    elif mime_type.startswith('video/'):
                        resource_type = "video"
                    else:
                        resource_type = "raw"
                else:
                    resource_type = "raw"
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                public_id=f"{folder}/{unique_filename}",
                resource_type=resource_type,
                overwrite=False,
                **kwargs
            )
            
            return {
                "success": True,
                "public_id": upload_result["public_id"],
                "url": upload_result["secure_url"],
                "format": upload_result.get("format"),
                "resource_type": upload_result.get("resource_type"),
                "bytes": upload_result.get("bytes"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "created_at": upload_result.get("created_at"),
                "version": upload_result.get("version"),
                "filename": filename,
                "folder": folder
            }
            
        except CloudinaryError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "cloudinary_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "general_error"
            }
    
    async def upload_cv_pdf(self, pdf_content: bytes, user_id: int, cv_id: int) -> Dict[str, Any]:
        """Upload CV PDF to Cloudinary."""
        filename = f"cv_{user_id}_{cv_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return await self.upload_file(
            file_content=pdf_content,
            filename=filename,
            folder="turn-platform/cvs",
            resource_type="raw",
            tags=["cv", "pdf", f"user_{user_id}"]
        )
    
    async def upload_portfolio_pdf(self, pdf_content: bytes, user_id: int, portfolio_id: int) -> Dict[str, Any]:
        """Upload Portfolio PDF to Cloudinary."""
        filename = f"portfolio_{user_id}_{portfolio_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return await self.upload_file(
            file_content=pdf_content,
            filename=filename,
            folder="turn-platform/portfolios",
            resource_type="raw",
            tags=["portfolio", "pdf", f"user_{user_id}"]
        )
    
    async def upload_project_artifact(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: int, 
        project_id: int,
        artifact_type: str
    ) -> Dict[str, Any]:
        """Upload project artifact to Cloudinary."""
        file_extension = Path(filename).suffix
        safe_filename = f"project_{project_id}_{artifact_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        
        return await self.upload_file(
            file_content=file_content,
            filename=safe_filename,
            folder="turn-platform/projects",
            resource_type="auto",
            tags=["project", "artifact", artifact_type, f"user_{user_id}", f"project_{project_id}"]
        )
    
    async def upload_tts_audio(self, audio_content: bytes, session_id: int, text_hash: str) -> Dict[str, Any]:
        """Upload TTS audio file to Cloudinary."""
        filename = f"tts_{session_id}_{text_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        
        return await self.upload_file(
            file_content=audio_content,
            filename=filename,
            folder="turn-platform/audio/tts",
            resource_type="video",  # Audio files use "video" resource type in Cloudinary
            tags=["tts", "audio", f"session_{session_id}"]
        )
    
    def generate_presigned_url(
        self, 
        public_id: str, 
        expires_in_hours: int = 24,
        **transformation_params
    ) -> str:
        """
        Generate a presigned URL for secure access.
        
        Args:
            public_id: Cloudinary public ID
            expires_in_hours: URL expiration time in hours
            **transformation_params: Cloudinary transformation parameters
            
        Returns:
            Presigned URL
        """
        try:
            # Calculate expiration timestamp
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            expires_timestamp = int(expires_at.timestamp())
            
            # Generate authenticated URL
            auth_url = cloudinary.utils.cloudinary_url(
                public_id,
                sign_url=True,
                auth_token={
                    "duration": expires_in_hours * 3600,  # seconds
                },
                **transformation_params
            )[0]
            
            return auth_url
            
        except Exception as e:
            # Fallback to regular URL if presigned fails
            return cloudinary.utils.cloudinary_url(public_id, **transformation_params)[0]
    
    async def delete_file(self, public_id: str, resource_type: str = "auto") -> Dict[str, Any]:
        """Delete file from Cloudinary."""
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            
            return {
                "success": result.get("result") == "ok",
                "public_id": public_id,
                "result": result.get("result")
            }
            
        except CloudinaryError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "cloudinary_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "general_error"
            }
    
    async def list_files(
        self, 
        folder: str = "turn-platform", 
        resource_type: str = "image",
        max_results: int = 100
    ) -> Dict[str, Any]:
        """List files in a Cloudinary folder."""
        try:
            result = cloudinary.api.resources(
                type="upload",
                resource_type=resource_type,
                prefix=folder,
                max_results=max_results
            )
            
            return {
                "success": True,
                "resources": result.get("resources", []),
                "total_count": result.get("total_count", 0)
            }
            
        except CloudinaryError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "cloudinary_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "general_error"
            }
    
    def get_image_url(
        self, 
        public_id: str, 
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: str = "fill",
        quality: str = "auto",
        format: str = "auto"
    ) -> str:
        """Get optimized image URL with transformations."""
        transformations = {
            "quality": quality,
            "fetch_format": format,
            "crop": crop
        }
        
        if width:
            transformations["width"] = width
        if height:
            transformations["height"] = height
        
        return cloudinary.utils.cloudinary_url(public_id, **transformations)[0]
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get Cloudinary usage information."""
        try:
            usage = cloudinary.api.usage()
            
            return {
                "success": True,
                "plan": usage.get("plan", "Free"),
                "storage": {
                    "used_gb": round(usage.get("storage", {}).get("used", 0) / (1024**3), 2),
                    "limit_gb": round(usage.get("storage", {}).get("limit", 0) / (1024**3), 2)
                },
                "bandwidth": {
                    "used_gb": round(usage.get("bandwidth", {}).get("used", 0) / (1024**3), 2),
                    "limit_gb": round(usage.get("bandwidth", {}).get("limit", 0) / (1024**3), 2)
                },
                "transformations": {
                    "used": usage.get("transformations", {}).get("used", 0),
                    "limit": usage.get("transformations", {}).get("limit", 0)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_error"
            }


# Global instance
cloudinary_service = CloudinaryService() if CLOUDINARY_AVAILABLE and all([
    settings.cloudinary_cloud_name, 
    settings.cloudinary_api_key, 
    settings.cloudinary_api_secret
]) else None