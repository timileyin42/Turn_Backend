"""
Company Website Scanner Service
Scans company websites for job openings (especially entry-level roles for startups/SMEs)
and extracts key hiring contact information (CEO, HR, founders).
"""
import aiohttp
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

from app.core.logger import logger
from app.services.ai_service import ai_service, AICoachingType


class CompanyWebsiteScanner:
    """
    Scans company websites to find:
    1. Job openings (especially entry-level roles)
    2. CEO/Founder contact information
    3. HR/Recruiting contact information
    4. Company size and type (startup/SME classification)
    """
    
    def __init__(self):
        self.logger = logger
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Common career page patterns
        self.career_page_patterns = [
            '/careers', '/jobs', '/join-us', '/work-with-us', '/opportunities',
            '/hiring', '/team', '/open-positions', '/career', '/about/jobs',
            '/company/careers', '/we-are-hiring', '/join'
        ]
        
        # Entry-level job indicators
        self.entry_level_keywords = [
            'entry level', 'entry-level', 'junior', 'associate', 'graduate',
            'trainee', 'intern', 'internship', 'fresh graduate', 'early career',
            'new grad', 'starting', 'beginner', '0-2 years', '0-1 years'
        ]
        
        # Startup/SME indicators
        self.startup_indicators = [
            'startup', 'founded', 'seed', 'series a', 'series b', 'venture',
            'small team', 'growing team', 'early stage', 'bootstrapped',
            '< 50 employees', 'team of', 'agile environment'
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': 'TURN-Job-Matcher-Bot/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def scan_company_website(
        self,
        company_url: str,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Comprehensive scan of a company website.
        
        Args:
            company_url: Company website URL
            company_name: Company name
            
        Returns:
            Dictionary with:
            - career_page_url: URL to careers page
            - job_listings: List of found job listings
            - entry_level_jobs: List of entry-level positions
            - ceo_contact: CEO email/LinkedIn if found
            - hr_contact: HR contact email if found
            - is_startup: Whether company appears to be startup/SME
            - company_size_estimate: Estimated company size
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': 'TURN-Job-Matcher-Bot/1.0'}
            )
        
        try:
            # Normalize URL
            if not company_url.startswith(('http://', 'https://')):
                company_url = f'https://{company_url}'
            
            # 1. Find career page
            career_page_url = await self._find_career_page(company_url)
            
            # 2. Scrape job listings from career page
            job_listings = []
            entry_level_jobs = []
            if career_page_url:
                jobs = await self._scrape_job_listings(career_page_url, company_name)
                job_listings = jobs.get('all_jobs', [])
                entry_level_jobs = jobs.get('entry_level_jobs', [])
            
            # 3. Find contact information
            contacts = await self._find_company_contacts(company_url, company_name)
            
            # 4. Determine if startup/SME
            is_startup, company_size = await self._classify_company_size(
                company_url, company_name
            )
            
            return {
                'company_name': company_name,
                'company_url': company_url,
                'career_page_url': career_page_url,
                'job_listings': job_listings,
                'entry_level_jobs': entry_level_jobs,
                'total_jobs_found': len(job_listings),
                'entry_level_count': len(entry_level_jobs),
                'ceo_contact': contacts.get('ceo'),
                'hr_contact': contacts.get('hr'),
                'founders': contacts.get('founders', []),
                'is_startup': is_startup,
                'is_sme': company_size in ['startup', 'small', 'medium'],
                'company_size_estimate': company_size,
                'scan_timestamp': datetime.utcnow().isoformat(),
                'scan_success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error scanning {company_url}: {str(e)}")
            return {
                'company_name': company_name,
                'company_url': company_url,
                'scan_success': False,
                'error': str(e),
                'scan_timestamp': datetime.utcnow().isoformat()
            }
    
    async def _find_career_page(self, base_url: str) -> Optional[str]:
        """Find the careers/jobs page URL."""
        try:
            # Try common career page patterns
            for pattern in self.career_page_patterns:
                test_url = urljoin(base_url, pattern)
                if await self._url_exists(test_url):
                    return test_url
            
            # Fallback: scrape homepage for career links
            async with self.session.get(base_url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for links with career-related text
                    for link in soup.find_all('a', href=True):
                        link_text = link.get_text().lower()
                        link_href = link['href'].lower()
                        
                        if any(keyword in link_text or keyword in link_href 
                               for keyword in ['career', 'job', 'hiring', 'join', 'team']):
                            full_url = urljoin(base_url, link['href'])
                            if await self._url_exists(full_url):
                                return full_url
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding career page for {base_url}: {str(e)}")
            return None
    
    async def _url_exists(self, url: str) -> bool:
        """Check if URL exists and returns 200."""
        try:
            async with self.session.head(url, timeout=5, allow_redirects=True) as response:
                return response.status == 200
        except:
            return False
    
    async def _scrape_job_listings(
        self,
        career_page_url: str,
        company_name: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape job listings from career page."""
        all_jobs = []
        entry_level_jobs = []
        
        try:
            async with self.session.get(career_page_url, timeout=15) as response:
                if response.status != 200:
                    return {'all_jobs': [], 'entry_level_jobs': []}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Common job listing selectors
                job_selectors = [
                    ('div', {'class': re.compile(r'job|position|opening|role|listing')}),
                    ('li', {'class': re.compile(r'job|position|opening|role')}),
                    ('article', {'class': re.compile(r'job|position')}),
                    ('a', {'class': re.compile(r'job|position')})
                ]
                
                job_elements = []
                for tag, attrs in job_selectors:
                    found = soup.find_all(tag, attrs)
                    if found:
                        job_elements.extend(found)
                
                # Extract job information
                for element in job_elements[:50]:  # Limit to 50 jobs
                    job_data = self._extract_job_data(element, career_page_url, company_name)
                    if job_data:
                        all_jobs.append(job_data)
                        
                        # Check if entry-level
                        if self._is_entry_level_job(job_data):
                            entry_level_jobs.append(job_data)
                
                # If no structured listings found, use AI to parse
                if not all_jobs:
                    all_jobs, entry_level_jobs = await self._ai_parse_job_page(
                        html, company_name
                    )
                
            return {
                'all_jobs': all_jobs,
                'entry_level_jobs': entry_level_jobs
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping jobs from {career_page_url}: {str(e)}")
            return {'all_jobs': [], 'entry_level_jobs': []}
    
    def _extract_job_data(
        self,
        element: Any,
        base_url: str,
        company_name: str
    ) -> Optional[Dict[str, Any]]:
        """Extract job data from HTML element."""
        try:
            # Try to find job title
            title = None
            title_selectors = ['h2', 'h3', 'h4', 'a', 'strong']
            for selector in title_selectors:
                title_elem = element.find(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    if len(title) > 5:  # Valid title
                        break
            
            if not title:
                title = element.get_text().strip()[:100]
            
            if not title or len(title) < 5:
                return None
            
            # Try to find link
            link = element.find('a')
            job_url = urljoin(base_url, link['href']) if link and link.get('href') else base_url
            
            # Try to find location
            location = "Remote/Onsite"
            location_patterns = re.compile(r'location|where|city|country|remote', re.I)
            location_elem = element.find(string=location_patterns)
            if location_elem:
                location = location_elem.strip()
            
            # Try to find description
            description = element.get_text().strip()[:500]
            
            return {
                'title': title,
                'company': company_name,
                'location': location,
                'description': description,
                'url': job_url,
                'source': 'company_website',
                'posted_date': datetime.utcnow().isoformat(),
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting job data from element: {str(e)}")
            return None
    
    def _is_entry_level_job(self, job_data: Dict[str, Any]) -> bool:
        """Determine if job is entry-level."""
        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')}".lower()
        
        # Check for entry-level keywords
        if any(keyword in job_text for keyword in self.entry_level_keywords):
            return True
        
        # Check if NOT senior/lead/principal
        senior_keywords = ['senior', 'sr.', 'lead', 'principal', 'director', 'head of', 'vp', 'chief']
        has_senior = any(keyword in job_text for keyword in senior_keywords)
        
        # If no senior keywords and has project manager related terms
        pm_keywords = ['project manager', 'program manager', 'product manager', 'pm']
        has_pm = any(keyword in job_text for keyword in pm_keywords)
        
        return has_pm and not has_senior
    
    async def _ai_parse_job_page(
        self,
        html_content: str,
        company_name: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Use AI to parse job listings from unstructured HTML."""
        try:
            # Extract text from HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()[:5000]  # Limit for AI processing
            
            prompt = f"""
            Parse this careers page content and extract job listings for {company_name}.
            Focus on finding entry-level and junior positions suitable for project managers.
            
            Content:
            {text_content}
            
            Return JSON array of jobs with format:
            [{{"title": "Job Title", "location": "Location", "is_entry_level": true/false, "description": "brief desc"}}]
            
            If no clear jobs found, return empty array [].
            """
            
            # Use AI service to parse job listings
            ai_response = await ai_service.generate_response(
                prompt=prompt,
                context="Extract structured job listings from unstructured careers page content",
                coaching_type=AICoachingType.GENERAL
            )
            
            if not ai_response or not ai_response.get('success'):
                self.logger.warning(f"AI service failed to parse jobs for {company_name}")
                return [], []
            
            # Parse AI response
            response_text = ai_response.get('response', '[]')
            
            # Try to extract JSON from response (handle cases where AI adds explanation)
            try:
                # Look for JSON array in response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    jobs_data = json.loads(json_match.group(0))
                else:
                    jobs_data = json.loads(response_text)
                
                if not isinstance(jobs_data, list):
                    return [], []
                
                # Process parsed jobs
                all_jobs = []
                entry_level_jobs = []
                
                for job in jobs_data:
                    if not isinstance(job, dict) or 'title' not in job:
                        continue
                    
                    job_entry = {
                        'title': job.get('title', 'Unknown Position'),
                        'company': company_name,
                        'location': job.get('location', 'Not specified'),
                        'description': job.get('description', ''),
                        'url': '',  # Will be set by caller
                        'source': 'company_website_ai_parsed',
                        'posted_date': datetime.utcnow().isoformat(),
                        'scraped_at': datetime.utcnow().isoformat()
                    }
                    
                    all_jobs.append(job_entry)
                    
                    # Check if marked as entry-level or matches entry-level criteria
                    if job.get('is_entry_level') or self._is_entry_level_job(job_entry):
                        entry_level_jobs.append(job_entry)
                
                self.logger.info(
                    f"AI parsed {len(all_jobs)} jobs for {company_name}, "
                    f"{len(entry_level_jobs)} entry-level"
                )
                
                return all_jobs, entry_level_jobs
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                self.logger.debug(f"AI response was: {response_text[:200]}")
                return [], []
            
        except Exception as e:
            self.logger.error(f"Error in AI job parsing: {str(e)}")
            return [], []
    
    async def _find_company_contacts(
        self,
        company_url: str,
        company_name: str
    ) -> Dict[str, Any]:
        """Find CEO, HR, and founder contact information."""
        contacts = {
            'ceo': None,
            'hr': None,
            'founders': []
        }
        
        try:
            # 1. Check About/Team pages
            about_contacts = await self._scrape_about_team_pages(company_url)
            contacts.update(about_contacts)
            
            # 2. Check contact page
            contact_page_info = await self._scrape_contact_page(company_url)
            if contact_page_info.get('hr_email'):
                contacts['hr'] = contact_page_info['hr_email']
            
            # 3. Try common email patterns (for very small startups)
            if not contacts['ceo'] and not contacts['hr']:
                guessed_emails = self._guess_company_emails(company_url, company_name)
                contacts['guessed_contacts'] = guessed_emails
            
            return contacts
            
        except Exception as e:
            self.logger.error(f"Error finding contacts for {company_url}: {str(e)}")
            return contacts
    
    async def _scrape_about_team_pages(self, base_url: str) -> Dict[str, Any]:
        """Scrape About/Team pages for leadership contacts."""
        contacts = {}
        
        about_patterns = ['/about', '/team', '/about-us', '/company', '/leadership', '/founders']
        
        for pattern in about_patterns:
            try:
                page_url = urljoin(base_url, pattern)
                async with self.session.get(page_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        text = soup.get_text().lower()
                        
                        # Look for CEO/Founder mentions with emails
                        ceo_patterns = [
                            r'ceo[:\s]+([a-zA-Z\s]+)',
                            r'chief executive officer[:\s]+([a-zA-Z\s]+)',
                            r'founder[:\s]+([a-zA-Z\s]+)',
                            r'co-founder[:\s]+([a-zA-Z\s]+)'
                        ]
                        
                        for pattern_regex in ceo_patterns:
                            match = re.search(pattern_regex, text, re.IGNORECASE)
                            if match:
                                name = match.group(1).strip()
                                # Try to find associated email
                                email_match = re.search(
                                    rf'{re.escape(name)}[\s\S]{{0,100}}([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})',
                                    text
                                )
                                if email_match:
                                    contacts['ceo'] = {
                                        'name': name,
                                        'email': email_match.group(1),
                                        'title': 'CEO/Founder'
                                    }
                                    break
                        
                        # Look for HR contacts
                        hr_emails = re.findall(
                            r'(hr@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|careers@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|recruiting@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                            text
                        )
                        if hr_emails:
                            contacts['hr'] = {
                                'email': hr_emails[0],
                                'title': 'HR/Recruiting'
                            }
                        
                        if contacts.get('ceo') and contacts.get('hr'):
                            break
                        
            except Exception as e:
                continue
        
        return contacts
    
    async def _scrape_contact_page(self, base_url: str) -> Dict[str, Any]:
        """Scrape contact page for emails."""
        contact_info = {}
        
        contact_patterns = ['/contact', '/contact-us', '/get-in-touch', '/reach-us']
        
        for pattern in contact_patterns:
            try:
                page_url = urljoin(base_url, pattern)
                async with self.session.get(page_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        text = soup.get_text()
                        
                        # Extract all emails
                        emails = re.findall(
                            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                            text
                        )
                        
                        # Categorize emails
                        for email in emails:
                            email_lower = email.lower()
                            if any(keyword in email_lower for keyword in ['hr', 'careers', 'recruiting', 'jobs']):
                                contact_info['hr_email'] = email
                            elif any(keyword in email_lower for keyword in ['ceo', 'founder', 'admin']):
                                contact_info['ceo_email'] = email
                            elif 'info' in email_lower or 'contact' in email_lower:
                                contact_info['general_email'] = email
                        
                        if contact_info:
                            break
                        
            except Exception as e:
                continue
        
        return contact_info
    
    def _guess_company_emails(self, company_url: str, company_name: str) -> Dict[str, List[str]]:
        """Guess common email patterns for startup/SME."""
        domain = urlparse(company_url).netloc.replace('www.', '')
        
        # Common email patterns for small companies
        hr_patterns = [
            f'hr@{domain}',
            f'careers@{domain}',
            f'jobs@{domain}',
            f'recruiting@{domain}',
            f'talent@{domain}'
        ]
        
        ceo_patterns = [
            f'ceo@{domain}',
            f'founder@{domain}',
            f'hello@{domain}',
            f'contact@{domain}',
            f'info@{domain}'
        ]
        
        return {
            'hr_guesses': hr_patterns,
            'ceo_guesses': ceo_patterns
        }
    
    async def _classify_company_size(
        self,
        company_url: str,
        company_name: str
    ) -> Tuple[bool, str]:
        """
        Classify if company is startup/SME and estimate size.
        
        Returns:
            (is_startup, size_category)
        """
        try:
            # Scrape homepage for company size indicators
            async with self.session.get(company_url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text().lower()
                    
                    # Check for startup indicators
                    startup_score = sum(1 for indicator in self.startup_indicators if indicator in text)
                    
                    # Check for team size mentions
                    team_size_patterns = [
                        r'(\d+)\s*(?:person|people|employee|team member|staff)',
                        r'team of\s*(\d+)',
                        r'(\d+)[\s-]*member team'
                    ]
                    
                    for pattern in team_size_patterns:
                        match = re.search(pattern, text)
                        if match:
                            size = int(match.group(1))
                            if size < 50:
                                return True, 'startup'
                            elif size < 250:
                                return True, 'small'
                            elif size < 1000:
                                return False, 'medium'
                            else:
                                return False, 'large'
                    
                    # If strong startup indicators, classify as startup
                    if startup_score >= 3:
                        return True, 'startup'
                    elif startup_score >= 1:
                        return True, 'small'
            
            # Default: assume SME if can't determine
            return True, 'small'
            
        except Exception as e:
            self.logger.error(f"Error classifying company size: {str(e)}")
            return True, 'small'  # Default to SME
    
    async def scan_multiple_companies(
        self,
        companies: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Scan multiple company websites in parallel.
        
        Args:
            companies: List of dicts with 'url' and 'name' keys
            
        Returns:
            List of scan results
        """
        tasks = [
            self.scan_company_website(company['url'], company['name'])
            for company in companies
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                self.logger.error(f"Company scan failed: {result}")
        
        return valid_results


# Global service instance
company_scanner_service = CompanyWebsiteScanner()
