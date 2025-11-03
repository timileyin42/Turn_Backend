"""
API endpoints for AI PM Teacher - Learning modules and progress tracking.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.database.user_models import User
from app.database.platform_models import (
    LearningModule, UserModuleProgress, LearningPath
)
from app.schemas.platform_schemas import (
    LearningModuleResponse, UserProgressResponse, 
    LearningPathProgress, StartModuleRequest
)
from app.services.education_content_service import education_content_service
from app.core.rate_limiter import limiter, RateLimitTiers


router = APIRouter(prefix="/api/v1/learning", tags=["AI PM Teacher"])


@router.get("/paths", response_model=List[str])
async def get_learning_paths():
    """Get all available learning paths."""
    return [path.value for path in LearningPath]


@router.get("/external-courses", response_model=List[dict])
@limiter.limit(RateLimitTiers.EXTERNAL_COURSES)
async def get_external_courses(request: Request):
    """Get real project management courses from external education providers."""
    try:
        # Fetch real course data from multiple providers
        raw_content = await education_content_service.fetch_all_pm_content()
        
        # Normalize the data into a standard format
        normalized_courses = education_content_service.normalize_course_data(raw_content)
        
        # Filter for project management relevant courses
        pm_courses = [
            course for course in normalized_courses 
            if any(keyword in course['title'].lower() or keyword in course['description'].lower() 
                  for keyword in ['project management', 'agile', 'scrum', 'project manager', 'pm'])
        ]
        
        # Sort by rating and enrollment
        pm_courses.sort(key=lambda x: (x['rating'], x['enrollment_count']), reverse=True)
        
        return pm_courses[:50]  # Return top 50 courses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching external courses: {str(e)}"
        )


@router.get("/providers", response_model=dict)
async def get_course_providers():
    """Get information about available course providers."""
    return {
        "providers": [
            {
                "name": "Coursera",
                "description": "Professional courses from top universities and companies",
                "website": settings.coursera_website_url,
                "specialties": ["University courses", "Professional certificates", "Degree programs"],
                "cost": "Free audit, paid certificates"
            },
            {
                "name": "edX", 
                "description": "High-quality courses from leading institutions",
                "website": settings.edx_website_url,
                "specialties": ["University courses", "MicroMasters", "Professional education"],
                "cost": "Free audit, paid verified certificates"
            },
            {
                "name": "FutureLearn",
                "description": "Social learning platform with courses from top universities",
                "website": settings.futurelearn_website_url,
                "specialties": ["Short courses", "Microcredentials", "Degree programs"],
                "cost": "Free limited access, paid unlimited access"
            },
            {
                "name": "MIT OpenCourseWare",
                "description": "Free MIT course materials online",
                "website": settings.mit_ocw_website_url,
                "specialties": ["Technical courses", "Engineering", "Management"],
                "cost": "Completely free"
            },
            {
                "name": "YouTube Education",
                "description": "Educational video content from experts",
                "website": settings.youtube_education_url,
                "specialties": ["Video tutorials", "Practical demonstrations", "Expert insights"],
                "cost": "Free with ads"
            },
            {
                "name": "Khan Academy",
                "description": "Free world-class education for anyone, anywhere",
                "website": settings.khan_academy_website_url,
                "specialties": ["Business fundamentals", "Entrepreneurship", "Economics"],
                "cost": "Completely free"
            }
        ],
        "total_providers": 6,
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/courses/search", response_model=List[dict])
async def search_courses(
    query: str,
    provider: Optional[str] = None,
    difficulty: Optional[int] = None,
    free_only: bool = False,
    limit: int = 20
):
    """Search for courses across all providers."""
    try:
        # Fetch all available courses
        raw_content = await education_content_service.fetch_all_pm_content()
        normalized_courses = education_content_service.normalize_course_data(raw_content)
        
        # Apply filters
        filtered_courses = []
        query_lower = query.lower()
        
        for course in normalized_courses:
            # Text search
            if (query_lower in course['title'].lower() or 
                query_lower in course['description'].lower() or
                any(query_lower in skill.lower() for skill in course['skills'])):
                
                # Provider filter
                if provider and provider.lower() != course['provider'].lower():
                    continue
                
                # Difficulty filter
                if difficulty and course['difficulty_level'] != difficulty:
                    continue
                
                # Free only filter
                if free_only and not course['is_free']:
                    continue
                
                filtered_courses.append(course)
        
        # Sort by relevance (title match first, then description)
        def relevance_score(course):
            score = 0
            if query_lower in course['title'].lower():
                score += 10
            if query_lower in course['description'].lower():
                score += 5
            score += course['rating']
            return score
        
        filtered_courses.sort(key=relevance_score, reverse=True)
        
        return filtered_courses[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching courses: {str(e)}"
        )


@router.get("/youtube-courses", response_model=List[dict])
@limiter.limit(RateLimitTiers.EXTERNAL_COURSES)
async def get_youtube_educational_content(
    request: Request,
    topic: Optional[str] = Query(None, description="Specific PM topic to search for"),
    duration: Optional[str] = Query("medium", description="Video duration: short, medium, long"),
    limit: int = Query(20, le=50, description="Number of videos to return")
):
    """Get high-quality YouTube educational content for project management."""
    try:
        # Fetch YouTube content
        raw_content = await education_content_service.fetch_all_pm_content()
        youtube_videos = raw_content.get('youtube', [])
        
        if not youtube_videos:
            return {
                "message": "YouTube API key not configured or no content available",
                "setup_instructions": {
                    "step_1": "Get free YouTube Data API key from Google Cloud Console",
                    "step_2": "Enable YouTube Data API v3 in your project", 
                    "step_3": "Add YOUTUBE_API_KEY to your environment variables",
                    "daily_quota": "10,000 units (approximately 100 searches per day)",
                    "cost": "Free up to quota limit"
                }
            }
        
        # Filter by topic if specified
        if topic:
            topic_lower = topic.lower()
            youtube_videos = [
                video for video in youtube_videos
                if topic_lower in video.get('snippet', {}).get('title', '').lower() or
                   topic_lower in video.get('snippet', {}).get('description', '').lower()
            ]
        
        # Normalize and enhance video data
        normalized_videos = []
        for video in youtube_videos[:limit]:
            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            video_id = video.get('id', {}).get('videoId', '')
            
            # Calculate educational score
            educational_score = 0
            title = snippet.get('title', '').lower()
            channel_title = snippet.get('channelTitle', '').lower()
            
            # Score based on educational indicators
            edu_keywords = ['course', 'tutorial', 'training', 'certification', 'masterclass', 'guide', 'fundamentals']
            for keyword in edu_keywords:
                if keyword in title:
                    educational_score += 10
            
            # Bonus for educational channels
            if any(indicator in channel_title for indicator in ['university', 'academy', 'institute', 'education', 'pmi']):
                educational_score += 20
            
            # Bonus for engagement
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            if view_count > 10000:
                educational_score += 5
            if like_count > view_count * 0.01:  # 1% like ratio
                educational_score += 5
            
            normalized_videos.append({
                'id': f"youtube_{video_id}",
                'title': snippet.get('title', ''),
                'description': snippet.get('description', '')[:500] + '...' if len(snippet.get('description', '')) > 500 else snippet.get('description', ''),
                'instructor': snippet.get('channelTitle', ''),
                'duration': 'Medium (4-20 minutes)',  # YouTube API doesn't give exact duration in search
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'embed_url': f"https://www.youtube.com/embed/{video_id}",
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'published_date': snippet.get('publishedAt', ''),
                'view_count': view_count,
                'like_count': like_count,
                'educational_score': educational_score,
                'topics': [
                    tag for tag in snippet.get('tags', [])
                    if any(pm_keyword in tag.lower() for pm_keyword in ['project', 'management', 'agile', 'scrum', 'pmp'])
                ][:5],
                'provider': 'YouTube Education',
                'cost': 'Free',
                'language': snippet.get('defaultLanguage', 'en'),
                'quality_indicators': [
                    f"{view_count:,} views" if view_count > 1000 else None,
                    f"{like_count:,} likes" if like_count > 100 else None,
                    "Educational channel" if 'university' in channel_title or 'academy' in channel_title else None,
                    "Professional content" if any(keyword in title for keyword in ['certification', 'professional', 'masterclass']) else None
                ]
            })
        
        # Sort by educational score and engagement
        normalized_videos.sort(key=lambda x: (x['educational_score'], x['view_count']), reverse=True)
        
        return {
            "videos": normalized_videos,
            "total_found": len(normalized_videos),
            "search_criteria": {
                "topic": topic or "All project management topics",
                "duration_filter": duration,
                "quality_filter": "Educational content prioritized"
            },
            "usage_info": {
                "api_quota_used": f"~{len(youtube_videos)} units of daily 10,000 quota",
                "recommendation": "Save high-quality videos to reduce API calls"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching YouTube educational content: {str(e)}"
        )


@router.get("/modules", response_model=List[LearningModuleResponse])
async def get_learning_modules(
    path: Optional[LearningPath] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get learning modules, optionally filtered by learning path."""
    query = select(LearningModule).where(LearningModule.is_active == True)
    
    if path:
        query = query.where(LearningModule.learning_path == path)
    
    query = query.order_by(LearningModule.order_index)
    
    result = await db.execute(query)
    modules = result.scalars().all()
    
    return [LearningModuleResponse.model_validate(module) for module in modules]


@router.get("/modules/{module_id}", response_model=LearningModuleResponse)
async def get_learning_module(
    module_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific learning module by ID."""
    result = await db.execute(
        select(LearningModule)
        .where(and_(
            LearningModule.id == module_id,
            LearningModule.is_active == True
        ))
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning module not found"
        )
    
    return LearningModuleResponse.model_validate(module)


@router.post("/modules/{module_id}/start", response_model=UserProgressResponse)
async def start_learning_module(
    module_id: int,
    request: StartModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a learning module for the current user."""
    # Check if module exists
    result = await db.execute(
        select(LearningModule)
        .where(and_(
            LearningModule.id == module_id,
            LearningModule.is_active == True
        ))
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning module not found"
        )
    
    # Check if user already has progress for this module
    result = await db.execute(
        select(UserModuleProgress)
        .where(and_(
            UserModuleProgress.user_id == current_user.id,
            UserModuleProgress.module_id == module_id
        ))
    )
    existing_progress = result.scalar_one_or_none()
    
    if existing_progress:
        # Update existing progress
        existing_progress.last_accessed_at = request.timestamp or datetime.utcnow()
        progress = existing_progress
    else:
        # Create new progress record
        progress = UserModuleProgress(
            user_id=current_user.id,
            module_id=module_id,
            started_at=request.timestamp or datetime.utcnow(),
            last_accessed_at=request.timestamp or datetime.utcnow()
        )
        db.add(progress)
    
    await db.commit()
    await db.refresh(progress)
    
    return UserProgressResponse.model_validate(progress)


@router.put("/modules/{module_id}/progress", response_model=UserProgressResponse)
async def update_module_progress(
    module_id: int,
    progress_percentage: int,
    time_spent_minutes: Optional[int] = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user progress for a learning module."""
    if not 0 <= progress_percentage <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress percentage must be between 0 and 100"
        )
    
    # Get existing progress
    result = await db.execute(
        select(UserModuleProgress)
        .where(and_(
            UserModuleProgress.user_id == current_user.id,
            UserModuleProgress.module_id == module_id
        ))
    )
    progress = result.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module progress not found. Start the module first."
        )
    
    # Update progress
    progress.progress_percentage = progress_percentage
    progress.time_spent_minutes += time_spent_minutes or 0
    progress.last_accessed_at = datetime.utcnow()
    
    # Mark as completed if 100%
    if progress_percentage == 100 and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(progress)
    
    return UserProgressResponse.model_validate(progress)


@router.get("/progress", response_model=List[LearningPathProgress])
async def get_user_learning_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's learning progress across all paths."""
    # Get all user progress with module details
    result = await db.execute(
        select(UserModuleProgress)
        .options(selectinload(UserModuleProgress.module))
        .where(UserModuleProgress.user_id == current_user.id)
    )
    user_progress = result.scalars().all()
    
    # Group by learning path
    path_progress = {}
    for progress in user_progress:
        path = progress.module.learning_path
        if path not in path_progress:
            path_progress[path] = {
                "learning_path": path,
                "total_modules": 0,
                "completed_modules": 0,
                "total_time_minutes": 0,
                "progress_percentage": 0,
                "modules": []
            }
        
        path_progress[path]["modules"].append(progress)
        path_progress[path]["total_time_minutes"] += progress.time_spent_minutes
        if progress.is_completed:
            path_progress[path]["completed_modules"] += 1
    
    # Get total modules per path
    for path in LearningPath:
        if path in path_progress:
            result = await db.execute(
                select(LearningModule)
                .where(and_(
                    LearningModule.learning_path == path,
                    LearningModule.is_active == True
                ))
            )
            total_modules = len(result.scalars().all())
            path_progress[path]["total_modules"] = total_modules
            
            if total_modules > 0:
                path_progress[path]["progress_percentage"] = (
                    path_progress[path]["completed_modules"] / total_modules * 100
                )
    
    return [LearningPathProgress(**data) for data in path_progress.values()]


@router.get("/progress/{module_id}", response_model=UserProgressResponse)
async def get_module_progress(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's progress for a specific module."""
    result = await db.execute(
        select(UserModuleProgress)
        .where(and_(
            UserModuleProgress.user_id == current_user.id,
            UserModuleProgress.module_id == module_id
        ))
    )
    progress = result.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module progress not found"
        )
    
    return UserProgressResponse.model_validate(progress)


@router.post("/modules/{module_id}/complete", response_model=UserProgressResponse)
async def complete_learning_module(
    module_id: int,
    quiz_score: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a learning module as completed."""
    # Get existing progress
    result = await db.execute(
        select(UserModuleProgress)
        .where(and_(
            UserModuleProgress.user_id == current_user.id,
            UserModuleProgress.module_id == module_id
        ))
    )
    progress = result.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module progress not found. Start the module first."
        )
    
    # Mark as completed
    progress.is_completed = True
    progress.completed_at = datetime.utcnow()
    progress.progress_percentage = 100
    progress.last_accessed_at = datetime.utcnow()
    
    if quiz_score is not None:
        if not 0 <= quiz_score <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz score must be between 0 and 100"
            )
        progress.quiz_score = quiz_score
    
    await db.commit()
    await db.refresh(progress)
    
    return UserProgressResponse.model_validate(progress)


@router.get("/stats", response_model=dict)
async def get_learning_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's learning statistics."""
    # Get all user progress
    result = await db.execute(
        select(UserModuleProgress)
        .where(UserModuleProgress.user_id == current_user.id)
    )
    all_progress = result.scalars().all()
    
    # Calculate stats
    total_modules_started = len(all_progress)
    completed_modules = len([p for p in all_progress if p.is_completed])
    total_time_minutes = sum(p.time_spent_minutes for p in all_progress)
    
    # Get total available modules
    result = await db.execute(
        select(LearningModule)
        .where(LearningModule.is_active == True)
    )
    total_available_modules = len(result.scalars().all())
    
    # Calculate completion rate
    completion_rate = (completed_modules / total_modules_started * 100) if total_modules_started > 0 else 0
    
    # Get current streak (mock for now)
    current_streak = 5  # This would be calculated based on daily activity
    
    return {
        "total_modules_started": total_modules_started,
        "completed_modules": completed_modules,
        "total_available_modules": total_available_modules,
        "completion_rate": round(completion_rate, 1),
        "total_time_hours": round(total_time_minutes / 60, 1),
        "average_quiz_score": round(
            sum(p.quiz_score for p in all_progress if p.quiz_score) / 
            len([p for p in all_progress if p.quiz_score])
        ) if any(p.quiz_score for p in all_progress) else None,
        "current_streak_days": current_streak,
        "favorite_learning_path": "agile_scrum"  # Mock data
    }