"""
Test Brevo Email Integration

This script tests the Brevo email service to ensure:
1. API credentials are correctly configured
2. Email sending works properly
3. Template rendering works correctly
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email_service import email_service
from app.core.config import settings


async def test_brevo_email_config():
    """Test 1: Verify Brevo Email configuration"""
    print("\n" + "="*80)
    print("TEST 1: Brevo Email Configuration")
    print("="*80)
    
    print(f"\n✓ API Key: {'*' * 20}{email_service.api_key[-10:] if email_service.api_key else 'NOT SET'}")
    print(f"✓ Base URL: {email_service.base_url}")
    print(f"✓ Sender Email: {email_service.sender_email}")
    print(f"✓ Sender Name: {email_service.sender_name}")
    
    if not email_service.api_key:
        print("\n❌ ERROR: BREVO_API_KEY is not configured!")
        return False
    
    print("\n✅ Configuration looks good!")
    return True


async def test_send_simple_email():
    """Test 2: Send a simple test email"""
    print("\n" + "="*80)
    print("TEST 2: Send Simple Test Email")
    print("="*80)
    
    test_email = input("\nEnter your email address to receive test email: ").strip()
    
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return False
    
    print(f"\nSending test email to: {test_email}")
    
    html_content = """
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4F46E5;">🎉 Brevo Email Test Successful!</h2>
            <p>This is a test email from TURN Platform using Brevo.</p>
            <p>If you're reading this, the integration is working perfectly!</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Sent via Brevo API<br>
                TURN - Project Manager Career Platform
            </p>
        </body>
    </html>
    """
    
    result = await email_service.send_email(
        to_email=test_email,
        subject="✅ Brevo Integration Test - TURN Platform",
        html_content=html_content,
        to_name="Test User"
    )
    
    print("\n" + "-"*80)
    print("Result:")
    print("-"*80)
    
    if result.get("success"):
        print(f"✅ SUCCESS!")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"   Status: {result.get('message')}")
        print(f"\n📧 Check your inbox at: {test_email}")
        return True
    else:
        print(f"❌ FAILED!")
        print(f"   Error: {result.get('error')}")
        if 'status_code' in result:
            print(f"   Status Code: {result.get('status_code')}")
        return False


async def test_send_template_email():
    """Test 3: Send email using Jinja2 template"""
    print("\n" + "="*80)
    print("TEST 3: Send Template-Based Email")
    print("="*80)
    
    test_email = input("\nEnter your email address for template test: ").strip()
    
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return False
    
    print(f"\nSending OTP verification email to: {test_email}")
    
    result = await email_service.send_verification_otp(
        email=test_email,
        name="Test User"
    )
    
    print("\n" + "-"*80)
    print("Result:")
    print("-"*80)
    
    if result.get("success"):
        print(f"✅ SUCCESS!")
        print(f"   OTP Code: {result.get('otp_code')}")
        print(f"   Template Used: {result.get('template_used')}")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"\n📧 Check your inbox for the OTP email!")
        return True
    else:
        print(f"❌ FAILED!")
        print(f"   Error: {result.get('error')}")
        return False


async def test_auto_application_email():
    """Test 4: Send auto-application notification email"""
    print("\n" + "="*80)
    print("TEST 4: Send Auto-Application Notification")
    print("="*80)
    
    test_email = input("\nEnter your email address for auto-application test: ").strip()
    
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return False
    
    print(f"\nSending auto-application notification to: {test_email}")
    
    result = await email_service.send_job_match_notification(
        email=test_email,
        user_name="Test User",
        job_title="Senior Project Manager",
        company_name="Tech Innovations Inc.",
        match_score=0.92,
        approve_url="https://turn.platform/apply/123/approve",
        reject_url="https://turn.platform/apply/123/reject",
        view_url="https://turn.platform/jobs/123",
        job_details={
            "location": "Remote",
            "job_type": "Full-time",
            "salary_range": "$80,000 - $120,000",
            "experience_level": "Senior",
            "match_reasons": [
                "Strong PMP certification match",
                "Experience with Agile methodologies",
                "Leadership skills align perfectly"
            ]
        }
    )
    
    print("\n" + "-"*80)
    print("Result:")
    print("-"*80)
    
    if result.get("success"):
        print(f"✅ SUCCESS!")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"\n📧 Check your inbox for the job match notification!")
        return True
    else:
        print(f"❌ FAILED!")
        print(f"   Error: {result.get('error')}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("BREVO EMAIL INTEGRATION TEST SUITE")
    print("="*80)
    print("\nThis will test the Brevo email service integration")
    print("Make sure your .env file has the correct BREVO_* variables")
    
    # Test 1: Configuration
    config_ok = await test_brevo_email_config()
    if not config_ok:
        print("\n❌ Configuration test failed. Please check your .env file.")
        return
    
    # Ask which tests to run
    print("\n" + "="*80)
    print("Select tests to run:")
    print("="*80)
    print("1. Simple Email Test")
    print("2. Template Email Test (OTP)")
    print("3. Auto-Application Email Test")
    print("4. Run All Tests")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    results = []
    
    if choice == "1":
        results.append(await test_send_simple_email())
    elif choice == "2":
        results.append(await test_send_template_email())
    elif choice == "3":
        results.append(await test_auto_application_email())
    elif choice == "4":
        results.append(await test_send_simple_email())
        results.append(await test_send_template_email())
        results.append(await test_auto_application_email())
    else:
        print("❌ Invalid choice")
        return
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Brevo integration is working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
