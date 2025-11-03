"""
Company registry data fetcher
Fetches company information from public registries
"""

from typing import Dict, Any, Optional
from datetime import datetime
import requests
from app.data.base import DataSource, DataCollectionResult
from app.data.sec_parser import get_sec_parser
from app.core.logging import get_logger
import os

logger = get_logger(__name__)


class CompanyRegistryFetcher(DataSource):
    """Fetches company data from public registries"""
    
    def __init__(
        self,
        name: str = "company_registry",
        rate_limit: int = 5  # Lower rate limit for API calls
    ):
        """
        Initialize company registry fetcher
        
        Args:
            name: Name of the data source
            rate_limit: Maximum requests per minute
        """
        super().__init__(name, rate_limit)
        self.session = requests.Session()
    
    def fetch_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch company data from registries
        
        Args:
            query: Query parameters containing:
                - client: Company name
                - client_country: Country code
        
        Returns:
            Dictionary containing company registry data
        """
        self._rate_limit_check()
        
        company_name = query.get("client", "")
        country = query.get("client_country", "").upper()
        
        result_data = {
            "company_name": company_name,
            "country": country,
            "sources": [],
            "registry_data": {}
        }
        
        # Try different registries based on country
        if country == "US":
            registry_data = self._fetch_us_registry(company_name)
            if registry_data:
                result_data["registry_data"]["us"] = registry_data
                result_data["sources"].append("SEC EDGAR")
        
        elif country == "GB" or country == "UK":
            registry_data = self._fetch_uk_registry(company_name)
            if registry_data:
                result_data["registry_data"]["uk"] = registry_data
                result_data["sources"].append("Companies House")
        
        elif country == "AU":
            registry_data = self._fetch_au_registry(company_name)
            if registry_data:
                result_data["registry_data"]["au"] = registry_data
                result_data["sources"].append("ASIC")
        
        # Try OpenCorporates API if available
        opencorp_data = self._fetch_opencorporates(company_name, country)
        if opencorp_data:
            result_data["registry_data"]["opencorporates"] = opencorp_data
            result_data["sources"].append("OpenCorporates")
        
        return result_data
    
    def _fetch_us_registry(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from US SEC EDGAR using downloaded company tickers file
        
        Args:
            company_name: Company name
        
        Returns:
            Dictionary with company data or None
        """
        try:
            logger.info(f"Fetching US registry data for: {company_name}")
            
            # Get SEC parser instance (singleton, loads file once)
            parser = get_sec_parser()
            
            if not parser.loaded:
                logger.warning("SEC company tickers file not loaded")
                return None
            
            # Search for company
            # Try exact match first, then partial
            matches = parser.search_company(company_name, exact_match=False, use_ticker=True)
            
            if matches:
                # Return first matching company
                company = matches[0]
                
                logger.info(
                    f"SEC match found for: {company_name}",
                    cik=company.get("cik"),
                    ticker=company.get("ticker"),
                    name=company.get("name")
                )
                
                return {
                    "source": "SEC EDGAR",
                    "company_name": company.get("name"),
                    "ticker": company.get("ticker"),
                    "cik": company.get("cik"),
                    "cik_str": company.get("cik_str"),
                    "match_type": "found",
                    "sec_url": f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={company.get('cik')}&action=getcompany",
                    "note": f"Found in SEC EDGAR database"
                }
            else:
                # No match found
                logger.info(f"No SEC match found for: {company_name}")
                return {
                    "source": "SEC EDGAR",
                    "company_name": company_name,
                    "match_type": "not_found",
                    "note": "Company not found in SEC EDGAR database (may not be publicly traded)"
                }
                
        except Exception as e:
            logger.error(f"Error fetching US registry data", error=str(e), exc_info=True)
            return {
                "source": "SEC EDGAR",
                "company_name": company_name,
                "error": str(e),
                "note": "Error occurred while checking SEC EDGAR database"
            }
    
    def _fetch_uk_registry(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from UK Companies House
        
        Args:
            company_name: Company name
        
        Returns:
            Dictionary with company data or None
        """
        try:
            logger.info(f"Fetching UK registry data for: {company_name}")
            
            # Companies House API would require API key
            # Placeholder for structure
            return {
                "source": "Companies House",
                "company_name": company_name,
                "status": "not_implemented",
                "note": "Companies House API integration required (API key needed)"
            }
        except Exception as e:
            logger.error(f"Error fetching UK registry data", error=str(e))
            return None
    
    def _fetch_au_registry(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Australian ASIC
        
        Args:
            company_name: Company name
        
        Returns:
            Dictionary with company data or None
        """
        try:
            logger.info(f"Fetching AU registry data for: {company_name}")
            
            # ASIC has limited public API access
            return {
                "source": "ASIC",
                "company_name": company_name,
                "status": "not_implemented",
                "note": "ASIC API integration required"
            }
        except Exception as e:
            logger.error(f"Error fetching AU registry data", error=str(e))
            return None
    
    def _fetch_opencorporates(
        self,
        company_name: str,
        country: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch data from OpenCorporates API
        
        Args:
            company_name: Company name
            country: Country code
        
        Returns:
            Dictionary with company data or None
        """
        try:
            # OpenCorporates API requires API key for production use
            api_token = os.getenv("OPENCORPORATES_API_TOKEN")
            
            if not api_token:
                logger.info("OpenCorporates API token not configured, skipping")
                return None
            
            # Build API URL
            base_url = "https://api.opencorporates.com/v0.4/companies/search"
            params = {
                "q": company_name,
                "jurisdiction_code": country.lower(),
                "api_token": api_token
            }
            
            response = self.session.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                companies = data.get("results", {}).get("companies", [])
                
                if companies:
                    # Return first matching company
                    company = companies[0]["company"]
                    return {
                        "source": "OpenCorporates",
                        "company_name": company.get("name"),
                        "company_number": company.get("company_number"),
                        "jurisdiction": company.get("jurisdiction_code"),
                        "status": company.get("current_status"),
                        "opencorporates_url": company.get("opencorporates_url")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching OpenCorporates data", error=str(e))
            return None
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate company registry data"""
        if not data:
            return False
        
        # Check if we have at least one source
        sources = data.get("sources", [])
        if not sources:
            return False
        
        # Check if we have registry data
        registry_data = data.get("registry_data", {})
        if not registry_data:
            return False
        
        return True

