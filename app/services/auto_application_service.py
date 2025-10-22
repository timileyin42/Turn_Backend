"""
AI-Powered Auto-Application Service for TURN Platform
Automatically matches user profiles with job opportunities and applies on user's behalf.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.logger import logger
from app.database.user_models import User, Profile
from app.database.job_models import JobListing, JobApplication, JobMatch
from app.database.cv_models import CV
from app.services.ai_service import ai_service, AICoachingType
from app.services.job_matching_service import job_matching_service
from app.services.job_search_service import job_search_service
from app.services.email_service import email_service
from app.schemas.job_schemas import JobApplicationCreate


class AutoApplicationCriteria:
    """Criteria for auto-application matching."""
    
    def __init__(
        self,
        min_match_score: float = 0.75,
        max_daily_applications: int = 5,
        preferred_locations: List[str] = None,
        required_skills: List[str] = None,
        excluded_companies: List[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        remote_only: bool = False,
        experience_level_match: bool = True
    ):
        self.min_match_score = min_match_score
        self.max_daily_applications = max_daily_applications
        self.preferred_locations = preferred_locations or []
        self.required_skills = required_skills or []
        self.excluded_companies = excluded_companies or []
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.remote_only = remote_only
        self.experience_level_match = experience_level_match


class AutoApplicationService:
    """
    AI-powered auto-application service that intelligently matches users with jobs
    and automatically applies on their behalf after user approval.
    """
    
    def __init__(self):
        self.logger = logger
        
    async def find_job_matches_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        criteria: AutoApplicationCriteria
    ) -> List[Dict[str, Any]]:
        """
        Find job matches for a user based on their profile and criteria.
        
        Args:
            db: Database session
            user_id: User ID to find matches for
            criteria: Auto-application criteria
            
        Returns:
            List of matched jobs with scores and reasons
        """
        try:
            # Get user profile data
            user_profile = await self._get_comprehensive_user_profile(db, user_id)
            if not user_profile:
                self.logger.warning(f"No profile found for user {user_id}")
                return []
            
            # Fetch recent job postings
            jobs = await self._fetch_fresh_job_postings(db, criteria)
            if not jobs:
                self.logger.info("No fresh job postings found")
                return []
            
            # Get AI-powered job recommendations
            recommendations = await job_matching_service.get_job_recommendations(
                db=db,
                user_id=user_id,
                jobs=jobs,
                limit=50  # Get more for filtering
            )
            
            # Filter recommendations based on criteria
            filtered_matches = []
            for rec in recommendations:
                if await self._meets_auto_application_criteria(rec, criteria, user_profile):
                    # Check if already applied
                    if not await self._has_already_applied(db, user_id, rec.job):
                        filtered_matches.append({
                            "job": rec.job,
                            "similarity_score": rec.similarity_score,
                            "match_reasons": rec.match_reasons,
                            "matching_method": rec.matching_method,
                            "auto_apply_score": await self._calculate_auto_apply_score(rec, user_profile),
                            "application_readiness": await self._assess_application_readiness(db, user_id, rec.job)
                        })
            
            # Sort by auto-apply score
            filtered_matches.sort(key=lambda x: x["auto_apply_score"], reverse=True)
            
            # Limit by daily application quota
            return filtered_matches[:criteria.max_daily_applications]
            
        except Exception as e:
            self.logger.error(f"Error finding job matches for user {user_id}: {str(e)}")
            return []
    
    async def generate_ai_application(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI-powered job application (CV + Cover Letter).
        
        Args:
            db: Database session
            user_id: User ID
            job_data: Job posting information
            
        Returns:
            Generated application materials
        """
        try:
            # Get user's latest CV and profile
            user_profile = await self._get_comprehensive_user_profile(db, user_id)
            cv_data = await self._get_user_cv_data(db, user_id)
            
            if not cv_data:
                raise ValueError("No CV found for user")
            
            # Generate customized cover letter using AI
            cover_letter = await self._generate_ai_cover_letter(
                user_profile=user_profile,
                cv_data=cv_data,
                job_data=job_data
            )
            
            # Generate CV customizations
            cv_customizations = await self._generate_cv_customizations(
                cv_data=cv_data,
                job_data=job_data
            )
            
            # Generate application summary
            application_summary = await self._generate_application_summary(
                user_profile=user_profile,
                job_data=job_data,
                cover_letter=cover_letter
            )
            
            return {
                "cover_letter": cover_letter,
                "cv_customizations": cv_customizations,
                "application_summary": application_summary,
                "generated_at": datetime.utcnow().isoformat(),
                "confidence_score": self._calculate_application_confidence(
                    user_profile, job_data
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error generating AI application: {str(e)}")
            raise
    
    async def submit_auto_application(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any],
        application_materials: Dict[str, Any],
        user_approved: bool = False
    ) -> Dict[str, Any]:
        """
        Submit auto-application on behalf of user.
        
        Args:
            db: Database session
            user_id: User ID
            job_data: Job posting data
            application_materials: Generated application materials
            user_approved: Whether user explicitly approved this application
            
        Returns:
            Application submission result
        """
        try:
            if not user_approved:
                # Store as pending application for user approval
                return await self._create_pending_application(
                    db, user_id, job_data, application_materials
                )
            
            # Create job application record
            job_application = JobApplication(
                user_id=user_id,
                job_listing_id=job_data.get("id"),
                cover_letter=application_materials["cover_letter"],
                cv_version_used="auto_generated",
                customized_cv_content=application_materials["cv_customizations"],
                status="submitted",
                applied_at=datetime.utcnow(),
                application_method="auto_application",
                notes=f"Auto-applied using AI. Confidence: {application_materials['confidence_score']:.2f}"
            )
            
            db.add(job_application)
            await db.commit()
            await db.refresh(job_application)
            
            # Send application via appropriate channel
            submission_result = await self._send_application_to_employer(
                job_data=job_data,
                application_materials=application_materials,
                user_id=user_id
            )
            
            # Log application submission
            await self._log_application_submission(
                db, user_id, job_application.id, submission_result
            )
            
            # Send confirmation email to user
            await self._send_application_confirmation_email(
                db, user_id, job_data, application_materials, submission_result
            )
            
            return {
                "application_id": job_application.id,
                "status": "submitted",
                "submission_result": submission_result,
                "submitted_at": job_application.applied_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting auto application: {str(e)}")
            raise
    
    async def get_pending_applications(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get pending applications requiring user approval."""
        # This would fetch from a PendingApplications table
        # For now, return empty list as we need to create the table first
        return []
    
    async def approve_pending_application(
        self,
        db: AsyncSession,
        user_id: int,
        pending_application_id: int
    ) -> Dict[str, Any]:
        """Approve and submit a pending application."""
        # Implementation would fetch pending application and submit it
        pass
    
    async def reject_pending_application(
        self,
        db: AsyncSession,
        user_id: int,
        pending_application_id: int,
        reason: str = None
    ) -> Dict[str, Any]:
        """Reject a pending application."""
        # Implementation would mark pending application as rejected
        pass
    
    # Private helper methods
    
    async def _get_comprehensive_user_profile(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive user profile for matching."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile).selectinload(Profile.skills))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.profile:
            return None
        
        profile = user.profile
        return {
            "user_id": user_id,
            "name": f"{profile.first_name} {profile.last_name}".strip(),
            "email": user.email,
            "current_job_title": profile.current_job_title,
            "company": profile.company,
            "years_of_experience": profile.years_of_experience,
            "career_goals": profile.career_goals,
            "target_industries": profile.target_industries,
            "preferred_work_mode": profile.preferred_work_mode,
            "skills": [skill.skill_name for skill in profile.skills],
            "location": f"{profile.city}, {profile.country}" if profile.city else profile.country,
            "bio": profile.bio
        }
    
    async def _fetch_fresh_job_postings(
        self,
        db: AsyncSession,
        criteria: AutoApplicationCriteria
    ) -> List[Dict[str, Any]]:
        """Fetch fresh job postings from external sources."""
        try:
            # Get fresh jobs from external APIs
            fresh_jobs = await job_search_service.fetch_all_pm_jobs()
            normalized_jobs = job_search_service.normalize_job_data(fresh_jobs)
            
            # Filter based on basic criteria
            filtered_jobs = []
            for job in normalized_jobs:
                # Location filter
                if criteria.preferred_locations:
                    job_location = job.get("location", "").lower()
                    if not any(loc.lower() in job_location for loc in criteria.preferred_locations):
                        if not (criteria.remote_only and "remote" in job_location):
                            continue
                
                # Remote filter
                if criteria.remote_only:
                    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('location', '')}".lower()
                    if "remote" not in job_text:
                        continue
                
                # Salary filter
                if criteria.salary_min and job.get("salary_min"):
                    if job["salary_min"] < criteria.salary_min:
                        continue
                
                # Excluded companies
                if criteria.excluded_companies:
                    company = job.get("company", "").lower()
                    if any(exc.lower() in company for exc in criteria.excluded_companies):
                        continue
                
                filtered_jobs.append(job)
            
            return filtered_jobs[:100]  # Limit for performance
            
        except Exception as e:
            self.logger.error(f"Error fetching fresh job postings: {str(e)}")
            return []
    
    async def _meets_auto_application_criteria(
        self,
        recommendation: Any,
        criteria: AutoApplicationCriteria,
        user_profile: Dict[str, Any]
    ) -> bool:
        """Check if job recommendation meets auto-application criteria."""
        # Check minimum match score
        if recommendation.similarity_score < criteria.min_match_score:
            return False
        
        job = recommendation.job
        
        # Check required skills
        if criteria.required_skills:
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            required_found = sum(1 for skill in criteria.required_skills 
                               if skill.lower() in job_text)
            if required_found < len(criteria.required_skills) * 0.7:  # 70% of required skills
                return False
        
        # Experience level matching
        if criteria.experience_level_match:
            user_experience = user_profile.get("years_of_experience", 0)
            job_description = job.get("description", "").lower()
            
            # Simple experience level detection
            if user_experience < 2 and any(word in job_description for word in ["senior", "lead", "principal"]):
                return False
            elif user_experience > 8 and any(word in job_description for word in ["junior", "entry", "intern"]):
                return False
        
        return True
    
    async def _has_already_applied(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any]
    ) -> bool:
        """Check if user has already applied to this job."""
        # This is a simplified check - in practice, you'd need better job deduplication
        job_title = job_data.get("title", "")
        company = job_data.get("company", "")
        
        result = await db.execute(
            select(JobApplication)
            .join(JobListing)
            .where(
                and_(
                    JobApplication.user_id == user_id,
                    JobListing.title.ilike(f"%{job_title}%"),
                    JobListing.company.ilike(f"%{company}%"),
                    JobApplication.applied_at > datetime.utcnow() - timedelta(days=30)
                )
            )
        )
        
        return result.first() is not None
    
    async def _calculate_auto_apply_score(
        self,
        recommendation: Any,
        user_profile: Dict[str, Any]
    ) -> float:
        """Calculate auto-application score (0-1)."""
        score = recommendation.similarity_score
        
        # Boost score based on various factors
        job = recommendation.job
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        # Career goals alignment
        if user_profile.get("career_goals"):
            career_goals = user_profile["career_goals"].lower()
            if any(goal in job_text for goal in career_goals.split()):
                score += 0.1
        
        # Experience level match
        user_exp = user_profile.get("years_of_experience", 0)
        if 2 <= user_exp <= 8:  # Mid-level gets boost for most jobs
            score += 0.05
        
        # Remote work preference
        if user_profile.get("preferred_work_mode") == "remote" and "remote" in job_text:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _assess_application_readiness(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess how ready the user's profile is for this application."""
        # Get user's CV completeness
        cv_data = await self._get_user_cv_data(db, user_id)
        
        readiness_score = 0.0
        missing_items = []
        
        if cv_data:
            readiness_score += 0.4
            if cv_data.get("summary"):
                readiness_score += 0.1
            if cv_data.get("experiences"):
                readiness_score += 0.2
            if cv_data.get("education"):
                readiness_score += 0.1
            if cv_data.get("skills"):
                readiness_score += 0.2
        else:
            missing_items.append("CV")
        
        # Check profile completeness
        user_profile = await self._get_comprehensive_user_profile(db, user_id)
        if user_profile:
            if not user_profile.get("career_goals"):
                missing_items.append("Career goals")
            if not user_profile.get("skills"):
                missing_items.append("Skills")
        
        return {
            "readiness_score": readiness_score,
            "missing_items": missing_items,
            "can_auto_apply": readiness_score >= 0.7
        }
    
    async def _get_user_cv_data(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get user's CV data."""
        result = await db.execute(
            select(CV)
            .options(
                selectinload(CV.experiences),
                selectinload(CV.education),
                selectinload(CV.skills)
            )
            .where(and_(CV.user_id == user_id, CV.is_default == True))
        )
        cv = result.scalar_one_or_none()
        
        if not cv:
            return None
        
        return {
            "id": cv.id,
            "title": cv.title,
            "summary": cv.summary,
            "experiences": [
                {
                    "job_title": exp.job_title,
                    "company_name": exp.company_name,
                    "description": exp.description,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None
                }
                for exp in cv.experiences
            ],
            "education": [
                {
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "institution": edu.institution,
                    "graduation_date": edu.graduation_date.isoformat() if edu.graduation_date else None
                }
                for edu in cv.education
            ],
            "skills": [skill.skill_name for skill in cv.skills]
        }
    
    async def _generate_ai_cover_letter(
        self,
        user_profile: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """Generate AI-powered cover letter."""
        prompt = f"""
        Generate a professional cover letter for this job application:
        
        Job Details:
        - Title: {job_data.get('title', 'N/A')}
        - Company: {job_data.get('company', 'N/A')}
        - Description: {job_data.get('description', 'N/A')[:500]}...
        
        Candidate Profile:
        - Name: {user_profile.get('name', 'Candidate')}
        - Current Role: {user_profile.get('current_job_title', 'N/A')}
        - Experience: {user_profile.get('years_of_experience', 0)} years
        - Key Skills: {', '.join(user_profile.get('skills', [])[:5])}
        - Career Goals: {user_profile.get('career_goals', 'N/A')}
        
        Recent Experience:
        {cv_data.get('experiences', [{}])[0].get('description', 'N/A') if cv_data.get('experiences') else 'N/A'}
        
        Write a compelling, personalized cover letter that:
        1. Shows enthusiasm for the specific role and company
        2. Highlights relevant experience and skills
        3. Demonstrates knowledge of the company/industry
        4. Is professional yet personable
        5. Is 3-4 paragraphs, not too long
        6. Do not make it yappy or generic.
        
        Return only the cover letter text, no additional formatting.
        """
        
        try:
            response = await ai_service.get_ai_coaching_session(
                coaching_type=AICoachingType.CAREER_GUIDANCE,
                user_question=prompt,
                user_context=user_profile
            )
            
            return response.get("response", "").strip()
            
        except Exception as e:
            self.logger.error(f"Error generating AI cover letter: {str(e)}")
            return self._get_fallback_cover_letter(user_profile, job_data)
    
    async def _generate_cv_customizations(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate CV customizations for specific job."""
        # Extract key requirements from job description
        job_description = job_data.get("description", "").lower()
        job_title = job_data.get("title", "").lower()
        
        # Suggest skills to highlight
        user_skills = [skill.lower() for skill in cv_data.get("skills", [])]
        relevant_skills = []
        
        for skill in user_skills:
            if skill in job_description or skill in job_title:
                relevant_skills.append(skill)
        
        # Suggest experience points to emphasize
        experiences = cv_data.get("experiences", [])
        relevant_experiences = []
        
        for exp in experiences:
            exp_desc = exp.get("description", "").lower()
            if any(keyword in exp_desc for keyword in ["project", "manage", "lead", "coordinate"]):
                relevant_experiences.append(exp["job_title"])
        
        return {
            "skills_to_highlight": relevant_skills[:5],
            "experiences_to_emphasize": relevant_experiences[:3],
            "suggested_summary_focus": f"Emphasize {job_title} experience and {relevant_skills[0] if relevant_skills else 'project management'} skills",
            "keywords_to_include": self._extract_job_keywords(job_data)
        }
    
    async def _generate_application_summary(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        cover_letter: str
    ) -> str:
        """Generate a summary of the application."""
        return f"""
        Application Summary for {job_data.get('title', 'Position')} at {job_data.get('company', 'Company')}
        
        Candidate: {user_profile.get('name', 'Candidate')}
        Match Strength: Based on {user_profile.get('years_of_experience', 0)} years experience and relevant skills
        
        Key Selling Points:
        - {user_profile.get('current_job_title', 'Current role')} with transferable skills
        - Relevant experience in {', '.join(user_profile.get('skills', [])[:3])}
        - Strong alignment with career goals
        
        Cover Letter Highlights:
        {cover_letter[:200]}...
        
        Application generated using AI optimization for maximum relevance.
        """
    
    def _calculate_application_confidence(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for application (0-1)."""
        confidence = 0.5  # Base confidence
        
        # Experience match
        user_exp = user_profile.get("years_of_experience", 0)
        if 2 <= user_exp <= 10:
            confidence += 0.2
        
        # Skills match
        user_skills = [skill.lower() for skill in user_profile.get("skills", [])]
        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')}".lower()
        skill_matches = sum(1 for skill in user_skills if skill in job_text)
        confidence += min(skill_matches * 0.1, 0.3)
        
        return min(confidence, 1.0)
    
    def _get_fallback_cover_letter(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """Fallback cover letter when AI fails."""
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_data.get('title', 'position')} role at {job_data.get('company', 'your company')}. With {user_profile.get('years_of_experience', 'several')} years of experience in {user_profile.get('current_job_title', 'the field')}, I am excited about the opportunity to contribute to your team.

My background in {', '.join(user_profile.get('skills', ['project management'])[:3])} aligns well with the requirements outlined in your job posting. In my current role, I have developed strong skills in problem-solving, team collaboration, and strategic thinking that would be valuable in this position.

I am particularly drawn to this opportunity because it aligns with my career goals of {user_profile.get('career_goals', 'professional growth and making meaningful contributions')}. I would welcome the chance to discuss how my experience and passion can benefit your organization.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
{user_profile.get('name', 'Candidate')}"""
    
    def _extract_job_keywords(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract important keywords from job posting."""
        description = job_data.get("description", "").lower()
        title = job_data.get("title", "").lower()
        
        # Common PM keywords to look for
        pm_keywords = [
            "project management", "scrum", "agile", "kanban", "jira", "confluence",
            "stakeholder", "roadmap", "strategy", "planning", "execution",
            "leadership", "team", "communication", "analysis", "reporting", "sofware development",
            "risk management", "budgeting", "scheduling", "resource allocation"
        ]
        
        found_keywords = []
        text = f"{title} {description}"
        
        for keyword in pm_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords[:8]
    
    async def _create_pending_application(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any],
        application_materials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create pending application for user approval."""
        # This would create a record in PendingApplications table
        # For now, return a mock response
        return {
            "pending_application_id": f"pending_{user_id}_{datetime.utcnow().timestamp()}",
            "status": "pending_approval",
            "job_title": job_data.get("title"),
            "company": job_data.get("company"),
            "created_at": datetime.utcnow().isoformat(),
            "requires_approval": True
        }
    
    async def _send_application_to_employer(
        self,
        job_data: Dict[str, Any],
        application_materials: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Send application to employer via appropriate channel."""
        # This would integrate with various job boards/ATS systems
        # For now, return a mock response
        return {
            "method": "email",
            "status": "sent",
            "recipient": job_data.get("contact_email", "hr@company.com"),
            "sent_at": datetime.utcnow().isoformat(),
            "confirmation_id": f"app_{user_id}_{datetime.utcnow().timestamp()}"
        }
    
    async def _log_application_submission(
        self,
        db: AsyncSession,
        user_id: int,
        application_id: int,
        submission_result: Dict[str, Any]
    ) -> None:
        """Log application submission for tracking."""
        self.logger.info(f"Auto-application submitted: user={user_id}, app={application_id}, result={submission_result}")
    
    async def _send_application_confirmation_email(
        self,
        db: AsyncSession,
        user_id: int,
        job_data: Dict[str, Any],
        application_materials: Dict[str, Any],
        submission_result: Dict[str, Any]
    ) -> None:
        """Send confirmation email to user."""
        try:
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            
            if user:
                await email_service.send_auto_application_confirmation(
                    user_email=user.email,
                    job_title=job_data.get("title"),
                    company=job_data.get("company"),
                    application_details=application_materials,
                    submission_result=submission_result
                )
        except Exception as e:
            self.logger.error(f"Error sending confirmation email: {str(e)}")


# Global service instance
auto_application_service = AutoApplicationService()