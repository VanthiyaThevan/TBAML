"""
Sanctions and watchlist checker
Checks if companies/individuals are on sanctions lists
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from app.data.base import DataSource, DataCollectionResult
from app.data.ofac_parser import get_ofac_parser
from app.core.logging import get_logger
import os

logger = get_logger(__name__)


class SanctionsChecker(DataSource):
    """Checks sanctions lists and watchlists"""
    
    def __init__(
        self,
        name: str = "sanctions_checker",
        rate_limit: int = 10
    ):
        """
        Initialize sanctions checker
        
        Args:
            name: Name of the data source
            rate_limit: Maximum requests per minute
        """
        super().__init__(name, rate_limit)
        self.session = requests.Session()
        self.sanctions_lists = {}  # Cache for loaded sanctions lists
    
    def fetch_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check sanctions lists
        
        Args:
            query: Query parameters containing:
                - client: Company/individual name
                - client_country: Country code
        
        Returns:
            Dictionary containing sanctions check results
        """
        self._rate_limit_check()
        
        entity_name = query.get("client", "")
        country = query.get("client_country", "")
        
        result_data = {
            "entity_name": entity_name,
            "country": country,
            "sanctions_checks": {},
            "matches": [],
            "is_sanctioned": False
        }
        
        # Check OFAC (US Sanctions)
        ofac_result = self._check_ofac(entity_name)
        if ofac_result:
            result_data["sanctions_checks"]["ofac"] = ofac_result
            if ofac_result.get("match"):
                result_data["matches"].append({
                    "list": "OFAC",
                    "match": ofac_result["match"]
                })
                result_data["is_sanctioned"] = True
        
        # Check UN Sanctions
        un_result = self._check_un_sanctions(entity_name)
        if un_result:
            result_data["sanctions_checks"]["un"] = un_result
            if un_result.get("match"):
                result_data["matches"].append({
                    "list": "UN",
                    "match": un_result["match"]
                })
                result_data["is_sanctioned"] = True
        
        # Check EU Sanctions (if applicable)
        if country in ["EU", "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", 
                      "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", 
                      "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]:
            eu_result = self._check_eu_sanctions(entity_name)
            if eu_result:
                result_data["sanctions_checks"]["eu"] = eu_result
                if eu_result.get("match"):
                    result_data["matches"].append({
                        "list": "EU",
                        "match": eu_result["match"]
                    })
                    result_data["is_sanctioned"] = True
        
        return result_data
    
    def _check_ofac(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Check OFAC (US) sanctions list using downloaded SDN list
        
        Args:
            entity_name: Name to check
        
        Returns:
            Dictionary with OFAC check results or None
        """
        try:
            logger.info(f"Checking OFAC sanctions list for: {entity_name}")
            
            # Get OFAC parser instance (singleton, loads file once)
            parser = get_ofac_parser()
            
            # Search for entity in SDN list
            # Use partial match to catch variations
            matches = parser.search_entity(entity_name, exact_match=False)
            
            if matches:
                # Found matches - extract relevant information
                match_details = []
                for match in matches[:5]:  # Limit to first 5 matches
                    names = match.get("names", [])
                    programs = match.get("programs", [])
                    profile_id = match.get("profile_id", "")
                    
                    match_details.append({
                        "profile_id": profile_id,
                        "names": names,
                        "programs": programs,
                        "dates_of_birth": match.get("dates_of_birth", []),
                        "places_of_birth": match.get("places_of_birth", [])
                    })
                
                logger.warning(
                    f"OFAC match found for: {entity_name}",
                    matches=len(matches),
                    profile_ids=[m.get("profile_id") for m in matches[:5]]
                )
                
                return {
                    "source": "OFAC SDN List",
                    "list_url": "https://ofac.treasury.gov/specially-designated-nationals-list-sdn-list",
                    "match": True,
                    "matches": match_details,
                    "match_count": len(matches),
                    "checked_at": datetime.utcnow().isoformat(),
                    "note": f"Found {len(matches)} potential match(es) in OFAC SDN list"
                }
            else:
                # No matches found
                logger.info(f"No OFAC match found for: {entity_name}")
                return {
                    "source": "OFAC SDN List",
                    "list_url": "https://ofac.treasury.gov/specially-designated-nationals-list-sdn-list",
                    "match": False,
                    "matches": [],
                    "match_count": 0,
                    "checked_at": datetime.utcnow().isoformat(),
                    "note": "Entity not found in OFAC SDN list"
                }
                
        except Exception as e:
            logger.error(f"Error checking OFAC list", error=str(e), exc_info=True)
            return {
                "source": "OFAC SDN List",
                "list_url": "https://ofac.treasury.gov/specially-designated-nationals-list-sdn-list",
                "match": None,
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat(),
                "note": "Error occurred while checking OFAC SDN list"
            }
    
    def _check_un_sanctions(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Check UN sanctions list
        
        Args:
            entity_name: Name to check
        
        Returns:
            Dictionary with UN sanctions check results or None
        """
        try:
            logger.info(f"Checking UN sanctions list for: {entity_name}")
            
            # UN sanctions lists are available via API or downloadable files
            # Placeholder structure
            
            return {
                "source": "UN Security Council",
                "list_url": "https://www.un.org/securitycouncil/sanctions/information",
                "match": None,
                "checked_at": datetime.utcnow().isoformat(),
                "note": "UN sanctions list checking requires API integration or file parsing"
            }
        except Exception as e:
            logger.error(f"Error checking UN sanctions list", error=str(e))
            return None
    
    def _check_eu_sanctions(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Check EU sanctions list using downloaded XML file
        
        Args:
            entity_name: Name to check
        
        Returns:
            Dictionary with EU sanctions check results or None
        """
        try:
            logger.info(f"Checking EU sanctions list for: {entity_name}")
            
            # Get EU sanctions parser instance (singleton, loads file once)
            from app.data.eu_sanctions_parser import get_eu_sanctions_parser
            
            parser = get_eu_sanctions_parser()
            
            if not parser.loaded:
                logger.warning("EU sanctions file not loaded")
                return None
            
            # Search for entity in EU sanctions list
            # Use partial match to catch variations
            matches = parser.search_entity(entity_name, exact_match=False)
            
            if matches:
                # Found matches - extract relevant information
                match_details = []
                for match in matches[:5]:  # Limit to first 5 matches
                    names = match.get("names", [])
                    regulations = match.get("regulations", [])
                    logical_id = match.get("logical_id", "")
                    subject_type = match.get("subject_type", "")
                    
                    match_details.append({
                        "logical_id": logical_id,
                        "names": names,
                        "subject_type": subject_type,
                        "regulations": regulations[:2],  # First 2 regulations
                        "citizenships": match.get("citizenships", []),
                        "birthdates": match.get("birthdates", [])
                    })
                
                logger.warning(
                    f"EU sanctions match found for: {entity_name}",
                    matches=len(matches),
                    logical_ids=[m.get("logical_id") for m in matches[:5]]
                )
                
                return {
                    "source": "EU Consolidated Sanctions List",
                    "list_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content",
                    "match": True,
                    "matches": match_details,
                    "match_count": len(matches),
                    "checked_at": datetime.utcnow().isoformat(),
                    "note": f"Found {len(matches)} potential match(es) in EU Consolidated Sanctions List"
                }
            else:
                # No matches found
                logger.info(f"No EU sanctions match found for: {entity_name}")
                return {
                    "source": "EU Consolidated Sanctions List",
                    "list_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content",
                    "match": False,
                    "matches": [],
                    "match_count": 0,
                    "checked_at": datetime.utcnow().isoformat(),
                    "note": "Entity not found in EU Consolidated Sanctions List"
                }
                
        except Exception as e:
            logger.error(f"Error checking EU sanctions list", error=str(e), exc_info=True)
            return {
                "source": "EU Consolidated Sanctions List",
                "list_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content",
                "match": None,
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat(),
                "note": "Error occurred while checking EU Consolidated Sanctions List"
            }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate sanctions check data"""
        if not data:
            return False
        
        # Must have sanctions_checks field
        sanctions_checks = data.get("sanctions_checks", {})
        if not sanctions_checks:
            return False
        
        return True

