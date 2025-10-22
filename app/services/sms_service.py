"""
SMS service using Termii provider for African markets.
"""
import requests
from typing import Optional, Dict, Any

from app.core.config import settings


class TermiiSMSProvider:
    """Termii SMS provider implementation."""
    
    def __init__(self):
        self.api_key = settings.termii_api_key
        self.sender_id = settings.termii_sender_id
        self.base_url = "https://api.ng.termii.com/api"
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS using Termii API."""
        if not self.api_key:
            raise ValueError("Termii API key not configured")
        
        try:
            # Clean phone number (remove + and ensure it starts with country code)
            clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
            if not clean_phone.startswith("234") and clean_phone.startswith("0"):
                # Convert Nigerian local format to international
                clean_phone = "234" + clean_phone[1:]
            
            # Prepare request payload
            payload = {
                "to": clean_phone,
                "from": self.sender_id,
                "sms": message,
                "type": "plain",
                "api_key": self.api_key,
                "channel": "generic"
            }
            
            # Send request to Termii API
            response = requests.post(
                f"{self.base_url}/sms/send",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("message_id"),
                    "status": "sent",
                    "provider": "termii",
                    "balance": data.get("balance"),
                    "units_used": data.get("sms_count_used")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "termii"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "provider": "termii"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "termii"
            }


class SMSService:
    """
    SMS service using Termii provider for African markets.
    """
    
    def __init__(self):
        """Initialize SMS service with Termii provider."""
        self.provider = TermiiSMSProvider()
    
    async def send_sms(
        self,
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send SMS using Termii provider.
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            
        Returns:
            Dictionary with send result
        """
        try:
            return await self.provider.send_sms(phone_number, message)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "termii"
            }
    
    async def send_otp_sms(
        self,
        phone_number: str,
        otp_code: str,
        purpose: str = "verification"
    ) -> Dict[str, Any]:
        """
        Send OTP SMS.
        
        Args:
            phone_number: Recipient phone number
            otp_code: OTP code
            purpose: Purpose of the OTP
            
        Returns:
            Dictionary with send result
        """
        # Create SMS message
        purpose_messages = {
            "verification": "verify your account",
            "reset": "reset your password",
            "login": "complete your login",
            "2fa": "complete two-factor authentication"
        }
        
        purpose_text = purpose_messages.get(purpose, "complete verification")
        
        message = (
            f"Your TURN verification code is: {otp_code}\n\n"
            f"Use this code to {purpose_text}. "
            f"This code expires in 10 minutes.\n\n"
            f"Never share this code with anyone.\n\n"
            f"- TURN Platform"
        )
        
        return await self.send_sms(phone_number, message)
    
    async def send_security_alert_sms(
        self,
        phone_number: str,
        security_event: str
    ) -> Dict[str, Any]:
        """
        Send security alert SMS.
        
        Args:
            phone_number: Recipient phone number  
            security_event: Description of security event
            
        Returns:
            Dictionary with send result
        """
        message = (
            f"🚨 TURN Security Alert: {security_event}\n\n"
            f"If this was not you, secure your account immediately:\n"
            f"1. Change your password\n"
            f"2. Enable 2FA\n"
            f"3. Contact support\n\n"
            f"- TURN Security Team"
        )
        
        return await self.send_sms(phone_number, message)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        return {
            "name": "Termii",
            "type": "termii", 
            "configured": bool(settings.termii_api_key),
            "class": "TermiiSMSProvider"
        }


# Global SMS service instance
sms_service = SMSService()