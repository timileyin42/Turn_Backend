"""
OTP (One-Time Password) service for authentication and verification.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.services.email_service import email_service
from app.services.sms_service import sms_service


class OTPService:
    """Service for handling OTP generation, storage, and verification."""
    
    def __init__(self):
        # In-memory storage for OTPs (in production, use Redis or database)
        self._otp_storage: Dict[str, Dict] = {}
    
    def generate_otp(self, length: int = 6) -> str:
        """
        Generate a random OTP.
        
        Args:
            length: Length of the OTP (default: 6)
            
        Returns:
            Generated OTP string
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def store_otp(
        self, 
        identifier: str, 
        otp: str, 
        purpose: str = "verification",
        expires_in_minutes: int = 10
    ) -> None:
        """
        Store OTP with expiration.
        
        Args:
            identifier: Email or phone number
            otp: Generated OTP
            purpose: Purpose of the OTP (verification, reset, etc.)
            expires_in_minutes: OTP expiration time in minutes
        """
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        self._otp_storage[identifier] = {
            "otp": otp,
            "purpose": purpose,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "attempts": 0
        }
    
    def verify_otp(
        self, 
        identifier: str, 
        otp: str, 
        purpose: str = "verification",
        max_attempts: int = 3
    ) -> bool:
        """
        Verify OTP.
        
        Args:
            identifier: Email or phone number
            otp: OTP to verify
            purpose: Expected purpose of the OTP
            max_attempts: Maximum verification attempts
            
        Returns:
            True if OTP is valid, False otherwise
        """
        stored_data = self._otp_storage.get(identifier)
        
        if not stored_data:
            return False
        
        # Check if too many attempts
        if stored_data["attempts"] >= max_attempts:
            self._otp_storage.pop(identifier, None)
            return False
        
        # Increment attempts
        stored_data["attempts"] += 1
        
        # Check expiration
        if datetime.utcnow() > stored_data["expires_at"]:
            self._otp_storage.pop(identifier, None)
            return False
        
        # Check purpose and OTP
        if stored_data["purpose"] != purpose or stored_data["otp"] != otp:
            return False
        
        # Valid OTP - remove from storage
        self._otp_storage.pop(identifier, None)
        return True
    
    async def send_email_otp(
        self, 
        email: str, 
        name: str,
        purpose: str = "verification"
    ) -> str:
        """
        Generate and send OTP via email.
        
        Args:
            email: Recipient email
            name: Recipient name
            purpose: Purpose of the OTP
            
        Returns:
            Generated OTP (for testing purposes)
        """
        otp = self.generate_otp()
        self.store_otp(email, otp, purpose)
        
        # Determine email template based on purpose
        if purpose == "verification":
            subject = "Email Verification Code - TURN"
            template_data = {
                "name": name,
                "otp_code": otp,
                "purpose": "verify your email address",
                "expires_in": "10 minutes"
            }
        elif purpose == "reset":
            subject = "Password Reset Code - TURN" 
            template_data = {
                "name": name,
                "otp_code": otp,
                "purpose": "reset your password",
                "expires_in": "10 minutes"
            }
        elif purpose == "login":
            subject = "Login Verification Code - TURN"
            template_data = {
                "name": name,
                "otp_code": otp,
                "purpose": "complete your login",
                "expires_in": "10 minutes"
            }
        else:
            subject = "Verification Code - TURN"
            template_data = {
                "name": name,
                "otp_code": otp,
                "purpose": "complete your verification",
                "expires_in": "10 minutes"
            }
        
        try:
            await email_service.send_otp_email(
                email=email,
                name=name,
                otp_code=otp,
                purpose=purpose,
                expires_in=template_data['expires_in']
            )
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            raise
        
        return otp
    
    async def send_sms_otp(
        self, 
        phone_number: str, 
        purpose: str = "verification"
    ) -> str:
        """
        Generate and send OTP via SMS.
        
        Args:
            phone_number: Recipient phone number
            purpose: Purpose of the OTP
            
        Returns:
            Generated OTP (for testing purposes)
        """
        otp = self.generate_otp()
        self.store_otp(phone_number, otp, purpose)
        
        try:
            # Send SMS using Termii SMS service
            result = await sms_service.send_otp_sms(
                phone_number=phone_number,
                otp_code=otp,
                purpose=purpose
            )
            
            if not result.get("success"):
                raise Exception(f"SMS sending failed: {result.get('error')}")
            
            print(f"SMS OTP sent successfully to {phone_number} via {result.get('provider')}")
            
        except Exception as e:
            print(f"Failed to send OTP SMS: {e}")
            raise
        
        return otp
    
    def cleanup_expired_otps(self) -> None:
        """Remove expired OTPs from storage."""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, data in self._otp_storage.items()
            if current_time > data["expires_at"]
        ]
        
        for key in expired_keys:
            self._otp_storage.pop(key, None)
    
    def get_otp_info(self, identifier: str) -> Optional[Dict]:
        """
        Get OTP information for debugging/testing.
        
        Args:
            identifier: Email or phone number
            
        Returns:
            OTP information or None if not found
        """
        return self._otp_storage.get(identifier)


# Global OTP service instance
otp_service = OTPService()