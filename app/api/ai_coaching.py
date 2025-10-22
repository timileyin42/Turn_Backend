"""
AI-powered learning and coaching endpoints for TURN Platform.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.ai_service import ai_service, AICoachingType, LearningLevel
from app.core.dependencies import get_current_user
from app.database.user_models import User
from app.core.rate_limiter import limiter, RateLimitTiers

router = APIRouter(prefix="/ai", tags=["AI PM Teacher"])


# Request/Response Models
class LearningPathRequest(BaseModel):
    user_level: LearningLevel
    career_goals: List[str]
    current_skills: List[str]
    time_commitment: str = "2-3 hours/week"


class CoachingSessionRequest(BaseModel):
    coaching_type: AICoachingType
    question: str
    context: Optional[Dict[str, Any]] = None


class ScenarioAnalysisRequest(BaseModel):
    scenario_description: str
    decisions_made: List[Dict[str, str]]
    user_level: LearningLevel


class InterviewPrepRequest(BaseModel):
    job_level: str
    company_type: str
    focus_areas: List[str]


class CareerGuidanceRequest(BaseModel):
    current_situation: Dict[str, Any]
    career_goals: Dict[str, Any]


@router.post("/learning-path")
@limiter.limit(RateLimitTiers.AI_COACHING)
async def generate_learning_path(
    http_request: Request,
    request: LearningPathRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a personalized 12-week learning path for the user.
    """
    try:
        learning_path = await ai_service.get_personalized_learning_path(
            user_level=request.user_level,
            career_goals=request.career_goals,
            current_skills=request.current_skills,
            time_commitment=request.time_commitment
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "learning_path": learning_path,
            "message": "Personalized learning path generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning path: {str(e)}"
        )


@router.post("/coaching-session")
@limiter.limit(RateLimitTiers.AI_COACHING)
async def ai_coaching_session(
    http_request: Request,
    request: CoachingSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered coaching and mentorship.
    """
    try:
        # Add user context if not provided
        if not request.context:
            request.context = {
                "user_id": current_user.id,
                "email": current_user.email,
                "experience_level": getattr(current_user, 'experience_level', 'Not specified'),
                "current_role": getattr(current_user, 'current_role', 'Not specified')
            }
        
        coaching_response = await ai_service.get_ai_coaching_session(
            coaching_type=request.coaching_type,
            user_question=request.question,
            user_context=request.context
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "coaching_session": coaching_response,
            "message": "AI coaching session completed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coaching session failed: {str(e)}"
        )


@router.post("/analyze-scenario")
async def analyze_project_scenario(
    request: ScenarioAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze project management scenarios and provide AI feedback.
    """
    try:
        analysis = await ai_service.analyze_project_scenario(
            scenario_description=request.scenario_description,
            decisions_made=request.decisions_made,
            user_level=request.user_level
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "scenario_analysis": analysis,
            "message": "Project scenario analyzed successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario analysis failed: {str(e)}"
        )


@router.post("/interview-prep")
async def generate_interview_questions(
    request: InterviewPrepRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate personalized PM interview questions for practice.
    """
    try:
        questions = await ai_service.generate_interview_questions(
            job_level=request.job_level,
            company_type=request.company_type,
            focus_areas=request.focus_areas
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "interview_prep": questions,
            "message": "Interview questions generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview prep generation failed: {str(e)}"
        )


@router.post("/career-guidance")
async def get_career_guidance(
    request: CareerGuidanceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized career guidance and development advice.
    """
    try:
        guidance = await ai_service.provide_career_guidance(
            current_situation=request.current_situation,
            career_goals=request.career_goals
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "career_guidance": guidance,
            "message": "Career guidance generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Career guidance failed: {str(e)}"
        )


@router.get("/coaching-types")
async def get_available_coaching_types():
    """
    Get list of available AI coaching types.
    """
    return {
        "success": True,
        "coaching_types": [
            {
                "type": coaching_type.value,
                "name": coaching_type.value.replace("_", " ").title(),
                "description": f"AI coaching for {coaching_type.value.replace('_', ' ')}"
            }
            for coaching_type in AICoachingType
        ]
    }


@router.get("/learning-levels")
async def get_learning_levels():
    """
    Get available learning levels.
    """
    return {
        "success": True,
        "learning_levels": [
            {
                "level": level.value,
                "name": level.value.title(),
                "description": f"For {level.value} level product managers"
            }
            for level in LearningLevel
        ]
    }


@router.get("/health")
async def ai_service_health():
    """
    Check AI service health and OpenAI API connectivity.
    """
    try:
        # Simple test to verify OpenAI API is working
        test_response = await ai_service._get_ai_response("Test message", max_tokens=10)
        
        return {
            "success": True,
            "ai_service": "healthy",
            "openai_api": "connected",
            "message": "AI service is operational"
        }
        
    except Exception as e:
        return {
            "success": False,
            "ai_service": "error",
            "openai_api": "disconnected",
            "error": str(e),
            "message": "AI service is experiencing issues"
        }


# Quick AI coaching endpoint for simple questions
@router.post("/quick-ask")
async def quick_ai_question(
    question: str,
    coaching_type: AICoachingType = AICoachingType.PM_FUNDAMENTALS,
    current_user: User = Depends(get_current_user)
):
    """
    Quick AI question endpoint for simple PM questions.
    """
    try:
        response = await ai_service.get_ai_coaching_session(
            coaching_type=coaching_type,
            user_question=question,
            user_context={"user_id": current_user.id}
        )
        
        return {
            "success": True,
            "question": question,
            "ai_response": response.get("response", ""),
            "coaching_type": coaching_type.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick AI question failed: {str(e)}"
        )