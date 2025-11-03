"""
Web scraping module with rate limiting
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
from app.data.base import DataSource, DataCollectionResult
from app.data.url_finder import URLFinder
from app.core.logging import get_logger
import os

logger = get_logger(__name__)


class WebScraper(DataSource):
    """Web scraping data source with rate limiting"""
    
    def __init__(
        self,
        name: str = "web_scraper",
        rate_limit: int = 10,
        timeout: int = 30,
        user_agent: Optional[str] = None
    ):
        """
        Initialize web scraper
        
        Args:
            name: Name of the scraper
            rate_limit: Maximum requests per minute
            timeout: Request timeout in seconds
            user_agent: User agent string (uses default if None)
        """
        super().__init__(name, rate_limit)
        self.timeout = timeout
        self.user_agent = user_agent or os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (TBAML-System/1.0) Compatible Bot"
        )
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent
        })
        # Initialize URL finder for automatic website discovery
        self.url_finder = URLFinder(timeout=self.timeout)
    
    def fetch_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from web sources
        
        Args:
            query: Query parameters containing:
                - client: Company name
                - client_country: Country code
                - url: Optional specific URL to scrape
        
        Returns:
            Dictionary containing scraped data
        """
        self._rate_limit_check()
        
        client = query.get("client", "")
        client_country = query.get("client_country", "")
        url = query.get("url")
        
        result_data = {
            "client": client,
            "client_country": client_country,
            "sources": []
        }
        
        # If URL is provided, scrape it directly
        if url:
            try:
                scraped_data = self._scrape_url(url)
                if scraped_data:
                    result_data["sources"].append(scraped_data)
            except Exception as e:
                logger.error(f"Error scraping URL {url}", error=str(e))
        
        # Search for company website and scrape
        else:
            # Try common website patterns
            company_website = self._find_company_website(client, client_country)
            if company_website:
                try:
                    scraped_data = self._scrape_url(company_website)
                    if scraped_data:
                        result_data["sources"].append(scraped_data)
                except Exception as e:
                    logger.error(f"Error scraping company website", 
                               url=company_website, error=str(e))
        
        return result_data
    
    def _scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
        
        Returns:
            Dictionary with scraped content or None
        """
        try:
            logger.info(f"Scraping URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            
            # Extract links (for finding company info pages)
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                if text and href:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, href)
                    links.append({
                        "url": absolute_url,
                        "text": text
                    })
            
            return {
                "url": url,
                "title": title_text,
                "description": description,
                "content": text[:5000],  # Limit content length
                "content_length": len(text),
                "links": links[:20],  # Limit number of links
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}", error=str(e))
            return None
        except Exception as e:
            logger.error(f"Error scraping {url}", error=str(e))
            return None
    
    def _find_company_website(
        self,
        company_name: str,
        country: str
    ) -> Optional[str]:
        """
        Attempt to find company website URL automatically
        
        Uses multiple strategies:
        1. Try common domain patterns (www.companyname.com, etc.)
        2. Use web search API (Tavily) if available
        3. Try company name variations
        4. Validate URLs to ensure they exist and match the company
        
        Args:
            company_name: Name of the company
            country: Country code
        
        Returns:
            Potential company website URL or None if not found
        """
        try:
            logger.info(f"Attempting to find website for: {company_name} ({country})")
            
            # Use URLFinder to discover website
            url_result = self.url_finder.find_company_url(company_name, country)
            
            if url_result and url_result.get("valid"):
                found_url = url_result.get("url")
                confidence = url_result.get("confidence", "medium")
                logger.info(
                    f"Found company website",
                    company=company_name,
                    url=found_url,
                    confidence=confidence
                )
                return found_url
            else:
                logger.warning(f"Could not find website for: {company_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding company website", company=company_name, error=str(e))
            return None
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped data
        
        Args:
            data: Data to validate
        
        Returns:
            True if data is valid
        """
        if not data:
            return False
        
        # Check if we have at least one source
        sources = data.get("sources", [])
        if not sources:
            return False
        
        # Check if sources have required fields
        for source in sources:
            if not source.get("url"):
                return False
        
        return True
    
    def __del__(self):
        """Cleanup session"""
        if hasattr(self, 'session'):
            self.session.close()

