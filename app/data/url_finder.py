"""
URL Finder - Discovers and validates company website URLs
Finds correct URLs for companies before scraping
"""

import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
from app.core.logging import get_logger
import os
import time

logger = get_logger(__name__)


class URLFinder:
    """Finds and validates company website URLs"""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize URL finder
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (TBAML-System/1.0) Compatible Bot"
        })
        
        # Common domain patterns to try
        self.domain_patterns = [
            "com",
            "org",
            "net",
            "co.uk",  # UK companies
            "co",  # Generic
            "ru",  # Russian companies
            "de",  # German companies
            "fr",  # French companies
            "it",  # Italian companies
            "nl",  # Netherlands companies
            "ch",  # Swiss companies
            "sg",  # Singapore companies
        ]
    
    def find_company_url(
        self,
        company_name: str,
        country: str = "US"
    ) -> Optional[Dict[str, Any]]:
        """
        Find company website URL
        
        Args:
            company_name: Name of the company
            country: Country code
        
        Returns:
            Dictionary with URL and validation info, or None if not found
        """
        logger.info(f"Finding URL for: {company_name} ({country})")
        
        # Strategy 1: Try common domain patterns (fast, free, no API needed)
        logger.debug(f"Strategy 1: Trying common domain patterns for {company_name}")
        candidate_urls = self._generate_candidate_urls(company_name, country)
        
        # Test each candidate
        for url in candidate_urls:
            result = self._validate_url(url, company_name)
            if result and result.get("valid"):
                logger.info(f"Found valid URL via domain patterns: {url}")
                return result
        
        # Strategy 2: Try company name variations (handles abbreviations, suffixes)
        logger.debug(f"Strategy 2: Trying name variations for {company_name}")
        variations = self._generate_name_variations(company_name)
        for variation in variations:
            # Skip if variation is same as original (already tried)
            if variation.lower() == company_name.lower():
                continue
                
            candidate_urls = self._generate_candidate_urls(variation, country)
            for url in candidate_urls:
                result = self._validate_url(url, company_name)
                if result and result.get("valid"):
                    logger.info(f"Found valid URL with variation '{variation}': {url}")
                    return result
        
        # Strategy 3 (FALLBACK): Try web search API (Tavily) - only if other methods fail
        # This is more expensive (API calls) and slower, so use as fallback
        logger.debug(f"Strategy 3 (Fallback): Trying web search API for {company_name}")
        search_result = self._search_for_url(company_name, country)
        if search_result and search_result.get("valid"):
            logger.info(f"Found URL via web search API (fallback): {search_result.get('url')}")
            return search_result
        
        logger.warning(f"Could not find valid URL for: {company_name} (all strategies exhausted)")
        return None
    
    def _generate_candidate_urls(
        self,
        company_name: str,
        country: str
    ) -> List[str]:
        """
        Generate candidate URLs based on company name
        
        Args:
            company_name: Company name
            country: Country code
        
        Returns:
            List of candidate URLs
        """
        candidates = []
        
        # Clean company name for URL
        clean_name = company_name.lower()
        # Remove common suffixes
        clean_name = clean_name.replace(" inc", "").replace(" ltd", "")
        clean_name = clean_name.replace(" corporation", "").replace(" corp", "")
        clean_name = clean_name.replace(" plc", "").replace(" oao", "")
        clean_name = clean_name.replace(" group", "").replace(" company", "")
        clean_name = clean_name.replace(" oil company", "").replace(" energy group", "")
        clean_name = clean_name.replace(" co", "").replace("(", "").replace(")", "")
        clean_name = clean_name.strip()
        
        # Handle special cases for known companies
        special_cases = {
            "rosneft oil company": "rosneft",
            "bp (british petroleum)": "bp",
            "british petroleum": "bp",
            "mercuria energy group": "mercuria",
            "gazprom neft": "gazprom-neft",
            "surgutneftegas": "surgutneftegas",
            "exxon mobil": "exxonmobil",
            "exxon mobil corporation": "exxonmobil",
            "total energies": "totalenergies",
            "total energies se": "totalenergies",
            "lukoil oao": "lukoil",
            "lukoil oao (lukoil)": "lukoil"
        }
        
        if clean_name in special_cases:
            clean_name = special_cases[clean_name]
        
        # Remove spaces and special characters
        url_name = clean_name.replace(" ", "").replace(".", "").replace("-", "")
        url_name_with_dashes = clean_name.replace(" ", "-").replace(".", "-")
        url_name_with_dots = clean_name.replace(" ", ".")
        
        # Country-specific domain suggestions
        country_domains = {
            "US": ["com"],
            "GB": ["co.uk", "com", "org"],
            "RU": ["ru", "com"],
            "FR": ["fr", "com"],
            "IT": ["it", "com"],
            "NL": ["nl", "com"],
            "CH": ["ch", "com"],
            "SG": ["sg", "com"]
        }
        
        preferred_domains = country_domains.get(country.upper(), ["com", "org"])
        
        # Generate URLs with preferred domains first
        for domain in preferred_domains + self.domain_patterns:
            if domain not in preferred_domains:  # Already added
                continue
            candidates.extend([
                f"https://www.{url_name}.{domain}",
                f"https://{url_name}.{domain}",
                f"https://www.{url_name_with_dashes}.{domain}",
                f"https://{url_name_with_dashes}.{domain}",
            ])
        
        # Add common patterns
        for domain in ["com", "org", "net"]:
            if domain not in preferred_domains:
                candidates.extend([
                    f"https://www.{url_name}.{domain}",
                    f"https://{url_name}.{domain}",
                ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for url in candidates:
            if url not in seen:
                seen.add(url)
                unique_candidates.append(url)
        
        return unique_candidates
    
    def _validate_url(
        self,
        url: str,
        company_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate if URL exists and is likely the company website
        
        Args:
            url: URL to validate
            company_name: Company name for verification
        
        Returns:
            Dictionary with validation result or None
        """
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            # If HEAD fails, try GET
            if response.status_code >= 400:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    stream=True
                )
            
            # Check if URL is accessible
            if response.status_code == 200:
                final_url = response.url
                
                # Extract page title/content to verify it's the right company
                # (quick check - look for company name in response)
                content_check = self._verify_company_match(final_url, company_name)
                
                return {
                    "url": final_url,
                    "valid": True,
                    "status_code": response.status_code,
                    "company_match": content_check,
                    "confidence": "high" if content_check else "medium"
                }
            
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout checking URL: {url}")
        except requests.exceptions.ConnectionError:
            logger.debug(f"Connection error for URL: {url}")
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request error for {url}: {str(e)}")
        except Exception as e:
            logger.debug(f"Error validating {url}: {str(e)}")
        
        return None
    
    def _verify_company_match(
        self,
        url: str,
        company_name: str
    ) -> bool:
        """
        Quick verification if URL matches company
        
        Args:
            url: URL to check
            company_name: Company name
        
        Returns:
            True if likely match
        """
        try:
            # Get page content
            response = self.session.get(
                url,
                timeout=5,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                content = response.text.lower()
                company_lower = company_name.lower()
                
                # Extract key words from company name
                company_words = [w for w in company_lower.split() if len(w) > 3]
                
                # Check if company name appears in content (basic check)
                for word in company_words:
                    if word in content:
                        return True
            
        except Exception:
            pass  # If we can't verify, return False
        
        return False
    
    def _search_for_url(
        self,
        company_name: str,
        country: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search for company URL using web search API (Tavily) as fallback
        
        This method is called only after domain pattern matching and name variations
        have failed. It uses Tavily API which requires an API key.
        
        Args:
            company_name: Company name
            country: Country code
        
        Returns:
            Dictionary with search result or None
        """
        # Check if Tavily API key is available
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        
        if not tavily_api_key:
            logger.debug(f"Tavily API key not configured - skipping web search fallback")
            return None
        
        try:
            # Construct search query for official website
            search_query = f"{company_name} official website {country}"
            logger.debug(f"Searching Tavily API: {search_query}")
            
            response = self.session.get(
                "https://api.tavily.com/search",
                params={
                    "api_key": tavily_api_key,
                    "query": search_query,
                    "search_depth": "basic",
                    "max_results": 5  # Get more results for better matching
                },
                timeout=15  # Longer timeout for API calls
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    logger.debug(f"No results from Tavily API for: {company_name}")
                    return None
                
                logger.debug(f"Tavily API returned {len(results)} results")
                
                # Try each result until we find a valid match
                for i, result in enumerate(results[:5], 1):  # Check top 5 results
                    url = result.get("url")
                    title = result.get("title", "")
                    
                    if not url:
                        continue
                    
                    logger.debug(f"Validating Tavily result {i}/{len(results)}: {url}")
                    
                    # Validate the found URL
                    validated = self._validate_url(url, company_name)
                    if validated and validated.get("valid"):
                        logger.info(
                            f"Found valid URL via Tavily API (result {i})",
                            url=url,
                            title=title[:50]
                        )
                        return validated
                    else:
                        logger.debug(f"Tavily result {i} failed validation: {url}")
                
                logger.warning(f"Tavily API returned results but none validated for: {company_name}")
            elif response.status_code == 401:
                logger.warning("Tavily API key is invalid or expired")
            elif response.status_code == 429:
                logger.warning("Tavily API rate limit exceeded - consider upgrading plan")
            else:
                logger.warning(f"Tavily API returned status {response.status_code}: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            logger.warning("Tavily API request timed out - check network connection")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Tavily API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Tavily search: {str(e)}", exc_info=True)
        
        return None
    
    def _generate_name_variations(self, company_name: str) -> List[str]:
        """
        Generate variations of company name
        
        Args:
            company_name: Original company name
        
        Returns:
            List of name variations
        """
        variations = [company_name]
        
        # Remove common suffixes/parentheses
        clean = company_name.replace(" (British Petroleum)", "").replace(" (Rosneft)", "")
        clean = clean.replace(" OAO", "").replace(" Inc", "").replace(" Ltd", "")
        clean = clean.replace(" plc", "").replace(" Corp", "").replace(" Corporation", "")
        clean = clean.replace(" Group", "").replace(" Company", "").replace(" Oil Company", "")
        variations.append(clean.strip())
        
        # Try without parentheses content
        if "(" in company_name and ")" in company_name:
            without_parens = company_name.split("(")[0].strip()
            variations.append(without_parens)
            
            # Also try content inside parentheses
            import re
            parens_content = re.findall(r'\(([^)]+)\)', company_name)
            for content in parens_content:
                variations.append(content.strip())
        
        # Handle special abbreviations
        abbreviation_map = {
            "bp": "bp",
            "rosneft": "rosneft",
            "lukoil": "lukoil",
            "exxon mobil": "exxonmobil",
            "total energies": "totalenergies"
        }
        
        clean_lower = clean.lower().strip()
        if clean_lower in abbreviation_map:
            variations.append(abbreviation_map[clean_lower])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            var_lower = var.lower().strip()
            if var_lower and var_lower not in seen:
                seen.add(var_lower)
                unique_variations.append(var)
        
        return unique_variations
    
    def batch_find_urls(
        self,
        companies: List[Dict[str, Any]],
        delay: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Find URLs for multiple companies
        
        Args:
            companies: List of company dictionaries
            Each dict should have: name, country (optional)
        delay: Delay between requests in seconds
        
        Returns:
            List of companies with found URLs
        """
        results = []
        
        logger.info(f"Finding URLs for {len(companies)} companies")
        
        for i, company in enumerate(companies, 1):
            company_name = company.get("name", "")
            country = company.get("country", "US")
            
            print(f"\n[{i}/{len(companies)}] Finding URL for: {company_name}")
            
            url_result = self.find_company_url(company_name, country)
            
            if url_result and url_result.get("valid"):
                company["url"] = url_result["url"]
                company["url_confidence"] = url_result.get("confidence", "medium")
                company["url_found"] = True
                print(f"  ✓ Found: {url_result['url']} (confidence: {url_result.get('confidence', 'medium')})")
            else:
                company["url"] = None
                company["url_found"] = False
                print(f"  ⚠ Could not find valid URL")
            
            results.append(company)
            
            # Delay between requests
            if i < len(companies):
                time.sleep(delay)
        
        found_count = sum(1 for c in results if c.get("url_found"))
        print(f"\n✓ Found URLs for {found_count}/{len(companies)} companies")
        
        return results

