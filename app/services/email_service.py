"""
Email Service with Template Support 

"""
 
import os
import logging
from typing import Dict, Any, Optional, List
import httpx
import random
import string
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for loading and rendering email templates using Jinja2."""
    
    def __init__(self):
        # Get the templates directory path
        self.templates_dir = Path(__file__).parent.parent / "templates" / "emails"
        
        # Ensure templates directory exists
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment with the templates directory
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        logger.info(f"EmailTemplateService initialized with directory: {self.templates_dir}")
    
    def load_template(self, template_name: str):
        """Load a template file by name."""
        try:
            template = self.jinja_env.get_template(template_name)
            return template
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            raise
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context."""
        try:
            template = self.load_template(template_name)
            rendered_content = template.render(**context)
            logger.info(f"Template {template_name} rendered successfully ({len(rendered_content)} chars)")
            return rendered_content
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            # Return a basic HTML fallback
            return f"""
            <html>
                <body>
                    <h2>Email Template Error</h2>
                    <p>Sorry, there was an error rendering the email template.</p>
                    <p>Error: {str(e)}</p>
                </body>
            </html>
            """


class EmailService:
    """
    Resend Email service with comprehensive template support
    
    Features:
    - Transactional emails (OTP, password reset, welcome)
    - Template-based HTML emails with Jinja2
    """
    
    def __init__(self):
        # Resend API configuration from settings
        self.api_key = settings.resend_api_key
        self.base_url = "https://api.resend.com/emails"
        self.sender_email = settings.resend_sender_email
        self.sender_name = settings.resend_sender_name
        
        # Initialize template service
        self.template_service = EmailTemplateService()
        
        # OTP storage (in production, use Redis or database)
        self._otp_store = {}
        
        if not self.api_key:
            logger.warning("RESEND_API_KEY not found. Email service will not work.")
        else:
            logger.info("Resend EmailService initialized successfully")
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP code"""
        return ''.join(random.choices(string.digits, k=length))
    
    async def send_email(self, to_email: str, subject: str, html_content: str, 
                        to_name: str = None, text_content: str = None,
                        sender_email: str = None, sender_name: str = None) -> Dict[str, Any]:
        """
        Send an email using Resend API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            to_name: Recipient name (optional)
            text_content: Plain text content (optional)
            sender_email: Override sender email (optional)
            sender_name: Override sender name (optional)
            
        Returns:
            Dict with success status and response data
        """
        if not self.api_key:
            logger.error("Resend API key not configured")
            return {
                "success": False,
                "error": "Email service not configured"
            }
        
        # Prepare sender with name
        from_field = sender_email or self.sender_email
        if sender_name or self.sender_name:
            from_field = f"{sender_name or self.sender_name} <{from_field}>"
        
        # Prepare request payload for Resend API
        payload = {
            "from": from_field,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # Add text content if provided
        if text_content:
            payload["text"] = text_content
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    message_id = data.get("id")
                    logger.info(f"📧 Email sent successfully to {to_email}, Message ID: {message_id}")
                    return {
                        "success": True,
                        "message_id": message_id,
                        "message": "Email sent successfully"
                    }
                else:
                    error_msg = f"Failed to send email: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"Exception sending email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_welcome_email(self, email: str, name: str, verification_url: Optional[str] = None) -> Dict[str, Any]:
        """Send welcome email using template"""
        try:
            context = {
                "name": name,
                "platform_url": settings.platform_url,
                "verification_url": verification_url,
                "social_linkedin": settings.social_linkedin,
                "social_twitter": settings.social_twitter,
                "help_center_url": settings.help_center_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("welcome.html", context)
            
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject="Welcome to TurnVe - Start Building Your Project Management Career!",
                html_content=html_content
            )
            
            return {
                **result,
                "template_used": "welcome.html",
                "email": email,
                "name": name
            }
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_verification_otp(self, email: str, name: str) -> Dict[str, Any]:
        """Send email verification OTP using template"""
        from app.services.otp_service import otp_service
        
        # Use otp_service to generate and store OTP
        otp_code = otp_service.generate_otp()
        otp_service.store_otp(email, otp_code, "verification", expires_in_minutes=10)
        
        try:
            # Render OTP verification template
            context = {
                "name": name,
                "otp_code": otp_code,
                "purpose_label": "Email Verification",
                "purpose_description": "verify your email address",
                "expires_in": "10 minutes",
                "generated_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("otp_verification.html", context)
            
            # Send via Resend
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject=f"Your TurnVe verification code: {otp_code}",
                html_content=html_content
            )
                
            return {
                **result,
                "otp_code": otp_code if result["success"] else None,
                "purpose": "verification",
                "template_used": "otp_verification.html"
            }
            
        except Exception as e:
            logger.error(f"Error sending verification OTP to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_password_reset_otp(self, email: str, name: str) -> Dict[str, Any]:
        """Send password reset OTP using template"""
        from app.services.otp_service import otp_service
        
        # Use otp_service to generate and store OTP
        otp_code = otp_service.generate_otp()
        otp_service.store_otp(email, otp_code, "reset", expires_in_minutes=10)
        
        try:
            # Render password reset template
            context = {
                "name": name,
                "otp_code": otp_code,
                "purpose_label": "Password Reset",
                "purpose_description": "reset your password",
                "expires_in": "10 minutes",
                "generated_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("otp_verification.html", context)
            
            # Send via Resend
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject=f"Your TurnVe password reset code: {otp_code}",
                html_content=html_content
            )
                
            return {
                **result,
                "otp_code": otp_code if result["success"] else None,
                "purpose": "password_reset",
                "template_used": "otp_verification.html"
            }
            
        except Exception as e:
            logger.error(f"Error sending password reset OTP to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_login_otp(self, email: str, name: str) -> Dict[str, Any]:
        """Send login verification OTP using template"""
        otp_code = self.generate_otp()
        
        try:
            # Render login OTP template
            context = {
                "name": name,
                "otp_code": otp_code,
                "purpose_label": "Login Verification",
                "purpose_description": "verify your login",
                "expires_in": "5 minutes",
                "generated_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("otp_verification.html", context)
            
            # Send via Brevo
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject=f"Your TurnVe login code: {otp_code}",
                html_content=html_content
            )
            
            if result["success"]:
                # Store OTP in cache/database with expiry
                await self._store_otp(email, otp_code, "login", expire_minutes=5)
                
            return {
                **result,
                "otp_code": otp_code if result["success"] else None,
                "purpose": "login",
                "template_used": "otp_verification.html"
            }
            
        except Exception as e:
            logger.error(f"Error sending login OTP to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_otp(self, email: str, otp_code: str, purpose: str) -> Dict[str, Any]:
        """Verify OTP code"""
        stored_otp = await self._get_stored_otp(email, purpose)
        
        if not stored_otp:
            return {
                "success": False,
                "error": "OTP not found or expired"
            }
        
        if stored_otp["code"] != otp_code:
            return {
                "success": False,
                "error": "Invalid OTP code"
            }
        
        if datetime.utcnow() > stored_otp["expires_at"]:
            await self._delete_stored_otp(email, purpose)
            return {
                "success": False,
                "error": "OTP has expired"
            }
        
        # Delete OTP after successful verification
        await self._delete_stored_otp(email, purpose)
        
        return {
            "success": True,
            "message": "OTP verified successfully"
        }
    
    async def _store_otp(self, email: str, otp_code: str, purpose: str, expire_minutes: int = 10):
        """Store OTP in cache (in production, use Redis or database)"""
        key = f"{email}:{purpose}"
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        self._otp_store[key] = {
            "code": otp_code,
            "purpose": purpose,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at
        }
        
        logger.info(f"OTP stored for {email} ({purpose}), expires at {expires_at}")
    
    async def _get_stored_otp(self, email: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get stored OTP from cache"""
        key = f"{email}:{purpose}"
        return self._otp_store.get(key)
    
    async def _delete_stored_otp(self, email: str, purpose: str):
        """Delete stored OTP from cache"""
        key = f"{email}:{purpose}"
        if key in self._otp_store:
            del self._otp_store[key]
            logger.info(f"OTP deleted for {email} ({purpose})")
    
    async def cleanup_expired_otps(self):
        """Clean up expired OTPs from storage"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, otp_data in self._otp_store.items():
            if current_time > otp_data["expires_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._otp_store[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired OTPs")
    
    async def send_cv_ready_notification(self, email: str, name: str, cv_download_url: str) -> Dict[str, Any]:
        """Send CV ready notification email using template"""
        try:
            context = {
                "name": name,
                "cv_download_url": cv_download_url,
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("cv_ready.html", context)
            
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject="Your CV is Ready for Download! 📄",
                html_content=html_content
            )
            
            return {
                **result,
                "template_used": "cv_ready.html"
            }
            
        except Exception as e:
            logger.error(f"Error sending CV ready notification to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_interview_reminder(self, email: str, name: str, interview_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send interview reminder email using template"""
        try:
            context = {
                "name": name,
                "interview_date": interview_details.get("date"),
                "interview_time": interview_details.get("time"),
                "company_name": interview_details.get("company"),
                "position": interview_details.get("position"),
                "interview_link": interview_details.get("link"),
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("interview_reminder.html", context)
            
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject=f"Interview Reminder: {interview_details.get('position')} at {interview_details.get('company')}",
                html_content=html_content
            )
            
            return {
                **result,
                "template_used": "interview_reminder.html"
            }
            
        except Exception as e:
            logger.error(f"Error sending interview reminder to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_job_alert(self, email: str, name: str, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send job alert email with matching opportunities using template"""
        try:
            context = {
                "name": name,
                "jobs": jobs,
                "job_count": len(jobs),
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("job_alert.html", context)
            
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject=f"{len(jobs)} New Job Opportunities Match Your Profile",
                html_content=html_content
            )
            
            return {
                **result,
                "template_used": "job_alert.html",
                "jobs_count": len(jobs)
            }
            
        except Exception as e:
            logger.error(f"Error sending job alert to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_newsletter(self, email: str, name: str, newsletter_content: Dict[str, Any]) -> Dict[str, Any]:
        """Send newsletter email using template"""
        try:
            context = {
                "name": name,
                "newsletter_title": newsletter_content.get("title"),
                "articles": newsletter_content.get("articles", []),
                "featured_job": newsletter_content.get("featured_job"),
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("newsletter.html", context)
            
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject=newsletter_content.get("title", "TURN Newsletter - Latest Updates"),
                html_content=html_content
            )
            
            return {
                **result,
                "template_used": "newsletter.html"
            }
            
        except Exception as e:
            logger.error(f"Error sending newsletter to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_course_completion(self, email: str, name: str, course_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send course completion certificate email using template"""
        try:
            context = {
                "name": name,
                "course_name": course_details.get("name"),
                "completion_date": course_details.get("completion_date"),
                "certificate_url": course_details.get("certificate_url"),
                "platform_url": settings.platform_url,
                "current_year": datetime.now().year
            }
            
            html_content = self.template_service.render_template("course_completion.html", context)
            
            result = await self.send_email(
                to_email=email,
                to_name=name,
                subject=f"Congratulations! You've completed {course_details.get('name')}",
                html_content=html_content
            )
            
            return {
                **result,
                "template_used": "course_completion.html"
            }
            
        except Exception as e:
            logger.error(f"Error sending course completion email to {email}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_otp(self, email: str, otp_code: str, purpose: str, expire_minutes: int = 10):
        """Store OTP in cache (in production, use Redis or database)"""
        key = f"{email}:{purpose}"
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        self._otp_store[key] = {
            "code": otp_code,
            "purpose": purpose,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        
        logger.info(f"OTP stored for {email} (purpose: {purpose}, expires: {expires_at})")
    
    async def _get_stored_otp(self, email: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get stored OTP from cache"""
        key = f"{email}:{purpose}"
        return self._otp_store.get(key)
    
    async def _delete_stored_otp(self, email: str, purpose: str):
        """Delete stored OTP from cache"""
        key = f"{email}:{purpose}"
        if key in self._otp_store:
            del self._otp_store[key]
            logger.info(f"OTP deleted for {email} (purpose: {purpose})")
    
    async def cleanup_expired_otps(self):
        """Clean up expired OTPs (run this periodically)"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, otp_data in self._otp_store.items():
            if now > otp_data["expires_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._otp_store[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired OTPs")
    
    # Auto-Application Email Methods
    
    async def send_job_match_notification(
        self, 
        email: str, 
        user_name: str, 
        job_title: str,
        company_name: str,
        match_score: float,
        approve_url: str,
        reject_url: str,
        view_url: str,
        job_details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send email notification for new job match."""
        try:
            subject = f"New Job Match: {job_title} at {company_name}"
            
            # Prepare template data
            template_data = {
                "user_name": user_name,
                "job_title": job_title,
                "company_name": company_name,
                "match_score": int(match_score * 100),  # Convert to percentage
                "approve_url": approve_url,
                "reject_url": reject_url,
                "view_url": view_url,
                "settings_url": "/dashboard/auto-apply/settings"
            }
            
            # Add job details if provided
            if job_details:
                template_data.update({
                    "location": job_details.get("location"),
                    "job_type": job_details.get("job_type"),
                    "salary_range": job_details.get("salary_range"),
                    "experience_level": job_details.get("experience_level"),
                    "match_reasons": job_details.get("match_reasons", [])
                })
            
            # Load and render template
            template = self.template_service.load_template('job_match_notification.html')
            html_content = template.render(**template_data)
            
            result = await self.send_email(email, subject, html_content)
            
            if result.get('success'):
                logger.info(f"Job match notification sent to {email} for {job_title} at {company_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending job match notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_job_match_summary(
        self,
        email: str,
        user_name: str,
        total_matches: int,
        pending_applications: int,
        applications_submitted: int,
        new_matches: List[Dict[str, Any]] = None,
        dashboard_url: str = "/dashboard/auto-apply",
        optimization_tips: List[str] = None,
        weekly_stats: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send daily/weekly job match summary email."""
        try:
            subject = f"Your Job Match Summary: {total_matches} New Opportunities"
            
            # Prepare template data
            template_data = {
                "user_name": user_name,
                "date_range": datetime.now().strftime("%B %d, %Y"),
                "total_matches": total_matches,
                "pending_applications": pending_applications,
                "applications_submitted": applications_submitted,
                "dashboard_url": dashboard_url,
                "settings_url": "/dashboard/auto-apply/settings",
                "new_matches": new_matches or [],
                "optimization_tips": optimization_tips or [],
                "weekly_stats": weekly_stats
            }
            
            # Load and render template
            template = self.template_service.load_template('job_match_summary.html')
            html_content = template.render(**template_data)
            
            result = await self.send_email(email, subject, html_content)
            
            if result.get('success'):
                logger.info(f"Job match summary sent to {email}: {applications_submitted} applications")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending job match summary: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_auto_application_confirmation(
        self,
        user_email: str,
        user_name: str,
        job_title: str,
        company_name: str,
        application_id: str,
        match_score: float,
        confidence_score: float = None,
        job_details: Dict[str, Any] = None,
        cover_letter_preview: str = None
    ) -> Dict[str, Any]:
        """Send confirmation email after auto-application submission."""
        try:
            subject = f" Application Submitted: {job_title} at {company_name}"
            
            # Prepare template data
            template_data = {
                "user_name": user_name,
                "job_title": job_title,
                "company_name": company_name,
                "application_id": application_id,
                "match_score": int(match_score * 100),  # Convert to percentage
                "submission_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                "track_url": f"/dashboard/applications/{application_id}",
                "dashboard_url": "/dashboard/auto-apply",
                "similar_jobs_url": "/dashboard/job-search",
                "ai_generated_content": True,
                "cover_letter_preview": cover_letter_preview
            }
            
            # Add optional data
            if confidence_score is not None:
                confidence_percent = int(confidence_score * 100)
                template_data["confidence_score"] = confidence_percent
                # Pre-format the style to avoid VS Code linter warnings
                template_data["confidence_style"] = f"width: {confidence_percent}%"
            
            if job_details:
                template_data.update({
                    "location": job_details.get("location"),
                    "job_type": job_details.get("job_type"),
                    "salary_range": job_details.get("salary_range")
                })
            
            # Load and render template
            template = self.template_service.load_template('auto_application_confirmation.html')
            html_content = template.render(**template_data)
            
            result = await self.send_email(user_email, subject, html_content)
            
            if result.get('success'):
                logger.info(f"Auto-application confirmation sent for {job_title} at {company_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending auto-application confirmation: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_application_status_update(
        self,
        email: str,
        user_name: str,
        job_title: str,
        company_name: str,
        status: str,
        message: str = None,
        timeline: List[Dict[str, Any]] = None,
        interview_details: str = None,
        feedback: str = None,
        recommendations: List[str] = None
    ) -> Dict[str, Any]:
        """Send email when application status changes."""
        try:
            # Define status mapping
            status_config = {
                "interview_scheduled": {
                    "title": " Interview Invitation",
                    "class": "interview",
                    "icon": "�"
                },
                "under_review": {
                    "title": "⏳ Application Under Review", 
                    "class": "pending",
                    "icon": "⏳"
                },
                "rejected": {
                    "title": "� Application Update",
                    "class": "rejected",
                    "icon": "&#128221;"  # Memo icon
                },
                "accepted": {
                    "title": "🎊 Job Offer Received",
                    "class": "success",
                    "icon": "🎊"
                },
                "withdrawn": {
                    "title": "Application Withdrawn",
                    "class": "pending",
                    "icon": "&#8505;"  # Info icon
                }
            }
            
            config = status_config.get(status, {
                "title": "📋 Application Update",
                "class": "pending", 
                "icon": "📋"
            })
            
            subject = f"{config['title']}: {job_title} at {company_name}"
            
            # Prepare template data
            template_data = {
                "user_name": user_name,
                "job_title": job_title,
                "company_name": company_name,
                "status": status,
                "status_title": config["title"],
                "status_class": config["class"],
                "status_icon": config["icon"],
                "status_message": message or "Your application status has been updated.",
                "track_url": f"/dashboard/applications",
                "dashboard_url": "/dashboard/auto-apply",
                "application_date": None,  # Can be passed in if needed
                "timeline": timeline or [],
                "interview_details": interview_details,
                "feedback": feedback,
                "recommendations": recommendations or [],
                "interview_prep_url": "/dashboard/interview-prep",
                "similar_jobs_url": "/dashboard/job-search",
                "expected_response_time": "1-2 weeks"
            }
            
            # Load and render template
            template = self.template_service.load_template('application_status_update.html')
            html_content = template.render(**template_data)
            
            result = await self.send_email(email, subject, html_content)
            
            if result.get('success'):
                logger.info(f"Application status update sent to {email}: {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending application status update: {e}")
            return {"success": False, "error": str(e)}


# Create a global instance for easy import
email_service = EmailService()
async def cleanup_expired_otps_task():
    """Background task to clean up expired OTPs"""
    while True:
        try:
            await email_service.cleanup_expired_otps()
            await asyncio.sleep(300)  # Clean up every 5 minutes
        except Exception as e:
            logger.error(f"Error in OTP cleanup task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying