"""
CV/Resume building routes for CV management and export functionality.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.services.cv_service import cv_service
from app.database.user_models import User
from app.schemas.cv_schemas import (
    CVCreate, CVUpdate, CVResponse, CVListResponse,
    CVSectionCreate, CVSectionUpdate, CVSectionResponse,
    CVTemplateResponse, CVExportResponse,
    CVEducationCreate, CVEducationUpdate, CVEducationResponse,
    CVExperienceCreate, CVExperienceUpdate, CVExperienceResponse,
    CVSkillCreate, CVSkillUpdate, CVSkillResponse,
    CVProjectCreate, CVProjectUpdate, CVProjectResponse,
    CVAnalyticsResponse
)

router = APIRouter(prefix="/cv", tags=["CV Management"])


# CV CRUD Routes

@router.post(
    "/",
    response_model=CVResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new CV",
    description="Create a new CV/resume for the authenticated user"
)
async def create_cv(
    cv_data: CVCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new CV."""
    try:
        return await cv_service.create_cv(db, current_user.id, cv_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create CV"
        )


@router.get(
    "/",
    response_model=CVListResponse,
    summary="Get user's CVs",
    description="Get all CVs owned by the authenticated user"
)
async def get_my_cvs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's CVs."""
    try:
        return await cv_service.get_user_cvs(db, current_user.id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CVs"
        )


@router.get(
    "/templates",
    response_model=List[CVTemplateResponse],
    summary="Get CV templates",
    description="Get available CV templates"
)
async def get_cv_templates(
    db: AsyncSession = Depends(get_db)
):
    """Get available CV templates."""
    try:
        return await cv_service.get_cv_templates(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CV templates"
        )


@router.get(
    "/{cv_id}",
    response_model=CVResponse,
    summary="Get CV by ID",
    description="Get CV details by ID (owner only)"
)
async def get_cv(
    cv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get CV by ID."""
    try:
        cv = await cv_service.get_cv_by_id(db, cv_id, current_user.id)
        if not cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return cv
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CV"
        )


@router.put(
    "/{cv_id}",
    response_model=CVResponse,
    summary="Update CV",
    description="Update CV information (owner only)"
)
async def update_cv(
    cv_id: int,
    cv_data: CVUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update CV."""
    try:
        updated_cv = await cv_service.update_cv(db, cv_id, current_user.id, cv_data)
        if not updated_cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return updated_cv
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update CV"
        )


@router.delete(
    "/{cv_id}",
    summary="Delete CV",
    description="Delete CV (owner only)"
)
async def delete_cv(
    cv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete CV."""
    try:
        success = await cv_service.delete_cv(db, cv_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return {"message": "CV deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete CV"
        )


# CV Sections Management

@router.post(
    "/{cv_id}/sections",
    response_model=CVSectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create CV section",
    description="Create a new section in the CV"
)
async def create_cv_section(
    cv_id: int,
    section_data: CVSectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create CV section."""
    try:
        section = await cv_service.create_cv_section(db, cv_id, current_user.id, section_data)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return section
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create CV section"
        )


@router.put(
    "/sections/{section_id}",
    response_model=CVSectionResponse,
    summary="Update CV section",
    description="Update CV section information"
)
async def update_cv_section(
    section_id: int,
    section_data: CVSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update CV section."""
    try:
        updated_section = await cv_service.update_cv_section(db, section_id, current_user.id, section_data)
        if not updated_section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found or access denied"
            )
        return updated_section
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update CV section"
        )


# Education Management

@router.post(
    "/{cv_id}/education",
    response_model=CVEducationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add education entry",
    description="Add education entry to CV"
)
async def add_education(
    cv_id: int,
    education_data: CVEducationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add education entry to CV."""
    try:
        education = await cv_service.add_education(db, cv_id, current_user.id, education_data)
        if not education:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return education
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add education entry"
        )


@router.put(
    "/education/{education_id}",
    response_model=CVEducationResponse,
    summary="Update education entry",
    description="Update education entry information"
)
async def update_education(
    education_id: int,
    education_data: CVEducationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update education entry."""
    try:
        updated_education = await cv_service.update_education(db, education_id, current_user.id, education_data)
        if not updated_education:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Education entry not found or access denied"
            )
        return updated_education
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update education entry"
        )


# Experience Management

@router.post(
    "/{cv_id}/experience",
    response_model=CVExperienceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add work experience",
    description="Add work experience entry to CV"
)
async def add_experience(
    cv_id: int,
    experience_data: CVExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add work experience to CV."""
    try:
        experience = await cv_service.add_experience(db, cv_id, current_user.id, experience_data)
        if not experience:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return experience
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add work experience"
        )


@router.put(
    "/experience/{experience_id}",
    response_model=CVExperienceResponse,
    summary="Update work experience",
    description="Update work experience entry"
)
async def update_experience(
    experience_id: int,
    experience_data: CVExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update work experience."""
    try:
        updated_experience = await cv_service.update_experience(db, experience_id, current_user.id, experience_data)
        if not updated_experience:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experience entry not found or access denied"
            )
        return updated_experience
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update work experience"
        )


# Skills Management

@router.post(
    "/{cv_id}/skills",
    response_model=CVSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add skill",
    description="Add skill to CV"
)
async def add_skill(
    cv_id: int,
    skill_data: CVSkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add skill to CV."""
    try:
        skill = await cv_service.add_skill(db, cv_id, current_user.id, skill_data)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return skill
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add skill"
        )


# CV Export

@router.post(
    "/{cv_id}/export",
    response_model=CVExportResponse,
    summary="Export CV",
    description="Export CV to specified format (PDF, DOCX, HTML)"
)
async def export_cv(
    cv_id: int,
    export_format: str = Query("pdf", regex="^(pdf|docx|html)$", description="Export format"),
    template_id: Optional[int] = Query(None, description="Template ID to use for export"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export CV to specified format."""
    try:
        export = await cv_service.export_cv(db, cv_id, current_user.id, export_format, template_id)
        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return export
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export CV"
        )

# Analytics

@router.get(
    "/{cv_id}/analytics",
    response_model=CVAnalyticsResponse,
    summary="Get CV analytics",
    description="Get CV analytics and statistics"
)
async def get_cv_analytics(
    cv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get CV analytics."""
    try:
        analytics = await cv_service.get_cv_analytics(db, cv_id, current_user.id)
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found or access denied"
            )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CV analytics"
        )