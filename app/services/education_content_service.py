"""
External education content providers for real course data.
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.core.config import settings


class CourseraAPI:
    """Integration with Coursera's public course catalog."""
    
    @staticmethod
    async def fetch_pm_courses() -> List[Dict[str, Any]]:
        """Fetch project management courses from Coursera."""
        async with aiohttp.ClientSession() as session:
            try:
                # Coursera public API for project management courses
                params = {
                    'q': 'search',
                    'query': 'project management',
                    'fields': 'name,description,photoUrl,instructorIds,partnerIds,startDate,workload,language',
                    'limit': 50
                }
                
                async with session.get(f"{settings.coursera_api_url}/courses", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('elements', [])
                    return []
            except Exception as e:
                print(f"Error fetching Coursera courses: {e}")
                return []


class EdXAPI:
    """Integration with edX course catalog."""
    
    @staticmethod
    async def fetch_pm_courses() -> List[Dict[str, Any]]:
        """Fetch project management courses from edX."""
        async with aiohttp.ClientSession() as session:
            try:
                params = {
                    'search_term': 'project management',
                    'page_size': 50
                }
                
                async with session.get(f"{settings.edx_api_url}/courses/", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('results', [])
                    return []
            except Exception as e:
                print(f"Error fetching edX courses: {e}")
                return []


class FutureLearnAPI:
    """Integration with FutureLearn course catalog."""
    
    @staticmethod
    async def fetch_pm_courses() -> List[Dict[str, Any]]:
        """Fetch project management courses from FutureLearn."""
        async with aiohttp.ClientSession() as session:
            try:
                params = {
                    'q': 'project management',
                    'page_size': 50
                }
                
                async with session.get(settings.futurelearn_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('objects', [])
                    return []
            except Exception as e:
                print(f"Error fetching FutureLearn courses: {e}")
                return []


class KhanAcademyAPI:
    """Integration with Khan Academy's public API."""
    
    @staticmethod
    async def fetch_business_content() -> List[Dict[str, Any]]:
        """Fetch business and entrepreneurship content from Khan Academy."""
        async with aiohttp.ClientSession() as session:
            try:
                # Khan Academy topic tree for business content
                async with session.get(f"{settings.khan_academy_api_url}/topic/business-and-entrepreneurship") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('children', [])
                    return []
            except Exception as e:
                print(f"Error fetching Khan Academy content: {e}")
                return []


class YouTubeEduAPI:
    """Integration with YouTube Educational content."""
    
    @staticmethod
    async def fetch_pm_videos(api_key: str) -> List[Dict[str, Any]]:
        """Fetch project management educational videos from YouTube."""
        async with aiohttp.ClientSession() as session:
            try:
                # Search for high-quality project management educational content
                search_queries = [
                    'project management course tutorial',
                    'PMP certification training',
                    'agile scrum master training',
                    'project manager skills development',
                    'PMI project management professional'
                ]
                
                all_videos = []
                
                for query in search_queries:
                    params = {
                        'part': 'snippet,statistics',
                        'q': query,
                        'type': 'video',
                        'videoDuration': 'medium',  # 4-20 minutes
                        'videoDefinition': 'high',
                        'order': 'relevance',
                        'maxResults': 10,  # 10 per query = 50 total
                        'key': api_key,
                        'videoLicense': 'any',
                        'videoEmbeddable': 'true'
                    }
                    
                    async with session.get(settings.youtube_search_api_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            videos = data.get('items', [])
                            
                            # Filter for educational channels and high-quality content
                            for video in videos:
                                snippet = video.get('snippet', {})
                                channel_title = snippet.get('channelTitle', '').lower()
                                video_title = snippet.get('title', '').lower()
                                
                                # Prioritize known educational channels and institutions
                                if any(edu_indicator in channel_title for edu_indicator in [
                                    'university', 'college', 'institute', 'academy', 'education',
                                    'pmi', 'project management', 'coursera', 'edx', 'learning',
                                    'training', 'certification', 'professional'
                                ]) or any(quality_indicator in video_title for quality_indicator in [
                                    'course', 'tutorial', 'certification', 'training', 'masterclass',
                                    'complete guide', 'fundamentals', 'professional'
                                ]):
                                    all_videos.append(video)
                        
                        # Small delay to respect rate limits
                        await asyncio.sleep(0.1)
                
                return all_videos[:50]  # Return top 50 educational videos
                
            except Exception as e:
                print(f"Error fetching YouTube videos: {e}")
                return []


class OpenCourseWareAPI:
    """Integration with MIT OpenCourseWare and other open educational resources."""
    
    @staticmethod
    async def fetch_mit_courses() -> List[Dict[str, Any]]:
        """Fetch MIT project management courses."""
        async with aiohttp.ClientSession() as session:
            try:
                # MIT OCW API
                params = {
                    'search': 'project management',
                    'format': 'json'
                }
                
                async with session.get(settings.mit_ocw_api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('results', [])
                    return []
            except Exception as e:
                print(f"Error fetching MIT OCW courses: {e}")
                return []


class EducationalContentService:
    """Main service to aggregate content from multiple educational providers."""
    
    def __init__(self):
        self.providers = {
            'coursera': CourseraAPI,
            'edx': EdXAPI,
            'futurelearn': FutureLearnAPI,
            'khan_academy': KhanAcademyAPI,
            'youtube': YouTubeEduAPI,
            'mit_ocw': OpenCourseWareAPI
        }
    
    async def fetch_all_pm_content(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch project management content from all providers."""
        content = {}
        
        tasks = [
            self._fetch_coursera_content(),
            self._fetch_edx_content(),
            self._fetch_futurelearn_content(),
            self._fetch_khan_academy_content(),
            self._fetch_youtube_content(),
            self._fetch_mit_content()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        content['coursera'] = results[0] if not isinstance(results[0], Exception) else []
        content['edx'] = results[1] if not isinstance(results[1], Exception) else []
        content['futurelearn'] = results[2] if not isinstance(results[2], Exception) else []
        content['khan_academy'] = results[3] if not isinstance(results[3], Exception) else []
        content['youtube'] = results[4] if not isinstance(results[4], Exception) else []
        content['mit_ocw'] = results[5] if not isinstance(results[5], Exception) else []
        
        return content
    
    async def _fetch_coursera_content(self) -> List[Dict[str, Any]]:
        """Fetch Coursera content."""
        return await CourseraAPI.fetch_pm_courses()
    
    async def _fetch_edx_content(self) -> List[Dict[str, Any]]:
        """Fetch edX content."""
        return await EdXAPI.fetch_pm_courses()
    
    async def _fetch_futurelearn_content(self) -> List[Dict[str, Any]]:
        """Fetch FutureLearn content."""
        return await FutureLearnAPI.fetch_pm_courses()
    
    async def _fetch_khan_academy_content(self) -> List[Dict[str, Any]]:
        """Fetch Khan Academy content."""
        return await KhanAcademyAPI.fetch_business_content()
    
    async def _fetch_youtube_content(self) -> List[Dict[str, Any]]:
        """Fetch YouTube educational content."""
        youtube_api_key = getattr(settings, 'youtube_api_key', None)
        if youtube_api_key:
            return await YouTubeEduAPI.fetch_pm_videos(youtube_api_key)
        else:
            print("YouTube API key not configured - skipping YouTube content")
            return []
    
    async def _fetch_mit_content(self) -> List[Dict[str, Any]]:
        """Fetch MIT OCW content."""
        return await OpenCourseWareAPI.fetch_mit_courses()
    
    def normalize_course_data(self, raw_content: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Normalize course data from different providers into a standard format."""
        normalized_courses = []
        
        # Normalize Coursera courses
        for course in raw_content.get('coursera', []):
            normalized_courses.append({
                'id': f"coursera_{course.get('id')}",
                'title': course.get('name', ''),
                'description': course.get('description', ''),
                'provider': 'Coursera',
                'url': f"https://www.coursera.org/learn/{course.get('slug', '')}",
                'image_url': course.get('photoUrl', ''),
                'duration_weeks': self._parse_duration(course.get('workload', '')),
                'difficulty_level': self._parse_difficulty(course.get('description', '')),
                'language': course.get('language', 'en'),
                'is_free': course.get('priceDetails', {}).get('amount', 0) == 0,
                'skills': self._extract_skills_from_description(course.get('description', '')),
                'rating': course.get('averageRating', 0),
                'enrollment_count': course.get('enrollmentCount', 0)
            })
        
        # Normalize edX courses
        for course in raw_content.get('edx', []):
            normalized_courses.append({
                'id': f"edx_{course.get('course_id')}",
                'title': course.get('name', ''),
                'description': course.get('short_description', ''),
                'provider': 'edX',
                'url': f"https://www.edx.org{course.get('course_about_url', '')}",
                'image_url': course.get('media', {}).get('course_image', {}).get('uri', ''),
                'duration_weeks': self._parse_duration(course.get('effort', '')),
                'difficulty_level': self._map_edx_level(course.get('level_type', '')),
                'language': course.get('language', 'en'),
                'is_free': course.get('price', 0) == 0,
                'skills': course.get('subjects', []),
                'rating': 0,  # edX doesn't provide ratings in this API
                'enrollment_count': course.get('enrollment_count', 0)
            })
        
        # Normalize YouTube content
        for video in raw_content.get('youtube', []):
            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            
            normalized_courses.append({
                'id': f"youtube_{video.get('id', {}).get('videoId')}",
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'provider': 'YouTube Education',
                'url': f"https://www.youtube.com/watch?v={video.get('id', {}).get('videoId')}",
                'image_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'duration_weeks': 1,  # Videos are typically shorter
                'difficulty_level': self._parse_difficulty(snippet.get('description', '')),
                'language': snippet.get('defaultLanguage', 'en'),
                'is_free': True,
                'skills': self._extract_skills_from_description(snippet.get('description', '')),
                'rating': 0,  # Would need additional API call
                'enrollment_count': int(statistics.get('viewCount', 0))
            })
        
        # Normalize MIT OCW courses
        for course in raw_content.get('mit_ocw', []):
            normalized_courses.append({
                'id': f"mit_{course.get('id')}",
                'title': course.get('title', ''),
                'description': course.get('description', ''),
                'provider': 'MIT OpenCourseWare',
                'url': course.get('url', ''),
                'image_url': '',  # MIT OCW doesn't always have images
                'duration_weeks': self._estimate_mit_duration(course.get('title', '')),
                'difficulty_level': 4,  # MIT courses are generally advanced
                'language': 'en',
                'is_free': True,
                'skills': course.get('topics', []),
                'rating': 0,
                'enrollment_count': 0
            })
        
        return normalized_courses
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string and return weeks."""
        if not duration_str:
            return 4  # Default
        
        duration_str = duration_str.lower()
        if 'week' in duration_str:
            try:
                return int(''.join(filter(str.isdigit, duration_str.split('week')[0])))
            except:
                return 4
        elif 'month' in duration_str:
            try:
                months = int(''.join(filter(str.isdigit, duration_str.split('month')[0])))
                return months * 4
            except:
                return 4
        return 4
    
    def _parse_difficulty(self, description: str) -> int:
        """Parse difficulty level from description."""
        description = description.lower()
        if any(word in description for word in ['beginner', 'intro', 'basic', 'fundamentals']):
            return 1
        elif any(word in description for word in ['intermediate', 'moderate']):
            return 2
        elif any(word in description for word in ['advanced', 'expert', 'professional']):
            return 3
        return 2  # Default to intermediate
    
    def _map_edx_level(self, level: str) -> int:
        """Map edX level to our difficulty scale."""
        level_map = {
            'introductory': 1,
            'intermediate': 2,
            'advanced': 3
        }
        return level_map.get(level.lower(), 2)
    
    def _estimate_mit_duration(self, title: str) -> int:
        """Estimate MIT course duration based on title patterns."""
        if any(word in title.lower() for word in ['introduction', 'intro', 'fundamentals']):
            return 8
        elif any(word in title.lower() for word in ['advanced', 'graduate']):
            return 12
        return 10
    
    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract relevant PM skills from course description."""
        pm_skills = [
            'project management', 'agile', 'scrum', 'kanban', 'waterfall',
            'risk management', 'stakeholder management', 'budget management',
            'time management', 'team leadership', 'communication', 'planning',
            'scheduling', 'quality management', 'procurement', 'integration',
            'scope management', 'cost management', 'pmp', 'prince2', 'lean',
            'six sigma', 'change management', 'resource management'
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in pm_skills:
            if skill in description_lower:
                found_skills.append(skill.title())
        
        return found_skills[:5]  # Limit to 5 skills


# Global instance
education_content_service = EducationalContentService()