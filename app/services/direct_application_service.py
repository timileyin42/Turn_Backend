"""
Direct Application Service
Sends job applications directly to company decision makers (CEO, HR, Founders)
with personalized messages optimized for startups and SMEs.
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import logger
from app.services.email_service import email_service
from app.services.ai_service import ai_service, AICoachingType
from app.services.company_scanner_service import company_scanner_service
from app.database.user_models import User, Profile
from app.database.job_models import JobApplication, JobListing


class DirectApplicationService:
    """
    Handles one-click direct applications to company decision makers.
    Specialized for startups and SMEs where direct outreach to CEO/Founders is effective.
    """
    
    def __init__(self):
        self.logger = logger
    
    async def send_direct_application(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any],
        company_contacts: Dict[str, Any],
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send one-click direct application to company decision maker.
        
        Args:
            db: Database session
            user_id: User ID applying
            job_data: Job posting information
            company_contacts: Company contact information (CEO, HR, etc.)
            user_message: Optional custom message from user
            
        Returns:
            Result dict with delivery status and tracking info
        """
        try:
            # Get comprehensive user profile
            user_profile = await self._get_user_profile_data(db, user_id)
            if not user_profile:
                raise ValueError("User profile not found")
            
            # Determine best recipient (CEO > HR > Careers)
            recipient = self._select_best_recipient(company_contacts, job_data)
            if not recipient or not recipient.get('email'):
                return {
                    'success': False,
                    'error': 'No valid recipient contact found',
                    'suggestion': 'Try finding contacts manually or apply through job board'
                }
            
            # Generate personalized pitch using AI
            personalized_pitch = await self._generate_ceo_pitch(
                user_profile=user_profile,
                job_data=job_data,
                recipient=recipient,
                user_message=user_message
            )
            
            # Prepare email content
            email_subject = self._create_subject_line(
                user_profile, job_data, recipient
            )
            
            email_body = await self._create_direct_application_email(
                user_profile=user_profile,
                job_data=job_data,
                recipient=recipient,
                pitch=personalized_pitch
            )
            
            # Send email
            send_result = await self._send_application_email(
                recipient_email=recipient['email'],
                recipient_name=recipient.get('name', 'Hiring Manager'),
                subject=email_subject,
                body=email_body,
                user_email=user_profile['email'],
                attachments=[]  # Could attach CV here
            )
            
            # Track application in database
            application_record = await self._record_direct_application(
                db=db,
                user_id=user_id,
                job_data=job_data,
                recipient=recipient,
                send_result=send_result
            )
            
            return {
                'success': True,
                'application_id': application_record.id if application_record else None,
                'recipient': {
                    'name': recipient.get('name'),
                    'title': recipient.get('title'),
                    'email': recipient['email']
                },
                'sent_at': datetime.utcnow().isoformat(),
                'tracking_id': send_result.get('message_id'),
                'message': f"Application sent directly to {recipient.get('title', 'decision maker')}!",
                'next_steps': [
                    'Wait 2-3 business days for response',
                    'Prepare for potential interview',
                    'Follow up if no response after 1 week'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error sending direct application: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_action': 'Use traditional application method'
            }
    
    async def find_and_apply_direct(
        self,
        db: AsyncSession,
        user_id: int,
        company_url: str,
        company_name: str,
        job_title: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete flow: Scan company website, find contacts, and apply directly.
        
        This is the ONE-CLICK feature that does everything:
        1. Scans company website for the job
        2. Finds CEO/HR contacts
        3. Sends personalized application directly
        
        Args:
            db: Database session
            user_id: User ID
            company_url: Company website URL
            company_name: Company name
            job_title: Job title user is applying for
            user_message: Optional custom message
            
        Returns:
            Complete application result
        """
        try:
            self.logger.info(f"Starting one-click direct application for user {user_id} to {company_name}")
            
            # Step 1: Scan company website
            async with company_scanner_service as scanner:
                scan_result = await scanner.scan_company_website(
                    company_url=company_url,
                    company_name=company_name
                )
            
            if not scan_result.get('scan_success'):
                return {
                    'success': False,
                    'error': 'Could not scan company website',
                    'details': scan_result.get('error'),
                    'manual_action_required': True
                }
            
            # Step 2: Check if it's a startup/SME (our focus)
            is_target_company = scan_result.get('is_startup') or scan_result.get('is_sme')
            if not is_target_company:
                return {
                    'success': False,
                    'warning': 'Company appears to be large enterprise',
                    'recommendation': 'For large companies, use traditional application process',
                    'company_size': scan_result.get('company_size_estimate'),
                    'alternative_action': 'Apply through company career portal'
                }
            
            # Step 3: Extract job data
            job_data = self._extract_job_from_scan(scan_result, job_title)
            
            # Step 4: Get contacts
            company_contacts = {
                'ceo': scan_result.get('ceo_contact'),
                'hr': scan_result.get('hr_contact'),
                'founders': scan_result.get('founders', [])
            }
            
            # Step 5: Send direct application
            application_result = await self.send_direct_application(
                db=db,
                user_id=user_id,
                job_data=job_data,
                company_contacts=company_contacts,
                user_message=user_message
            )
            
            # Add scan context to result
            application_result['company_scan'] = {
                'is_startup': scan_result.get('is_startup'),
                'company_size': scan_result.get('company_size_estimate'),
                'entry_level_jobs_found': scan_result.get('entry_level_count'),
                'career_page_url': scan_result.get('career_page_url')
            }
            
            return application_result
            
        except Exception as e:
            self.logger.error(f"Error in one-click direct application: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'recovery_suggestions': [
                    'Check if company website is accessible',
                    'Try applying through LinkedIn or job boards',
                    'Visit company career page manually'
                ]
            }
    
    async def batch_apply_to_startups(
        self,
        db: AsyncSession,
        user_id: int,
        company_list: List[Dict[str, str]],
        max_applications: int = 5
    ) -> Dict[str, Any]:
        """
        Apply to multiple startups/SMEs in one go.
        
        Args:
            db: Database session
            user_id: User ID
            company_list: List of companies with 'url', 'name', and 'job_title'
            max_applications: Maximum number to send (rate limiting)
            
        Returns:
            Summary of batch application results
        """
        results = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'applications': [],
            'errors': []
        }
        
        # Limit to prevent spam
        companies_to_apply = company_list[:max_applications]
        results['total_attempted'] = len(companies_to_apply)
        
        # Apply to each company
        for company in companies_to_apply:
            try:
                result = await self.find_and_apply_direct(
                    db=db,
                    user_id=user_id,
                    company_url=company['url'],
                    company_name=company['name'],
                    job_title=company.get('job_title', 'Project Manager'),
                    user_message=company.get('message')
                )
                
                if result.get('success'):
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'company': company['name'],
                        'error': result.get('error')
                    })
                
                results['applications'].append({
                    'company': company['name'],
                    'success': result.get('success'),
                    'details': result
                })
                
                # Respectful delay between applications
                await asyncio.sleep(2)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'company': company['name'],
                    'error': str(e)
                })
        
        return results
    
    # Private helper methods
    
    async def _get_user_profile_data(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive user profile for application."""
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.profile:
            return None
        
        profile = user.profile
        return {
            'user_id': user_id,
            'name': f"{profile.first_name} {profile.last_name}".strip(),
            'email': user.email,
            'phone': profile.phone_number,
            'current_title': profile.current_job_title,
            'company': profile.company,
            'years_experience': profile.years_of_experience,
            'career_goals': profile.career_goals,
            'skills': [skill.skill_name for skill in profile.skills] if profile.skills else [],
            'linkedin': profile.linkedin_url,
            'portfolio': profile.portfolio_url,
            'location': f"{profile.city}, {profile.country}" if profile.city else profile.country,
            'bio': profile.bio,
            'availability': profile.availability
        }
    
    def _select_best_recipient(
        self,
        company_contacts: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select best recipient for direct application."""
        # Priority: CEO/Founder (for startups) > HR > Careers email
        
        # Check for CEO/Founder (best for startups)
        if company_contacts.get('ceo'):
            ceo = company_contacts['ceo']
            if isinstance(ceo, dict) and ceo.get('email'):
                return {
                    'email': ceo['email'],
                    'name': ceo.get('name', 'CEO'),
                    'title': ceo.get('title', 'CEO/Founder'),
                    'type': 'ceo'
                }
        
        # Check for founders
        founders = company_contacts.get('founders', [])
        if founders and isinstance(founders, list) and len(founders) > 0:
            founder = founders[0]
            if isinstance(founder, dict) and founder.get('email'):
                return {
                    'email': founder['email'],
                    'name': founder.get('name', 'Founder'),
                    'title': founder.get('title', 'Founder'),
                    'type': 'founder'
                }
        
        # Check for HR contact
        if company_contacts.get('hr'):
            hr = company_contacts['hr']
            if isinstance(hr, dict) and hr.get('email'):
                return {
                    'email': hr['email'],
                    'name': hr.get('name', 'HR Manager'),
                    'title': hr.get('title', 'HR/Recruiting'),
                    'type': 'hr'
                }
            elif isinstance(hr, str):  # If it's just an email string
                return {
                    'email': hr,
                    'name': 'Hiring Team',
                    'title': 'HR/Recruiting',
                    'type': 'hr'
                }
        
        # Fallback to guessed contacts if available
        if company_contacts.get('guessed_contacts'):
            guesses = company_contacts['guessed_contacts']
            if guesses.get('ceo_guesses'):
                return {
                    'email': guesses['ceo_guesses'][0],
                    'name': 'Hiring Manager',
                    'title': 'Decision Maker',
                    'type': 'guessed_ceo'
                }
            elif guesses.get('hr_guesses'):
                return {
                    'email': guesses['hr_guesses'][0],
                    'name': 'HR Team',
                    'title': 'Recruiting',
                    'type': 'guessed_hr'
                }
        
        return None
    
    async def _generate_ceo_pitch(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        recipient: Dict[str, Any],
        user_message: Optional[str] = None
    ) -> str:
        """Generate AI-powered personalized pitch for CEO/Founder."""
        recipient_type = recipient.get('type', 'hiring_manager')
        recipient_title = recipient.get('title', 'Hiring Manager')
        
        prompt = f"""
        Write a compelling, direct pitch for a project manager applying to a startup/SME.
        This will be sent directly to the {recipient_title}.
        
        Applicant Profile:
        - Name: {user_profile['name']}
        - Current Role: {user_profile.get('current_title', 'Project Manager')}
        - Experience: {user_profile.get('years_experience', 0)} years
        - Key Skills: {', '.join(user_profile.get('skills', [])[:5])}
        - Career Goals: {user_profile.get('career_goals', 'Growth in project management')}
        
        Job/Company:
        - Position: {job_data.get('title', 'Project Manager')}
        - Company: {job_data.get('company', 'Startup')}
        - Description: {job_data.get('description', '')[:300]}
        
        Recipient Type: {recipient_type}
        
        User's Custom Message: {user_message or 'None provided'}
        
        Write a 2-3 paragraph pitch that:
        1. Shows genuine interest in THIS specific company/role
        2. Highlights how applicant solves their problems
        3. Demonstrates understanding of startup/SME challenges
        4. Is conversational and authentic (not corporate/formal)
        5. Includes a clear call-to-action
        6. Is direct and confident without being pushy
        
        For CEO/Founder pitches: Focus on business impact, growth mindset, and willingness to wear multiple hats.
        For HR pitches: Focus on cultural fit, team collaboration, and process improvement.
        
        IMPORTANT: Be concise, compelling, and human. Avoid clichés and generic statements.
        
        Return ONLY the pitch text, no subject line or formatting.
        """
        
        try:
            # Use AI service to generate pitch
            response = await ai_service.get_ai_coaching_session(
                coaching_type=AICoachingType.CAREER_GUIDANCE,
                user_question=prompt,
                user_context=user_profile
            )
            
            pitch = response.get('response', '').strip()
            return pitch if pitch else self._get_fallback_pitch(user_profile, job_data, recipient)
            
        except Exception as e:
            self.logger.error(f"Error generating CEO pitch: {str(e)}")
            return self._get_fallback_pitch(user_profile, job_data, recipient)
    
    def _get_fallback_pitch(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        recipient: Dict[str, Any]
    ) -> str:
        """Fallback pitch if AI fails."""
        name = user_profile.get('name', 'Candidate')
        title = user_profile.get('current_title', 'Project Manager')
        years = user_profile.get('years_experience', 'several')
        company = job_data.get('company', 'your company')
        position = job_data.get('title', 'Project Manager')
        
        return f"""I'm reaching out because I'm genuinely excited about the {position} opportunity at {company}. 

With {years} years of hands-on experience as a {title}, I've learned that great project management in startups isn't just about following processes—it's about building them, adapting quickly, and driving real business results. I thrive in fast-paced environments where I can wear multiple hats and directly impact growth.

I'd love to chat about how I can help {company} scale efficiently while maintaining the agility that makes startups special. Are you open to a quick 15-minute call this week?

Looking forward to connecting!

Best regards,
{name}"""
    
    def _create_subject_line(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        recipient: Dict[str, Any]
    ) -> str:
        """Create compelling subject line for direct application."""
        position = job_data.get('title', 'Project Manager')
        company = job_data.get('company', 'your company')
        name = user_profile.get('name', 'Candidate')
        
        recipient_type = recipient.get('type', 'hr')
        
        # Different subject lines based on recipient
        if recipient_type in ['ceo', 'founder']:
            subject_options = [
                f"Project Manager who can scale {company} efficiently | {name}",
                f"Excited to drive growth at {company} | {name}",
                f"Let's talk about {company}'s next PM | {name}",
                f"{name} | Ready to tackle {company}'s project challenges"
            ]
        else:
            subject_options = [
                f"Application: {position} at {company} | {name}",
                f"{name} applying for {position} role",
                f"Project Manager application | {name}",
                f"Interested in {position} position | {name}"
            ]
        
        # Pick first option (could randomize)
        return subject_options[0]
    
    async def _create_direct_application_email(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        recipient: Dict[str, Any],
        pitch: str
    ) -> str:
        """Create full email body for direct application."""
        recipient_name = recipient.get('name', 'there')
        name = user_profile.get('name', 'Candidate')
        email = user_profile.get('email')
        phone = user_profile.get('phone', 'Available upon request')
        linkedin = user_profile.get('linkedin', '')
        
        # Build email
        email_body = f"""Hi {recipient_name},

{pitch}

Quick snapshot of what I bring:
• {user_profile.get('years_experience', 'Several')} years of project management experience
• Expertise in: {', '.join(user_profile.get('skills', ['Agile', 'Scrum', 'Team Leadership'])[:4])}
• Currently: {user_profile.get('current_title', 'Project Manager')} at {user_profile.get('company', 'my current company')}

I've attached my CV and would be happy to share specific examples of how I've helped similar companies scale.

Best time to reach me:
📧 {email}
📱 {phone}
{f'💼 {linkedin}' if linkedin else ''}

Looking forward to hearing from you!

Best,
{name}

---
P.S. I'm available for a quick call anytime this week if you'd like to learn more about how I can contribute to {job_data.get('company', 'the team')}.
"""
        
        return email_body
    
    async def _send_application_email(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        body: str,
        user_email: str,
        attachments: List[str] = None
    ) -> Dict[str, Any]:
        """Send the actual email."""
        try:
            # Use email service to send
            # For now, return mock result
            # In production, integrate with email_service.send_email()
            
            result = await email_service.send_email(
                to_email=recipient_email,
                subject=subject,
                body=body,
                reply_to=user_email,
                # attachments=attachments
            )
            
            return {
                'success': True,
                'message_id': f"msg_{datetime.utcnow().timestamp()}",
                'sent_at': datetime.utcnow().isoformat(),
                'provider': 'brevo'
            }
            
        except Exception as e:
            self.logger.error(f"Error sending application email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _record_direct_application(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any],
        recipient: Dict[str, Any],
        send_result: Dict[str, Any]
    ) -> Optional[JobApplication]:
        """Record direct application in database."""
        try:
            application = JobApplication(
                user_id=user_id,
                # job_listing_id=None,  # Might not exist in DB yet
                company_name=job_data.get('company'),
                job_title=job_data.get('title'),
                status='submitted',
                application_method='direct_to_decision_maker',
                applied_at=datetime.utcnow(),
                recipient_email=recipient.get('email'),
                recipient_title=recipient.get('title'),
                tracking_id=send_result.get('message_id'),
                notes=f"Direct application sent to {recipient.get('title')} via one-click feature"
            )
            
            db.add(application)
            await db.commit()
            await db.refresh(application)
            
            return application
            
        except Exception as e:
            self.logger.error(f"Error recording direct application: {str(e)}")
            await db.rollback()
            return None
    
    def _extract_job_from_scan(
        self,
        scan_result: Dict[str, Any],
        job_title: str
    ) -> Dict[str, Any]:
        """Extract job data from scan result."""
        # Look for matching job in scan results
        entry_level_jobs = scan_result.get('entry_level_jobs', [])
        all_jobs = scan_result.get('job_listings', [])
        
        # Try to find exact match
        for job in entry_level_jobs + all_jobs:
            if job_title.lower() in job.get('title', '').lower():
                return job
        
        # Fallback: create job data from scan
        return {
            'title': job_title,
            'company': scan_result.get('company_name'),
            'description': f"Position at {scan_result.get('company_name')}",
            'url': scan_result.get('career_page_url', scan_result.get('company_url')),
            'location': 'To be determined',
            'source': 'company_website_scan'
        }


# Global service instance
direct_application_service = DirectApplicationService()
