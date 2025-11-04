"""
Project management routes for CRUD operations and AI coaching.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.services.project_service import project_service
from app.database.user_models import User
from app.schemas.project_schemas import (
    ProjectSimulationCreate, ProjectSimulationUpdate, ProjectSimulationResponse,
    ProjectTaskCreate, ProjectTaskUpdate, ProjectTaskResponse,
    AiCoachingSessionCreate, AiCoachingSessionResponse,
    ProjectCreate, ProjectResponse, ProjectListResponse, ProjectSearchRequest,
    ProjectUpdate, ProjectCollaboratorResponse, ProjectCollaboratorCreate,
    AICoachingSessionCreate, AICoachingSessionResponse, ProjectAnalyticsResponse
)

router = APIRouter(prefix="/projects", tags=["Project Management"])


# Project CRUD Routes

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new project",
    description="Create a new project for the authenticated user"
)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project.
    
    Example request body:
    {
        "title": "E-Commerce Platform Redesign",
        "description": "Modernize the UI/UX of our e-commerce platform",
        "status": "planning",
        "priority": "high",
        "category": "web_development",
        "start_date": "2025-11-10",
        "end_date": "2025-12-31",
        "budget": 50000
    }
    """
    try:
        return await project_service.create_project(db, current_user.id, project_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="Get user's projects",
    description="Get all projects owned by or accessible to the authenticated user"
)
async def get_my_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's projects.
    
    Example query parameters:
    ?skip=0&limit=20
    """
    try:
        return await project_service.get_user_projects(db, current_user.id, skip, limit)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )


@router.get(
    "/search",
    response_model=ProjectListResponse,
    summary="Search projects",
    description="Search projects with advanced filters"
)
async def search_projects(
    query: Optional[str] = Query(None, description="Search query"),
    project_status: Optional[str] = Query(None, description="Filter by project status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search projects with filters.
    
    Example query parameters:
    ?query=e-commerce&project_status=active&priority=high&category=web_development&limit=10
    """
    try:
        search_params = ProjectSearchRequest(
            query=query,
            status=project_status,
            priority=priority,
            category=category
        )
        return await project_service.search_projects(db, current_user.id, search_params, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search projects"
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Get project details by ID (requires project access)"
)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get project by ID.
    
    Example: GET /api/v1/projects/42
    """
    try:
        project = await project_service.get_project_by_id(db, project_id, current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project information (requires project write access)"
)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update project.
    
    Example request body:
    {
        "title": "E-Commerce Platform Redesign v2",
        "status": "in_progress",
        "priority": "urgent",
        "progress_percentage": 45
    }
    """
    try:
        updated_project = await project_service.update_project(db, project_id, current_user.id, project_data)
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return updated_project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete(
    "/{project_id}",
    summary="Delete project",
    description="Delete project (owner only)"
)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete project.
    
    Example: DELETE /api/v1/projects/42
    """
    try:
        success = await project_service.delete_project(db, project_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


# Task Management Routes

@router.post(
    "/{project_id}/tasks",
    response_model=ProjectTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project task",
    description="Create a new task in the project"
)
async def create_task(
    project_id: int,
    task_data: ProjectTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create project task.
    
    Example request body:
    {
        "title": "Design homepage wireframes",
        "description": "Create low-fidelity wireframes for the new homepage layout",
        "status": "todo",
        "priority": "high",
        "due_date": "2025-11-20",
        "assigned_to_user_id": 5
    }
    """
    try:
        task = await project_service.create_task(db, project_id, current_user.id, task_data)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get(
    "/{project_id}/tasks",
    response_model=List[ProjectTaskResponse],
    summary="Get project tasks",
    description="Get all tasks for the project"
)
async def get_project_tasks(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get project tasks.
    
    Example: GET /api/v1/projects/42/tasks
    """
    try:
        return await project_service.get_project_tasks(db, project_id, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project tasks"
        )


@router.put(
    "/tasks/{task_id}",
    response_model=ProjectTaskResponse,
    summary="Update project task",
    description="Update project task information"
)
async def update_task(
    task_id: int,
    task_data: ProjectTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update project task.
    
    Example request body:
    {
        "status": "in_progress",
        "progress_percentage": 30,
        "notes": "Started working on mobile wireframes"
    }
    """
    try:
        updated_task = await project_service.update_task(db, task_id, current_user.id, task_data)
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied"
            )
        return updated_task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


# Collaboration Routes

@router.post(
    "/{project_id}/collaborators",
    response_model=ProjectCollaboratorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add project collaborator",
    description="Add a collaborator to the project (owner only)"
)
async def add_collaborator(
    project_id: int,
    collaborator_data: ProjectCollaboratorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add project collaborator.
    
    Example request body:
    {
        "user_id": 15,
        "role": "contributor",
        "permissions": ["read", "write"]
    }
    """
    try:
        collaborator = await project_service.add_collaborator(db, project_id, current_user.id, collaborator_data)
        if not collaborator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return collaborator
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add collaborator"
        )


# AI Coaching Routes

@router.post(
    "/{project_id}/ai-coaching",
    response_model=AICoachingSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI coaching session",
    description="Create a new AI coaching session for the project"
)
async def create_ai_coaching_session(
    project_id: int,
    session_data: AICoachingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create AI coaching session.
    
    Example request body:
    {
        "session_type": "project_guidance",
        "topic": "How to structure API endpoints for microservices",
        "user_message": "I need advice on breaking down my monolithic app into microservices"
    }
    """
    try:
        session = await project_service.create_ai_coaching_session(db, project_id, current_user.id, session_data)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI coaching session: {str(e)}"
        )


@router.get(
    "/{project_id}/ai-coaching",
    response_model=List[AICoachingSessionResponse],
    summary="Get AI coaching sessions",
    description="Get AI coaching sessions for the project"
)
async def get_ai_coaching_sessions(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI coaching sessions for project.
    
    Example: GET /api/v1/projects/42/ai-coaching
    """
    try:
        return await project_service.get_project_ai_sessions(db, project_id, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI coaching sessions"
        )


# Analytics Routes

@router.get(
    "/{project_id}/analytics",
    response_model=ProjectAnalyticsResponse,
    summary="Get project analytics",
    description="Get project analytics and statistics"
)
async def get_project_analytics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get project analytics.
    
    Example: GET /api/v1/projects/42/analytics
    """
    try:
        analytics = await project_service.get_project_analytics(db, project_id, current_user.id)
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project analytics"
        )