"""
AI Service for TURN Platform - AI PM Teacher and Coaching Features
Provides intelligent project management coaching using FREE AI services.
"""
import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
import logging

# Free AI service imports
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None

# Lazy imports for heavy ML libraries - only import when actually needed
# This prevents slow startup times
pipeline = None
torch = None
AutoTokenizer = None
AutoModelForCausalLM = None

from app.core.config import settings


class AICoachingType(Enum):
    """Types of AI coaching available."""
    PM_FUNDAMENTALS = "pm_fundamentals"
    PRODUCT_STRATEGY = "product_strategy"
    STAKEHOLDER_MANAGEMENT = "stakeholder_management"
    AGILE_SCRUM = "agile_scrum"
    DATA_ANALYSIS = "data_analysis"
    LEADERSHIP = "leadership"
    CAREER_GUIDANCE = "career_guidance"


class LearningLevel(Enum):
    """User learning levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AIProvider(Enum):
    """Available AI providers."""
    GEMINI = "gemini"
    GROQ = "groq" 
    HUGGINGFACE = "huggingface"
    

class AIService:
    """
    AI-powered coaching and learning service using FREE AI providers.
    Supports Google Gemini, Groq, and Hugging Face models.
    """
    
    def __init__(self, provider: AIProvider = AIProvider.GEMINI):
        """Initialize AI service with specified free provider."""
        self.provider = provider
        self.logger = logging.getLogger(__name__)
        
        # Initialize providers
        self._init_providers()
        
    def _init_providers(self):
        """Initialize available AI providers."""
        self.providers = {}
        
        # Google Gemini (Free tier: 15 requests/minute, 1M requests/month)
        if genai and hasattr(settings, 'gemini_api_key') and settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.providers[AIProvider.GEMINI] = genai.GenerativeModel('gemini-pro')
                self.logger.info("Google Gemini initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini: {e}")
        
        # Groq (Free tier: 14,400 tokens/day)
        if Groq and hasattr(settings, 'groq_api_key') and settings.groq_api_key:
            try:
                self.providers[AIProvider.GROQ] = Groq(api_key=settings.groq_api_key)
                self.logger.info("Groq initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Groq: {e}")
                
        # Hugging Face (Free with rate limits) - Lazy import to avoid slow startup
        try:
            from transformers import pipeline as hf_pipeline
            import torch
            # Use smaller model for free hosting
            self.providers[AIProvider.HUGGINGFACE] = hf_pipeline(
                "text-generation",
                model="microsoft/DialoGPT-medium",
                tokenizer="microsoft/DialoGPT-medium",
                device=0 if torch.cuda.is_available() else -1
            )
            self.logger.info("Hugging Face model initialized successfully")
        except ImportError:
            self.logger.debug("Transformers/torch not installed - Hugging Face provider unavailable")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Hugging Face: {e}")
        
        if not self.providers:
            self.logger.warning("No AI providers available. Check API keys and dependencies.")
            
    def get_available_provider(self) -> Optional[AIProvider]:
        """Get the first available provider."""
        if self.provider in self.providers:
            return self.provider
        
        # Fallback to any available provider
        for provider in [AIProvider.GEMINI, AIProvider.GROQ, AIProvider.HUGGINGFACE]:
            if provider in self.providers:
                return provider
        return None
        
    # AI PM Teacher persona
    pm_teacher_system_prompt = """
    You are an expert AI Product Manager Teacher with 15+ years of experience at top tech companies like Google, Amazon, and Microsoft. 
    
    Your role:
    - Provide personalized PM coaching and mentorship
    - Break down complex PM concepts into digestible lessons
    - Offer real-world examples and case studies
    - Give actionable advice for career growth
    - Adapt teaching style to user's experience level
    
    Your teaching style:
    - Socratic method: Ask thought-provoking questions
    - Use real product examples (Netflix, Spotify, Uber, etc.)
    - Provide frameworks and templates
    - Encourage critical thinking
    - Be encouraging but honest about challenges
    
    Always provide structured, actionable responses with clear next steps.
    """
    
    async def _generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate AI response using available provider."""
        provider = self.get_available_provider()
        if not provider:
            return "AI service temporarily unavailable. Please try again later."
            
        full_prompt = f"{system_prompt or self.pm_teacher_system_prompt}\n\nUser: {prompt}\n\nAI:"
        
        try:
            if provider == AIProvider.GEMINI:
                model = self.providers[AIProvider.GEMINI]
                response = model.generate_content(full_prompt)
                return response.text
                
            elif provider == AIProvider.GROQ:
                client = self.providers[AIProvider.GROQ]
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt or self.pm_teacher_system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",  # Free Llama 3 model
                    max_tokens=1000,
                    temperature=0.7
                )
                return chat_completion.choices[0].message.content
                
            elif provider == AIProvider.HUGGINGFACE:
                model = self.providers[AIProvider.HUGGINGFACE]
                response = model(full_prompt, max_length=500, num_return_sequences=1)
                return response[0]['generated_text'][len(full_prompt):].strip()
                
        except Exception as e:
            self.logger.error(f"Error generating AI response with {provider}: {e}")
            return f"I'm having trouble processing your request right now. Please try again later."

    async def get_personalized_learning_path(
        self,
        user_level: LearningLevel,
        career_goals: List[str],
        current_skills: List[str],
        time_commitment: str = "2-3 hours/week"
    ) -> Dict[str, Any]:
        """
        Generate a personalized learning path for the user.
        """
        try:
            prompt = f"""
            Create a personalized 12-week learning path for a {user_level.value} level product manager.
            
            User Profile:
            - Current Level: {user_level.value}
            - Career Goals: {', '.join(career_goals)}
            - Current Skills: {', '.join(current_skills)}
            - Time Commitment: {time_commitment}
            
            Provide a structured learning path with:
            1. Weekly themes and objectives
            2. Recommended courses and resources
            3. Practical exercises and projects
            4. Skills to develop each week
            5. Success metrics and milestones
            
            Format as JSON with this structure:
            {{
                "learning_path": {{
                    "duration": "12 weeks",
                    "weekly_hours": "{time_commitment}",
                    "weeks": [
                        {{
                            "week": 1,
                            "theme": "PM Fundamentals",
                            "objectives": ["Learn core PM concepts", "..."],
                            "activities": ["Read specific chapters", "Complete exercise", "..."],
                            "deliverables": ["Framework document", "..."],
                            "resources": ["Specific course links", "..."]
                        }}
                    ]
                }}
            }}
            """
            
            response = await self._generate_response(prompt)
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"error": "Failed to parse AI response", "raw_response": response}
            
        except Exception as e:
            return {
                "error": f"Failed to generate learning path: {str(e)}",
                "fallback_path": self._get_fallback_learning_path(user_level)
            }

    async def get_ai_coaching_session(
        self,
        coaching_type: AICoachingType,
        user_question: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Conduct an AI coaching session based on user's question and context.
        """
        try:
            context_info = ""
            if user_context:
                context_info = f"""
                User Context:
                - Experience Level: {user_context.get('experience_level', 'Not specified')}
                - Current Role: {user_context.get('current_role', 'Not specified')}
                - Industry: {user_context.get('industry', 'Not specified')}
                - Company Size: {user_context.get('company_size', 'Not specified')}
                """
            
            coaching_focus = {
                AICoachingType.PM_FUNDAMENTALS: "product management fundamentals, frameworks, and core concepts",
                AICoachingType.PRODUCT_STRATEGY: "product strategy, roadmapping, and vision setting",
                AICoachingType.STAKEHOLDER_MANAGEMENT: "stakeholder communication, alignment, and influence",
                AICoachingType.AGILE_SCRUM: "agile methodologies, scrum practices, and sprint planning",
                AICoachingType.DATA_ANALYSIS: "data-driven decision making, metrics, and analytics",
                AICoachingType.LEADERSHIP: "team leadership, cross-functional collaboration, and people management",
                AICoachingType.CAREER_GUIDANCE: "career development, skill building, and advancement strategies"
            }
            
            prompt = f"""
            {self.pm_teacher_system_prompt}
            
            Coaching Focus: {coaching_focus[coaching_type]}
            {context_info}
            
            User Question: "{user_question}"
            
            Provide a comprehensive coaching response that includes:
            1. Direct answer to their question
            2. Relevant framework or methodology
            3. Real-world example or case study
            4. 2-3 follow-up questions to deepen understanding
            5. Specific next steps or action items
            6. Additional resources for further learning
            
            Keep the tone encouraging, practical, and mentor-like.
            """
            
            response = await self._generate_response(prompt)
            
            return {
                "coaching_type": coaching_type.value,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "follow_up_available": True
            }
            
        except Exception as e:
            return {
                "error": f"Coaching session failed: {str(e)}",
                "fallback_response": self._get_fallback_coaching_response(coaching_type)
            }

    async def analyze_project_scenario(
        self,
        scenario_description: str,
        decisions_made: List[Dict[str, str]],
        user_level: LearningLevel
    ) -> Dict[str, Any]:
        """
        Analyze a project management scenario and provide feedback.
        """
        try:
            decisions_text = "\n".join([
                f"- {decision['decision']}: {decision['rationale']}" 
                for decision in decisions_made
            ])
            
            prompt = f"""
            As an expert PM coach, analyze this project scenario and the user's decisions.
            
            Scenario: {scenario_description}
            
            User's Decisions and Rationale:
            {decisions_text}
            
            User Level: {user_level.value}
            
            Provide detailed feedback including:
            1. Overall assessment of decisions (score out of 10)
            2. Strengths in their approach
            3. Areas for improvement
            4. Alternative approaches they could have considered
            5. Key learnings and takeaways
            6. Similar real-world scenarios for reference
            
            Tailor feedback complexity to their {user_level.value} level.
            """
            
            response = await self._generate_response(prompt)
            
            return {
                "scenario_analysis": response,
                "analyzed_at": datetime.now().isoformat(),
                "user_level": user_level.value
            }
            
        except Exception as e:
            return {
                "error": f"Scenario analysis failed: {str(e)}",
                "fallback_feedback": "Please review your decisions against standard PM frameworks and try again."
            }

    async def generate_interview_questions(
        self,
        job_level: str,
        company_type: str,
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """
        Generate personalized PM interview questions for practice.
        """
        try:
            prompt = f"""
            Generate a comprehensive set of product manager interview questions for:
            - Job Level: {job_level}
            - Company Type: {company_type}
            - Focus Areas: {', '.join(focus_areas)}
            
            Create 15 questions across these categories:
            1. Product Strategy (4 questions)
            2. Technical/Analytical (3 questions)
            3. Behavioral/Leadership (4 questions)
            4. Case Study/Problem Solving (2 questions)
            5. Company-Specific (2 questions)
            
            For each question, provide:
            - The question
            - What the interviewer is looking for
            - Key points to cover in response
            - Common mistakes to avoid
            
            Format as structured JSON.
            """
            
            response = await self._generate_response(prompt)
            
            try:
                questions_data = json.loads(response)
            except json.JSONDecodeError:
                questions_data = {"error": "Failed to parse questions", "raw_response": response}
            
            return {
                "interview_questions": questions_data,
                "generated_at": datetime.now().isoformat(),
                "job_level": job_level,
                "company_type": company_type
            }
            
        except Exception as e:
            return {
                "error": f"Question generation failed: {str(e)}",
                "fallback_questions": self._get_fallback_interview_questions()
            }

    async def provide_career_guidance(
        self,
        current_situation: Dict[str, Any],
        career_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provide personalized career guidance and development advice.
        """
        try:
            prompt = f"""
            Provide comprehensive career guidance for this product manager:
            
            Current Situation:
            - Role: {current_situation.get('current_role', 'Not specified')}
            - Experience: {current_situation.get('years_experience', 'Not specified')} years
            - Company: {current_situation.get('company_type', 'Not specified')}
            - Skills: {current_situation.get('current_skills', [])}
            - Challenges: {current_situation.get('challenges', [])}
            
            Career Goals:
            - Target Role: {career_goals.get('target_role', 'Not specified')}
            - Timeline: {career_goals.get('timeline', 'Not specified')}
            - Industry Preference: {career_goals.get('industry', 'Not specified')}
            - Growth Areas: {career_goals.get('growth_areas', [])}
            
            Provide actionable guidance including:
            1. Gap analysis between current state and goals
            2. Specific skills to develop
            3. Experience to gain
            4. Network building strategies
            5. Timeline and milestones
            6. Potential career paths
            7. Recommended actions for next 3, 6, and 12 months
            """
            
            response = await self._generate_response(prompt)
            
            return {
                "career_guidance": response,
                "generated_at": datetime.now().isoformat(),
                "follow_up_recommended": True
            }
            
        except Exception as e:
            return {
                "error": f"Career guidance failed: {str(e)}",
                "fallback_advice": "Focus on developing core PM skills: strategy, execution, and leadership."
            }



    def _get_fallback_learning_path(self, user_level: LearningLevel) -> Dict[str, Any]:
        """
        Provide fallback learning path when AI fails.
        """
        return {
            "duration": "12 weeks",
            "weekly_hours": "2-3 hours",
            "weeks": [
                {
                    "week": 1,
                    "theme": "PM Fundamentals",
                    "objectives": ["Understand PM role", "Learn core frameworks"],
                    "activities": ["Read PM literature", "Complete exercises"],
                    "deliverables": ["PM framework document"],
                    "resources": ["Product Management courses"]
                }
            ]
        }

    def _get_fallback_coaching_response(self, coaching_type: AICoachingType) -> str:
        """
        Provide fallback coaching response when AI fails.
        """
        return f"I'm currently unable to provide personalized coaching for {coaching_type.value}. Please try again later or consult our learning resources."

    def _get_fallback_interview_questions(self) -> List[Dict[str, str]]:
        """
        Provide fallback interview questions when AI fails.
        """
        return [
            {
                "question": "How do you prioritize features in a product roadmap?",
                "category": "Product Strategy",
                "guidance": "Discuss frameworks like RICE, MoSCoW, or Impact vs Effort"
            }
        ]
    
    # Auto-Application AI Methods
    
    async def generate_custom_cover_letter(
        self,
        user_profile: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any],
        template: Optional[str] = None
    ) -> str:
        """
        Generate a customized cover letter for job application.
        
        Args:
            user_profile: User profile information
            cv_data: User's CV data
            job_data: Job posting details
            template: Optional custom template
            
        Returns:
            Generated cover letter
        """
        try:
            # Extract key information
            user_name = user_profile.get('name', 'Candidate')
            current_role = user_profile.get('current_job_title', 'Professional')
            experience_years = user_profile.get('years_of_experience', 0)
            skills = user_profile.get('skills', [])
            career_goals = user_profile.get('career_goals', '')
            
            job_title = job_data.get('title', 'Position')
            company = job_data.get('company', 'Company')
            job_description = job_data.get('description', '')[:1000]  # Limit for context
            
            # Get recent experience
            recent_experience = ""
            if cv_data.get('experiences'):
                latest_exp = cv_data['experiences'][0]
                recent_experience = f"{latest_exp.get('job_title', '')} at {latest_exp.get('company_name', '')} - {latest_exp.get('description', '')[:200]}"
            
            prompt = f"""
            Write a compelling, personalized cover letter for this job application:
            
            Candidate Information:
            - Name: {user_name}
            - Current Role: {current_role}
            - Experience: {experience_years} years
            - Key Skills: {', '.join(skills[:6])}
            - Career Goals: {career_goals}
            - Recent Experience: {recent_experience}
            
            Job Information:
            - Position: {job_title}
            - Company: {company}
            - Job Description: {job_description}
            
            Requirements:
            1. Professional but personable tone
            2. Show enthusiasm for the specific role and company
            3. Highlight 2-3 most relevant experiences/skills
            4. Demonstrate understanding of company/industry
            5. Include a compelling value proposition
            6. 3-4 paragraphs maximum
            7. Avoid generic phrases
            8. Include specific examples where possible
            
            Template guidance: {template if template else 'Use standard professional format'}
            
            Return only the cover letter content, no additional formatting or explanations.
            """
            
            response = await self._generate_response(prompt)
            
            # Clean up the response
            cover_letter = response.strip()
            
            # Ensure it starts with proper greeting if missing
            if not cover_letter.lower().startswith(('dear', 'hello', 'greetings')):
                cover_letter = f"Dear Hiring Manager,\n\n{cover_letter}"
            
            # Ensure it ends with proper closing if missing
            if not any(closing in cover_letter.lower() for closing in ['sincerely', 'best regards', 'thank you']):
                cover_letter += f"\n\nBest regards,\n{user_name}"
            
            return cover_letter
            
        except Exception as e:
            self.logger.error(f"Error generating custom cover letter: {str(e)}")
            return self._get_fallback_cover_letter(user_profile, job_data)
    
    async def generate_cv_optimization_suggestions(
        self,
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate CV optimization suggestions for specific job.
        
        Args:
            cv_data: User's CV data
            job_data: Job posting details
            
        Returns:
            CV optimization suggestions
        """
        try:
            job_title = job_data.get('title', '')
            job_description = job_data.get('description', '')
            company = job_data.get('company', '')
            
            # Extract current CV content
            current_summary = cv_data.get('summary', '')
            current_skills = [skill for skill in cv_data.get('skills', [])]
            current_experiences = cv_data.get('experiences', [])
            
            prompt = f"""
            Analyze this CV against the job requirements and provide optimization suggestions:
            
            Job Details:
            - Title: {job_title}
            - Company: {company}
            - Description: {job_description[:1000]}
            
            Current CV Content:
            - Summary: {current_summary}
            - Skills: {', '.join(current_skills)}
            - Experience Count: {len(current_experiences)}
            
            Provide specific recommendations for:
            1. Summary/Objective optimization (2-3 sentences)
            2. Skills to highlight/reorder (from existing skills)
            3. Keywords to incorporate
            4. Experience descriptions to emphasize
            5. Overall positioning strategy
            
            Return as JSON with sections: summary_suggestions, skills_optimization, keywords_to_add, experience_focus, positioning_advice
            """
            
            response = await self._generate_response(prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Parse manually if JSON parsing fails
                return self._parse_cv_suggestions_text(response)
                
        except Exception as e:
            self.logger.error(f"Error generating CV optimization suggestions: {str(e)}")
            return self._get_fallback_cv_suggestions()
    
    async def assess_job_application_strength(
        self,
        user_profile: Dict[str, Any],
        cv_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess the strength of a job application match.
        
        Args:
            user_profile: User profile information
            cv_data: User's CV data  
            job_data: Job posting details
            
        Returns:
            Application strength assessment
        """
        try:
            prompt = f"""
            Assess the strength of this job application match and provide detailed analysis:
            
            Candidate Profile:
            - Experience: {user_profile.get('years_of_experience', 0)} years
            - Current Role: {user_profile.get('current_job_title', 'N/A')}
            - Skills: {', '.join(user_profile.get('skills', [])[:8])}
            - Career Goals: {user_profile.get('career_goals', 'N/A')}
            
            Job Requirements:
            - Title: {job_data.get('title', 'N/A')}
            - Company: {job_data.get('company', 'N/A')}
            - Description: {job_data.get('description', 'N/A')[:800]}
            
            Provide assessment as JSON with:
            {{
                "overall_strength": "excellent|good|fair|weak",
                "match_score": 0.85,
                "strengths": ["skill match", "experience level", "etc"],
                "weaknesses": ["missing skill X", "etc"],
                "recommendations": ["action 1", "action 2"],
                "likelihood_of_response": "high|medium|low",
                "estimated_competition_level": "high|medium|low",
                "application_strategy": "specific advice for this application"
            }}
            """
            
            response = await self._generate_response(prompt)
            
            try:
                assessment = json.loads(response)
                # Ensure numeric score
                if 'match_score' in assessment:
                    assessment['match_score'] = float(assessment['match_score'])
                return assessment
            except (json.JSONDecodeError, ValueError):
                return self._get_fallback_assessment()
                
        except Exception as e:
            self.logger.error(f"Error assessing job application strength: {str(e)}")
            return self._get_fallback_assessment()
    
    async def generate_interview_prep_content(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate interview preparation content for specific job.
        
        Args:
            user_profile: User profile information
            job_data: Job posting details
            
        Returns:
            Interview preparation content
        """
        try:
            prompt = f"""
            Generate comprehensive interview preparation content for this job:
            
            Candidate:
            - Experience: {user_profile.get('years_of_experience', 0)} years
            - Current Role: {user_profile.get('current_job_title', 'N/A')}
            - Skills: {', '.join(user_profile.get('skills', [])[:6])}
            
            Job:
            - Title: {job_data.get('title', 'N/A')}
            - Company: {job_data.get('company', 'N/A')}
            - Description: {job_data.get('description', 'N/A')[:800]}
            
            Generate as JSON:
            {{
                "likely_questions": [
                    {{"question": "...", "category": "behavioral|technical|situational", "guidance": "how to answer"}},
                ],
                "company_research_points": ["fact 1", "fact 2"],
                "questions_to_ask": ["question 1", "question 2"],
                "key_stories_to_prepare": ["situation/project to highlight"],
                "technical_topics_to_review": ["topic 1", "topic 2"],
                "red_flags_to_address": ["potential concern"]
            }}
            """
            
            response = await self._generate_response(prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return self._get_fallback_interview_prep()
                
        except Exception as e:
            self.logger.error(f"Error generating interview prep content: {str(e)}")
            return self._get_fallback_interview_prep()
    
    # Helper methods for fallbacks
    
    def _get_fallback_cover_letter(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> str:
        """Fallback cover letter template."""
        user_name = user_profile.get('name', 'Candidate')
        job_title = job_data.get('title', 'position')
        company = job_data.get('company', 'your company')
        experience_years = user_profile.get('years_of_experience', 'several')
        
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With {experience_years} years of experience in project management and a proven track record of delivering successful outcomes, I am excited about the opportunity to contribute to your team.

My background has equipped me with strong analytical, communication, and leadership skills that align well with the requirements outlined in your job posting. I am particularly drawn to this role because it offers the opportunity to make a meaningful impact while continuing to grow professionally.

I would welcome the chance to discuss how my experience and passion for excellence can benefit your organization. Thank you for considering my application.

Best regards,
{user_name}"""
    
    def _get_fallback_cv_suggestions(self) -> Dict[str, Any]:
        """Fallback CV optimization suggestions."""
        return {
            "summary_suggestions": "Tailor your summary to highlight relevant project management experience and key achievements.",
            "skills_optimization": ["Reorder skills to match job requirements", "Add quantifiable achievements"],
            "keywords_to_add": ["project management", "stakeholder communication", "process improvement"],
            "experience_focus": "Emphasize leadership and project delivery experience",
            "positioning_advice": "Position yourself as a results-driven professional with strong execution capabilities"
        }
    
    def _get_fallback_assessment(self) -> Dict[str, Any]:
        """Fallback application strength assessment."""
        return {
            "overall_strength": "good",
            "match_score": 0.7,
            "strengths": ["Relevant experience", "Strong skill set"],
            "weaknesses": ["Consider highlighting specific achievements"],
            "recommendations": ["Customize cover letter", "Quantify accomplishments"],
            "likelihood_of_response": "medium",
            "estimated_competition_level": "medium",
            "application_strategy": "Focus on demonstrating value and fit for the role"
        }
    
    def _get_fallback_interview_prep(self) -> Dict[str, Any]:
        """Fallback interview preparation content."""
        return {
            "likely_questions": [
                {"question": "Tell me about yourself", "category": "behavioral", "guidance": "Focus on professional journey and relevant experience"},
                {"question": "Why are you interested in this role?", "category": "motivational", "guidance": "Connect your goals with the position"}
            ],
            "company_research_points": ["Research company mission and values", "Review recent news and developments"],
            "questions_to_ask": ["What does success look like in this role?", "What are the biggest challenges facing the team?"],
            "key_stories_to_prepare": ["Success story demonstrating leadership", "Challenge overcome through problem-solving"],
            "technical_topics_to_review": ["Project management methodologies", "Industry-specific knowledge"],
            "red_flags_to_address": ["Be prepared to explain any gaps or transitions"]
        }
    
    def _parse_cv_suggestions_text(self, text: str) -> Dict[str, Any]:
        """Parse CV suggestions from text when JSON parsing fails."""
        # Simple text parsing fallback
        return {
            "summary_suggestions": "Optimize summary based on job requirements",
            "skills_optimization": ["Highlight relevant skills", "Use job-specific keywords"],
            "keywords_to_add": ["project management", "leadership", "analytics"],
            "experience_focus": "Emphasize measurable achievements",
            "positioning_advice": "Position as a strategic thinker and execution expert"
        }


# Global AI service instance
ai_service = AIService()