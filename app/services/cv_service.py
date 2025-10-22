"""
CV/Resume building service for dynamic CV generation, templates, and export functionality.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.database.cv_models import (
    CV, CVSection, CVTemplate, CVExport, 
    Education, WorkExperience, CVSkill, CVProject
)
from app.schemas.cv_schemas import (
    CVCreate, CVUpdate, CVResponse, CVListResponse,
    CVSectionCreate, CVSectionUpdate, CVSectionResponse,
    CVTemplateResponse, CVExportResponse,
    CVEducationCreate, CVEducationUpdate, CVEducationResponse,
    CVExperienceCreate, CVExperienceUpdate, CVExperienceResponse,
    CVSkillCreate, CVSkillUpdate, CVSkillResponse,
    CVProjectCreate, CVProjectUpdate, CVProjectResponse,
    CVSearchRequest, CVAnalyticsResponse
)


class CVService:
    """Service for CV/Resume creation, management, and export operations."""
    
    async def create_cv(
        self, 
        db: AsyncSession, 
        user_id: int, 
        cv_data: CVCreate
    ) -> CVResponse:
        """
        Create a new CV for user.
        
        Args:
            db: Database session
            user_id: CV owner ID
            cv_data: CV creation data
            
        Returns:
            Created CV response
        """
        db_cv = CV(
            user_id=user_id,
            **cv_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_cv)
        await db.commit()
        await db.refresh(db_cv)
        
        return CVResponse.model_validate(db_cv)
    
    async def get_cv_by_id(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int
    ) -> Optional[CVResponse]:
        """
        Get CV by ID with access control.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: Requesting user ID
            
        Returns:
            CV response if user has access
        """
        result = await db.execute(
            select(CV)
            .options(
                selectinload(CV.sections),
                selectinload(CV.education),
                selectinload(CV.experience),
                selectinload(CV.skills),
                selectinload(CV.projects)
            )
            .where(
                and_(
                    CV.id == cv_id,
                    CV.user_id == user_id
                )
            )
        )
        cv = result.scalar_one_or_none()
        
        if not cv:
            return None
        
        return CVResponse.model_validate(cv)
    
    async def update_cv(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int, 
        cv_data: CVUpdate
    ) -> Optional[CVResponse]:
        """
        Update CV information.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID (must be owner)
            cv_data: Updated CV data
            
        Returns:
            Updated CV response
        """
        result = await db.execute(
            select(CV).where(
                and_(
                    CV.id == cv_id,
                    CV.user_id == user_id
                )
            )
        )
        cv = result.scalar_one_or_none()
        
        if not cv:
            return None
        
        # Update fields
        update_data = cv_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(cv, field, value)
            
            cv.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(cv)
        
        return CVResponse.model_validate(cv)
    
    async def delete_cv(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int
    ) -> bool:
        """
        Delete CV (owner only).
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID (must be owner)
            
        Returns:
            True if CV was deleted
        """
        result = await db.execute(
            select(CV).where(
                and_(
                    CV.id == cv_id,
                    CV.user_id == user_id
                )
            )
        )
        cv = result.scalar_one_or_none()
        
        if cv:
            await db.delete(cv)
            await db.commit()
            return True
        
        return False
    
    async def get_user_cvs(
        self, 
        db: AsyncSession, 
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> CVListResponse:
        """
        Get all CVs for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Paginated CV list
        """
        # Count total
        count_result = await db.execute(
            select(func.count(CV.id)).where(CV.user_id == user_id)
        )
        total = count_result.scalar()
        
        # Get CVs with pagination
        result = await db.execute(
            select(CV)
            .options(selectinload(CV.sections))
            .where(CV.user_id == user_id)
            .order_by(desc(CV.updated_at))
            .offset(skip)
            .limit(limit)
        )
        cvs = result.scalars().all()
        
        cv_responses = [CVResponse.model_validate(cv) for cv in cvs]
        
        return CVListResponse(
            cvs=cv_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
    # CV Sections Management
    
    async def create_cv_section(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int, 
        section_data: CVSectionCreate
    ) -> Optional[CVSectionResponse]:
        """
        Create a new section in CV.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID
            section_data: Section creation data
            
        Returns:
            Created section response
        """
        # Check CV ownership
        cv_exists = await self._check_cv_ownership(db, cv_id, user_id)
        if not cv_exists:
            return None
        
        db_section = CVSection(
            cv_id=cv_id,
            **section_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_section)
        await db.commit()
        await db.refresh(db_section)
        
        return CVSectionResponse.model_validate(db_section)
    
    async def update_cv_section(
        self, 
        db: AsyncSession, 
        section_id: int, 
        user_id: int, 
        section_data: CVSectionUpdate
    ) -> Optional[CVSectionResponse]:
        """
        Update CV section.
        
        Args:
            db: Database session
            section_id: Section ID
            user_id: User ID
            section_data: Updated section data
            
        Returns:
            Updated section response
        """
        # Get section with CV ownership check
        result = await db.execute(
            select(CVSection)
            .join(CV)
            .where(
                and_(
                    CVSection.id == section_id,
                    CV.user_id == user_id
                )
            )
        )
        section = result.scalar_one_or_none()
        
        if not section:
            return None
        
        # Update fields
        update_data = section_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(section, field, value)
            
            section.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(section)
        
        return CVSectionResponse.model_validate(section)
    
    # CV Education Management
    
    async def add_education(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int, 
        education_data: CVEducationCreate
    ) -> Optional[CVEducationResponse]:
        """
        Add education entry to CV.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID
            education_data: Education data
            
        Returns:
            Created education response
        """
        # Check CV ownership
        if not await self._check_cv_ownership(db, cv_id, user_id):
            return None
        
        db_education = Education(
            cv_id=cv_id,
            **education_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_education)
        await db.commit()
        await db.refresh(db_education)
        
        return CVEducationResponse.model_validate(db_education)
    
    async def update_education(
        self, 
        db: AsyncSession, 
        education_id: int, 
        user_id: int, 
        education_data: CVEducationUpdate
    ) -> Optional[CVEducationResponse]:
        """
        Update education entry.
        
        Args:
            db: Database session
            education_id: Education ID
            user_id: User ID
            education_data: Updated education data
            
        Returns:
            Updated education response
        """
        result = await db.execute(
            select(Education)
            .join(CV)
            .where(
                and_(
                    Education.id == education_id,
                    CV.user_id == user_id
                )
            )
        )
        education = result.scalar_one_or_none()
        
        if not education:
            return None
        
        # Update fields
        update_data = education_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(education, field, value)
            
            education.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(education)
        
        return CVEducationResponse.model_validate(education)
    
    # CV Experience Management
    
    async def add_experience(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int, 
        experience_data: CVExperienceCreate
    ) -> Optional[CVExperienceResponse]:
        """
        Add work experience entry to CV.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID
            experience_data: Experience data
            
        Returns:
            Created experience response
        """
        # Check CV ownership
        if not await self._check_cv_ownership(db, cv_id, user_id):
            return None
        
        db_experience = WorkExperience(
            cv_id=cv_id,
            **experience_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_experience)
        await db.commit()
        await db.refresh(db_experience)
        
        return CVExperienceResponse.model_validate(db_experience)
    
    async def update_experience(
        self, 
        db: AsyncSession, 
        experience_id: int, 
        user_id: int, 
        experience_data: CVExperienceUpdate
    ) -> Optional[CVExperienceResponse]:
        """
        Update experience entry.
        
        Args:
            db: Database session
            experience_id: Experience ID
            user_id: User ID
            experience_data: Updated experience data
            
        Returns:
            Updated experience response
        """
        result = await db.execute(
            select(WorkExperience)
            .join(CV)
            .where(
                and_(
                    WorkExperience.id == experience_id,
                    CV.user_id == user_id
                )
            )
        )
        experience = result.scalar_one_or_none()
        
        if not experience:
            return None
        
        # Update fields
        update_data = experience_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(experience, field, value)
            
            experience.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(experience)
        
        return CVExperienceResponse.model_validate(experience)
    
    # CV Skills Management
    
    async def add_skill(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int, 
        skill_data: CVSkillCreate
    ) -> Optional[CVSkillResponse]:
        """
        Add skill to CV.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID
            skill_data: Skill data
            
        Returns:
            Created skill response
        """
        # Check CV ownership
        if not await self._check_cv_ownership(db, cv_id, user_id):
            return None
        
        db_skill = CVSkill(
            cv_id=cv_id,
            **skill_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_skill)
        await db.commit()
        await db.refresh(db_skill)
        
        return CVSkillResponse.model_validate(db_skill)
    
    # CV Export functionality
    
    async def export_cv(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int, 
        export_format: str = "pdf",
        template_id: Optional[int] = None
    ) -> Optional[CVExportResponse]:
        """
        Export CV to specified format.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID
            export_format: Export format (pdf, docx, html)
            template_id: Optional template ID
            
        Returns:
            CV export response with download URL
        """
        # Check CV ownership
        if not await self._check_cv_ownership(db, cv_id, user_id):
            return None
        
        # Get CV with all sections
        cv = await self.get_cv_by_id(db, cv_id, user_id)
        if not cv:
            return None
        
        # Create export record
        db_export = CVExport(
            cv_id=cv_id,
            user_id=user_id,
            export_format=export_format,
            template_id=template_id,
            status="processing",
            created_at=datetime.utcnow()
        )
        
        db.add(db_export)
        await db.commit()
        await db.refresh(db_export)
        
        # TODO: Implement actual export generation
        # This would integrate with document generation service
        # For now, mark as completed with placeholder URL
        db_export.status = "completed"
        db_export.file_url = f"/exports/cv_{cv_id}_{db_export.id}.{export_format}"
        db_export.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(db_export)
        
        return CVExportResponse.model_validate(db_export)
    
    async def get_cv_templates(
        self, 
        db: AsyncSession
    ) -> List[CVTemplateResponse]:
        """
        Get available CV templates.
        
        Args:
            db: Database session
            
        Returns:
            List of CV templates
        """
        result = await db.execute(
            select(CVTemplate)
            .where(CVTemplate.is_active == True)
            .order_by(CVTemplate.name)
        )
        templates = result.scalars().all()
        
        return [CVTemplateResponse.model_validate(template) for template in templates]
    
    async def get_cv_analytics(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int
    ) -> Optional[CVAnalyticsResponse]:
        """
        Get CV analytics and statistics.
        
        Args:
            db: Database session
            cv_id: CV ID
            user_id: User ID
            
        Returns:
            CV analytics data
        """
        # Check CV ownership
        if not await self._check_cv_ownership(db, cv_id, user_id):
            return None
        
        # Get CV with all related data
        result = await db.execute(
            select(CV)
            .options(
                selectinload(CV.sections),
                selectinload(CV.education),
                selectinload(CV.experience),
                selectinload(CV.skills),
                selectinload(CV.projects)
            )
            .where(CV.id == cv_id)
        )
        cv = result.scalar_one_or_none()
        
        if not cv:
            return None
        
        # Calculate completion percentage
        total_sections = 8  # Expected sections: contact, summary, education, experience, skills, projects, achievements, references
        completed_sections = 0
        
        # Basic info completion
        if cv.title and cv.summary:
            completed_sections += 2
        
        # Section-based completion
        if cv.education:
            completed_sections += 1
        if cv.experience:
            completed_sections += 1
        if cv.skills:
            completed_sections += 1
        if cv.projects:
            completed_sections += 1
        if cv.sections:
            completed_sections += min(len(cv.sections), 2)  # Additional custom sections
        
        completion_percentage = (completed_sections / total_sections) * 100
        
        # Count exports
        export_count_result = await db.execute(
            select(func.count(CVExport.id)).where(CVExport.cv_id == cv_id)
        )
        export_count = export_count_result.scalar()
        
        return CVAnalyticsResponse(
            cv_id=cv_id,
            completion_percentage=completion_percentage,
            total_sections=len(cv.sections) if cv.sections else 0,
            education_count=len(cv.education) if cv.education else 0,
            experience_count=len(cv.experience) if cv.experience else 0,
            skills_count=len(cv.skills) if cv.skills else 0,
            projects_count=len(cv.projects) if cv.projects else 0,
            export_count=export_count,
            created_at=cv.created_at,
            last_updated=cv.updated_at
        )
    
    # Helper methods
    
    async def _check_cv_ownership(
        self, 
        db: AsyncSession, 
        cv_id: int, 
        user_id: int
    ) -> bool:
        """Check if user owns the CV."""
        result = await db.execute(
            select(CV).where(
                and_(
                    CV.id == cv_id,
                    CV.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none() is not None


# Global CV service instance
cv_service = CVService()