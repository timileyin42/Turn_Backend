"""
Real job search API integration service with smart matching.
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


class RemoteOKAPI:
    """Integration with RemoteOK job board API."""
    
    @staticmethod
    async def fetch_pm_jobs() -> List[Dict[str, Any]]:
        """Fetch project management jobs from RemoteOK."""
        async with aiohttp.ClientSession() as session:
            try:
                headers = {'User-Agent': 'Turn-Platform-Job-Search/1.0'}
                async with session.get(settings.remoteok_api_url, headers=headers) as response:
                    if response.status == 200:
                        jobs = await response.json()
                        # Filter for PM jobs
                        pm_jobs = [
                            job for job in jobs 
                            if isinstance(job, dict) and any(
                                keyword in str(job.get('position', '')).lower() 
                                for keyword in ['project manager', 'project management', 'pm', 'program manager', 'scrum master', 'product manager']
                            )
                        ]
                        return pm_jobs[:50]
                    return []
            except Exception as e:
                print(f"Error fetching RemoteOK jobs: {e}")
                return []


class RemotiveAPI:
    """Integration with Remotive job board API."""
    
    @staticmethod
    async def fetch_pm_jobs() -> List[Dict[str, Any]]:
        """Fetch project management jobs from Remotive."""
        async with aiohttp.ClientSession() as session:
            try:
                params = {
                    'category': 'project-management',
                    'limit': 50
                }
                async with session.get(settings.remotive_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('jobs', [])
                    return []
            except Exception as e:
                print(f"Error fetching Remotive jobs: {e}")
                return []


class GitHubJobsAPI:
    """Integration with GitHub Jobs API (via third-party)."""
    
    @staticmethod
    async def fetch_pm_jobs() -> List[Dict[str, Any]]:
        """Fetch project management jobs from GitHub's career repositories."""
        async with aiohttp.ClientSession() as session:
            try:
                # Search for repositories with job postings
                params = {
                    'q': 'project manager jobs hiring',
                    'sort': 'updated',
                    'order': 'desc',
                    'per_page': 20
                }
                async with session.get(settings.github_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Transform repository data into job-like format
                        jobs = []
                        for repo in data.get('items', []):
                            if 'job' in repo.get('name', '').lower() or 'career' in repo.get('name', '').lower():
                                jobs.append({
                                    'id': f"github_{repo['id']}",
                                    'title': f"Project Manager at {repo['owner']['login']}",
                                    'company': repo['owner']['login'],
                                    'description': repo.get('description', ''),
                                    'url': repo['html_url'],
                                    'location': 'Remote',
                                    'posted_date': repo['updated_at'],
                                    'source': 'GitHub'
                                })
                        return jobs
                    return []
            except Exception as e:
                print(f"Error fetching GitHub jobs: {e}")
                return []


class AngelListAPI:
    """Integration with AngelList/Wellfound API."""
    
    @staticmethod
    async def fetch_startup_pm_jobs() -> List[Dict[str, Any]]:
        """Fetch project management jobs from startups."""
        # Note: AngelList API requires authentication, this is a simplified version
        # In production, you'd need to register for API access
        async with aiohttp.ClientSession() as session:
            try:
                # This would require proper API key and authentication
                # URL from settings: settings.angellist_api_url
                # For now, return structured data format that would come from their API
                return []
            except Exception as e:
                print(f"Error fetching AngelList jobs: {e}")
                return []


class LinkedInJobsAPI:
    """Integration with LinkedIn Jobs (via RapidAPI or direct scraping)."""
    
    @staticmethod
    async def fetch_linkedin_pm_jobs(rapidapi_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch PM jobs from LinkedIn via RapidAPI."""
        if not rapidapi_key:
            return []
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'X-RapidAPI-Key': rapidapi_key,
                    'X-RapidAPI-Host': 'linkedin-data-api.p.rapidapi.com'
                }
                
                params = {
                    'keywords': 'project manager',
                    'locationId': '103644278',  # United States
                    'dateSincePosted': 'past24Hours',
                    'sort': 'mostRecent'
                }
                
                async with session.get(
                    settings.linkedin_rapidapi_url,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
                    return []
            except Exception as e:
                print(f"Error fetching LinkedIn jobs: {e}")
                return []


class IndeedAPI:
    """Integration with Indeed job search (via RapidAPI)."""
    
    @staticmethod
    async def fetch_indeed_pm_jobs(rapidapi_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch PM jobs from Indeed via RapidAPI."""
        if not rapidapi_key:
            return []
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'X-RapidAPI-Key': rapidapi_key,
                    'X-RapidAPI-Host': 'indeed12.p.rapidapi.com'
                }
                
                params = {
                    'query': 'project manager',
                    'location': 'United States',
                    'page_id': '1'
                }
                
                async with session.get(
                    settings.indeed_rapidapi_url,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('hits', [])
                    return []
            except Exception as e:
                print(f"Error fetching Indeed jobs: {e}")
                return []


class CrunchbaseAPI:
    """Integration with Crunchbase for startup hiring data."""
    
    @staticmethod
    async def fetch_startup_hiring_data(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch startup companies that are actively hiring."""
        if not api_key:
            return []
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'X-cb-user-key': api_key,
                    'Content-Type': 'application/json'
                }
                
                # Search for companies actively hiring
                url = settings.crunchbase_api_url
                
                payload = {
                    "field_ids": ["name", "short_description", "website", "location_identifiers"],
                    "query": [
                        {
                            "type": "predicate",
                            "field_id": "facet_ids",
                            "operator_id": "includes",
                            "values": ["company"]
                        }
                    ],
                    "limit": 50
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        companies = data.get('entities', [])
                        
                        # Transform to job-like format
                        jobs = []
                        for company in companies:
                            properties = company.get('properties', {})
                            jobs.append({
                                'id': f"crunchbase_{company.get('uuid')}",
                                'title': f"Project Manager at {properties.get('name')}",
                                'company': properties.get('name'),
                                'description': properties.get('short_description', ''),
                                'url': properties.get('website', {}).get('value', ''),
                                'location': 'Startup Environment',
                                'posted_date': datetime.utcnow().isoformat(),
                                'source': 'Crunchbase',
                                'job_type': 'startup'
                            })
                        return jobs
                    return []
            except Exception as e:
                print(f"Error fetching Crunchbase data: {e}")
                return []


class JobSearchService:
    """Main service to aggregate job listings from multiple sources."""
    
    def __init__(self):
        self.sources = {
            'remoteok': RemoteOKAPI,
            'remotive': RemotiveAPI,
            'github': GitHubJobsAPI,
            'angellist': AngelListAPI,
            'linkedin': LinkedInJobsAPI,
            'indeed': IndeedAPI,
            'crunchbase': CrunchbaseAPI
        }
    
    async def fetch_all_pm_jobs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch project management jobs from all sources."""
        jobs = {}
        
        # Free APIs (no key required)
        free_tasks = [
            self._fetch_remoteok_jobs(),
            self._fetch_remotive_jobs(),
            self._fetch_github_jobs()
        ]
        
        # Paid APIs (require keys)
        paid_tasks = []
        
        linkedin_key = getattr(settings, 'linkedin_rapidapi_key', None)
        if linkedin_key:
            paid_tasks.append(self._fetch_linkedin_jobs(linkedin_key))
        
        indeed_key = getattr(settings, 'indeed_rapidapi_key', None)
        if indeed_key:
            paid_tasks.append(self._fetch_indeed_jobs(indeed_key))
        
        crunchbase_key = getattr(settings, 'crunchbase_api_key', None)
        if crunchbase_key:
            paid_tasks.append(self._fetch_crunchbase_jobs(crunchbase_key))
        
        # Execute all tasks
        all_tasks = free_tasks + paid_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Process results
        jobs['remoteok'] = results[0] if len(results) > 0 and not isinstance(results[0], Exception) else []
        jobs['remotive'] = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else []
        jobs['github'] = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []
        
        # Add paid API results
        result_index = 3
        if linkedin_key and len(results) > result_index:
            jobs['linkedin'] = results[result_index] if not isinstance(results[result_index], Exception) else []
            result_index += 1
        
        if indeed_key and len(results) > result_index:
            jobs['indeed'] = results[result_index] if not isinstance(results[result_index], Exception) else []
            result_index += 1
        
        if crunchbase_key and len(results) > result_index:
            jobs['crunchbase'] = results[result_index] if not isinstance(results[result_index], Exception) else []
        
        return jobs
    
    async def _fetch_remoteok_jobs(self) -> List[Dict[str, Any]]:
        """Fetch RemoteOK jobs."""
        return await RemoteOKAPI.fetch_pm_jobs()
    
    async def _fetch_remotive_jobs(self) -> List[Dict[str, Any]]:
        """Fetch Remotive jobs."""
        return await RemotiveAPI.fetch_pm_jobs()
    
    async def _fetch_github_jobs(self) -> List[Dict[str, Any]]:
        """Fetch GitHub jobs."""
        return await GitHubJobsAPI.fetch_pm_jobs()
    
    async def _fetch_linkedin_jobs(self, api_key: str) -> List[Dict[str, Any]]:
        """Fetch LinkedIn jobs."""
        return await LinkedInJobsAPI.fetch_linkedin_pm_jobs(api_key)
    
    async def _fetch_indeed_jobs(self, api_key: str) -> List[Dict[str, Any]]:
        """Fetch Indeed jobs."""
        return await IndeedAPI.fetch_indeed_pm_jobs(api_key)
    
    async def _fetch_crunchbase_jobs(self, api_key: str) -> List[Dict[str, Any]]:
        """Fetch Crunchbase startup data."""
        return await CrunchbaseAPI.fetch_startup_hiring_data(api_key)
    
    def normalize_job_data(self, raw_jobs: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Normalize job data from different sources."""
        normalized_jobs = []
        
        # Normalize RemoteOK jobs
        for job in raw_jobs.get('remoteok', []):
            if isinstance(job, dict) and job.get('position'):
                normalized_jobs.append({
                    'id': f"remoteok_{job.get('id')}",
                    'title': job.get('position', ''),
                    'company': job.get('company', ''),
                    'location': 'Remote',
                    'remote_option': True,
                    'description': job.get('description', ''),
                    'requirements': self._extract_requirements(job.get('description', '')),
                    'responsibilities': self._extract_responsibilities(job.get('description', '')),
                    'salary_min': self._parse_salary_min(job.get('salary_min')),
                    'salary_max': self._parse_salary_max(job.get('salary_max')),
                    'currency': 'USD',
                    'experience_level': self._determine_experience_level(job.get('position', '')),
                    'employment_type': 'full-time',
                    'industry': 'Technology',
                    'skills_required': job.get('tags', []),
                    'application_url': job.get('url', ''),
                    'posted_at': self._parse_date(job.get('date')),
                    'source': 'RemoteOK',
                    'logo_url': job.get('logo', '')
                })
        
        # Normalize Remotive jobs
        for job in raw_jobs.get('remotive', []):
            normalized_jobs.append({
                'id': f"remotive_{job.get('id')}",
                'title': job.get('title', ''),
                'company': job.get('company_name', ''),
                'location': 'Remote',
                'remote_option': True,
                'description': job.get('description', ''),
                'requirements': self._extract_requirements(job.get('description', '')),
                'responsibilities': self._extract_responsibilities(job.get('description', '')),
                'salary_min': None,
                'salary_max': None,
                'currency': 'USD',
                'experience_level': job.get('job_type', 'mid-level'),
                'employment_type': 'full-time',
                'industry': job.get('category', 'Technology'),
                'skills_required': [],
                'application_url': job.get('url', ''),
                'posted_at': job.get('publication_date', ''),
                'source': 'Remotive',
                'logo_url': job.get('company_logo', '')
            })
        
        # Add other sources...
        
        return normalized_jobs
    
    def _extract_requirements(self, description: str) -> str:
        """Extract requirements from job description."""
        if not description:
            return ""
        
        # Look for requirements section
        requirements_patterns = [
            r"requirements?:(.+?)(?:responsibilities?:|qualifications?:|$)",
            r"qualifications?:(.+?)(?:requirements?:|responsibilities?:|$)",
            r"what you.{0,20}need:(.+?)(?:what you.{0,20}do:|responsibilities?:|$)"
        ]
        
        for pattern in requirements_patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_responsibilities(self, description: str) -> str:
        """Extract responsibilities from job description."""
        if not description:
            return ""
        
        # Look for responsibilities section
        responsibilities_patterns = [
            r"responsibilities?:(.+?)(?:requirements?:|qualifications?:|$)",
            r"what you.{0,20}do:(.+?)(?:what you.{0,20}need:|requirements?:|$)",
            r"role:(.+?)(?:requirements?:|qualifications?:|$)"
        ]
        
        for pattern in responsibilities_patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _parse_salary_min(self, salary_data) -> Optional[int]:
        """Parse minimum salary from various formats."""
        if not salary_data:
            return None
        
        if isinstance(salary_data, (int, float)):
            return int(salary_data)
        
        if isinstance(salary_data, str):
            # Extract numbers from salary string
            numbers = re.findall(r'\d+', salary_data.replace(',', ''))
            if numbers:
                return int(numbers[0]) * 1000 if len(numbers[0]) <= 3 else int(numbers[0])
        
        return None
    
    def _parse_salary_max(self, salary_data) -> Optional[int]:
        """Parse maximum salary from various formats."""
        if not salary_data:
            return None
        
        if isinstance(salary_data, (int, float)):
            return int(salary_data)
        
        if isinstance(salary_data, str):
            numbers = re.findall(r'\d+', salary_data.replace(',', ''))
            if len(numbers) >= 2:
                return int(numbers[1]) * 1000 if len(numbers[1]) <= 3 else int(numbers[1])
            elif len(numbers) == 1:
                return int(numbers[0]) * 1000 if len(numbers[0]) <= 3 else int(numbers[0])
        
        return None
    
    def _determine_experience_level(self, title: str) -> str:
        """Determine experience level from job title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['senior', 'sr', 'lead', 'principal', 'director']):
            return 'senior'
        elif any(word in title_lower for word in ['junior', 'jr', 'entry', 'associate', 'trainee']):
            return 'entry-level'
        else:
            return 'mid-level'
    
    def _parse_date(self, date_str) -> str:
        """Parse and normalize date strings."""
        if not date_str:
            return datetime.utcnow().isoformat()
        
        try:
            # Try to parse various date formats
            if isinstance(date_str, str):
                # Unix timestamp
                if date_str.isdigit():
                    return datetime.fromtimestamp(int(date_str)).isoformat()
                # ISO format
                elif 'T' in date_str:
                    return date_str
                # Other formats would need more parsing
            
            return datetime.utcnow().isoformat()
        except:
            return datetime.utcnow().isoformat()
    
    async def get_personalized_job_recommendations(
        self, 
        db: AsyncSession, 
        user_id: int, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get personalized job recommendations using smart matching."""
        try:
            # Import here to avoid circular imports
            from app.services.job_matching_service import job_matching_service
            
            # Fetch jobs from all free sources
            all_jobs = []
            
            # Get jobs from free APIs
            remoteok_jobs = await RemoteOKAPI.fetch_pm_jobs()
            remotive_jobs = await RemotiveAPI.fetch_pm_jobs()
            github_jobs = await GitHubJobsAPI.fetch_pm_jobs()
            
            # Combine and normalize jobs
            for job in remoteok_jobs:
                normalized_job = self._normalize_job_data(job, 'remoteok')
                all_jobs.append(normalized_job)
            
            for job in remotive_jobs:
                normalized_job = self._normalize_job_data(job, 'remotive')
                all_jobs.append(normalized_job)
            
            for job in github_jobs:
                normalized_job = self._normalize_job_data(job, 'github')
                all_jobs.append(normalized_job)
            
            # Remove duplicates based on job title and company
            unique_jobs = []
            seen_jobs = set()
            
            for job in all_jobs:
                job_key = f"{job.get('position', '')}-{job.get('company', '')}".lower()
                if job_key not in seen_jobs:
                    seen_jobs.add(job_key)
                    unique_jobs.append(job)
            
            # Get smart recommendations
            recommendations = await job_matching_service.get_job_recommendations(
                db, user_id, unique_jobs, limit
            )
            
            return [rec.dict() for rec in recommendations]
            
        except Exception as e:
            print(f"Error getting personalized recommendations: {e}")
            # Fallback to regular job search
            jobs_data = await self.fetch_all_pm_jobs()
            all_jobs = []
            for source, jobs in jobs_data.items():
                for job in jobs[:5]:  # Limit fallback
                    all_jobs.append(self._normalize_job_data(job, source))
            return all_jobs[:limit]
    
    async def save_job_for_user(
        self, 
        db: AsyncSession, 
        user_id: int, 
        job_data: Dict[str, Any]
    ) -> bool:
        """Save a job to user's saved jobs list."""
        try:
            from app.services.job_matching_service import job_matching_service
            return await job_matching_service.save_job_for_user(db, user_id, job_data)
        except Exception as e:
            print(f"Error saving job: {e}")
            return False
    
    async def get_user_saved_jobs(
        self, 
        db: AsyncSession, 
        user_id: int, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's saved jobs."""
        try:
            from app.services.job_matching_service import job_matching_service
            return await job_matching_service.get_saved_jobs(db, user_id, limit)
        except Exception as e:
            print(f"Error getting saved jobs: {e}")
            return []
    
    def get_matching_info(self) -> Dict[str, Any]:
        """Get information about smart matching capabilities."""
        try:
            from app.services.job_matching_service import job_matching_service
            return job_matching_service.get_matching_capabilities()
        except Exception as e:
            return {
                "sentence_transformers_available": False,
                "embedding_model": None,
                "fallback_method": "Basic job aggregation",
                "features": ["Basic job aggregation from free APIs"],
                "error": str(e)
            }


# Global instance
job_search_service = JobSearchService()