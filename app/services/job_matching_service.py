"""
Smart Job Matching Service using FREE sentence-transformers for semantic similarity.
Provides intelligent job recommendations based on user skills, experience, and preferences.
"""
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

# Optional ML libraries - as it's not available in Python 3.13 yet
try:
    import numpy as np  # type: ignore
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

#embedding libraries
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from app.database.job_models import JobPosting, JobApplication, SavedJob
from app.database.user_models import User, UserSkill
from app.database.cv_models import CV, CVExperience, CVEducation, CVSkill
from app.schemas.job_schemas import JobMatchResponse, JobRecommendationResponse


class JobMatchingService:
    """Free job matching service using sentence transformers and scikit-learn."""
    
    def __init__(self):
        """Initialize job matching service with free embedding models."""
        self.embedding_model = None
        self.tfidf_vectorizer = None
        
        # Initialize TF-IDF if sklearn available
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        
        # Initialize embedding model if available
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use free, lightweight models
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 22MB model
                print("Sentence Transformers loaded successfully")
            except Exception as e:
                print(f"WARNING: Could not load sentence transformers: {e}")
                self.embedding_model = None
        else:
            print("WARNING: Sentence Transformers not available. Using basic matching.")
    
    async def get_user_profile_text(self, db: AsyncSession, user_id: int) -> str:
        """Generate comprehensive user profile text for matching."""
        profile_parts = []
        
        # Get user basic info
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return ""
        
        # Get user skills
        skills_result = await db.execute(
            select(UserSkill).where(UserSkill.user_id == user_id)
        )
        skills = skills_result.scalars().all()
        if skills:
            skill_names = [skill.skill_name for skill in skills]
            profile_parts.append(f"Skills: {', '.join(skill_names)}")
        
        # Get latest CV data
        cv_result = await db.execute(
            select(CV)
            .where(and_(CV.user_id == user_id, CV.is_default == True))
            .limit(1)
        )
        cv = cv_result.scalar_one_or_none()
        
        if cv:
            if cv.summary:
                profile_parts.append(f"Summary: {cv.summary}")
            
            # Get work experience
            exp_result = await db.execute(
                select(CVExperience).where(CVExperience.cv_id == cv.id)
            )
            experiences = exp_result.scalars().all()
            
            for exp in experiences:
                exp_text = f"Experience: {exp.job_title} at {exp.company_name}"
                if exp.description:
                    exp_text += f" - {exp.description}"
                profile_parts.append(exp_text)
            
            # Get education
            edu_result = await db.execute(
                select(CVEducation).where(CVEducation.cv_id == cv.id)
            )
            education = edu_result.scalars().all()
            
            for edu in education:
                profile_parts.append(f"Education: {edu.degree} in {edu.field_of_study}")
        
        return " ".join(profile_parts)
    
    def get_job_text(self, job: Dict[str, Any]) -> str:
        """Extract relevant text from job posting for matching."""
        job_parts = []
        
        # Job title and company
        if job.get('position'):
            job_parts.append(f"Position: {job['position']}")
        if job.get('company'):
            job_parts.append(f"Company: {job['company']}")
        
        # Job description
        if job.get('description'):
            job_parts.append(f"Description: {job['description']}")
        
        # Required skills/tags
        if job.get('tags'):
            if isinstance(job['tags'], list):
                job_parts.append(f"Skills: {', '.join(job['tags'])}")
            elif isinstance(job['tags'], str):
                job_parts.append(f"Skills: {job['tags']}")
        
        # Location preferences
        if job.get('location'):
            job_parts.append(f"Location: {job['location']}")
        
        return " ".join(job_parts)
    
    async def calculate_job_similarity_embeddings(
        self, 
        user_profile: str, 
        jobs: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Calculate job similarity using sentence transformers (free)."""
        if not self.embedding_model or not user_profile.strip():
            return []
        
        try:
            # Prepare texts
            job_texts = [self.get_job_text(job) for job in jobs]
            all_texts = [user_profile] + job_texts
            
            # Generate embeddings
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, self.embedding_model.encode, all_texts
            )
            
            # Calculate similarities
            user_embedding = embeddings[0].reshape(1, -1)
            job_embeddings = embeddings[1:]
            
            similarities = cosine_similarity(user_embedding, job_embeddings)[0]
            
            # Pair jobs with similarity scores
            job_scores = list(zip(jobs, similarities))
            
            # Sort by similarity (highest first)
            job_scores.sort(key=lambda x: x[1], reverse=True)
            
            return job_scores
            
        except Exception as e:
            print(f"WARNING: Error in embedding similarity: {e}")
            return []
    
    async def calculate_job_similarity_tfidf(
        self, 
        user_profile: str, 
        jobs: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Fallback job similarity using TF-IDF (completely free)."""
        if not user_profile.strip():
            return []
        
        try:
            # Prepare texts
            job_texts = [self.get_job_text(job) for job in jobs]
            all_texts = [user_profile] + job_texts
            
            # Remove empty texts
            valid_texts = [text for text in all_texts if text.strip()]
            if len(valid_texts) < 2:
                return []
            
            # Calculate TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(valid_texts)
            
            # Calculate similarities
            user_vector = tfidf_matrix[0]
            job_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(user_vector, job_vectors)[0]
            
            # Pair jobs with similarity scores
            job_scores = list(zip(jobs, similarities))
            
            # Sort by similarity (highest first)
            job_scores.sort(key=lambda x: x[1], reverse=True)
            
            return job_scores
            
        except Exception as e:
            print(f"WARNING: Error in TF-IDF similarity: {e}")
            return []
    
    async def get_job_recommendations(
        self, 
        db: AsyncSession, 
        user_id: int, 
        jobs: List[Dict[str, Any]], 
        limit: int = 10
    ) -> List[JobRecommendationResponse]:
        """Get personalized job recommendations for user."""
        
        # Get user profile
        user_profile = await self.get_user_profile_text(db, user_id)
        if not user_profile.strip():
            # Return jobs without personalization if no profile
            return [
                JobRecommendationResponse(
                    job=job,
                    similarity_score=0.0,
                    match_reasons=["No user profile available for personalization"]
                )
                for job in jobs[:limit]
            ]
        
        # Calculate similarities using best available method
        if SENTENCE_TRANSFORMERS_AVAILABLE and self.embedding_model:
            job_scores = await self.calculate_job_similarity_embeddings(user_profile, jobs)
            method = "Semantic Embeddings"
        else:
            job_scores = await self.calculate_job_similarity_tfidf(user_profile, jobs)
            method = "TF-IDF"
        
        # Format recommendations
        recommendations = []
        for job, score in job_scores[:limit]:
            match_reasons = self._generate_match_reasons(user_profile, job, score)
            
            recommendations.append(JobRecommendationResponse(
                job=job,
                similarity_score=float(score),
                match_reasons=match_reasons,
                matching_method=method
            ))
        
        return recommendations
    
    def _generate_match_reasons(
        self, 
        user_profile: str, 
        job: Dict[str, Any], 
        score: float
    ) -> List[str]:
        """Generate human-readable match reasons."""
        reasons = []
        
        # Extract keywords from user profile
        user_words = set(user_profile.lower().split())
        job_text = self.get_job_text(job).lower()
        job_words = set(job_text.split())
        
        # Find common keywords
        common_words = user_words.intersection(job_words)
        common_skills = [word for word in common_words if len(word) > 3]
        
        if score > 0.7:
            reasons.append("🔥 Excellent match for your profile")
        elif score > 0.5:
            reasons.append("Good match for your skills")
        elif score > 0.3:
            reasons.append("⚡ Potential match worth considering")
        else:
            reasons.append("Basic match - might be a stretch opportunity")
        
        if common_skills:
            top_skills = list(common_skills)[:3]
            reasons.append(f"Matches your skills: {', '.join(top_skills)}")
        
        # Check job level based on experience keywords
        if any(word in job_text for word in ['senior', 'lead', 'principal', 'manager']):
            if any(word in user_profile.lower() for word in ['senior', 'lead', 'manager', 'years']):
                reasons.append("📈 Senior-level position matching your experience")
            else:
                reasons.append("Growth opportunity - senior position")
        
        # Remote work preference
        if 'remote' in job_text and score > 0.4:
            reasons.append("🏠 Remote work opportunity")
        
        return reasons[:4]  # Limit to top 4 reasons
    
    async def save_job_for_user(
        self, 
        db: AsyncSession, 
        user_id: int, 
        job_data: Dict[str, Any]
    ) -> bool:
        """Save a job to user's saved jobs list."""
        try:
            saved_job = SavedJob(
                user_id=user_id,
                job_title=job_data.get('position', 'Unknown Position'),
                company_name=job_data.get('company', 'Unknown Company'),
                job_url=job_data.get('url', ''),
                job_data=json.dumps(job_data),
                saved_at=datetime.utcnow()
            )
            
            db.add(saved_job)
            await db.commit()
            return True
            
        except Exception as e:
            print(f"Error saving job: {e}")
            await db.rollback()
            return False
    
    async def get_saved_jobs(
        self, 
        db: AsyncSession, 
        user_id: int, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's saved jobs."""
        result = await db.execute(
            select(SavedJob)
            .where(SavedJob.user_id == user_id)
            .order_by(SavedJob.saved_at.desc())
            .limit(limit)
        )
        
        saved_jobs = result.scalars().all()
        
        return [
            {
                'id': job.id,
                'job_title': job.job_title,
                'company_name': job.company_name,
                'job_url': job.job_url,
                'saved_at': job.saved_at.isoformat(),
                'job_data': json.loads(job.job_data) if job.job_data else {}
            }
            for job in saved_jobs
        ]
    
    def get_matching_capabilities(self) -> Dict[str, Any]:
        """Get information about available matching capabilities."""
        return {
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
            "embedding_model": "all-MiniLM-L6-v2" if self.embedding_model else None,
            "fallback_method": "TF-IDF with scikit-learn",
            "features": [
                "Semantic similarity matching",
                "Skill-based recommendations",
                "Experience level matching",
                "Remote work preference detection",
                "Personalized match explanations"
            ]
        }


# Global instance
job_matching_service = JobMatchingService()