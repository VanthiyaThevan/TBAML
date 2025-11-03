"""
Data validation and cleaning pipeline
Validates and cleans collected data from various sources
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataValidator:
    """Validates and cleans collected data"""
    
    def __init__(self):
        """Initialize data validator"""
        pass
    
    def validate_and_clean(
        self,
        raw_data: Dict[str, Any],
        source: str
    ) -> Dict[str, Any]:
        """
        Validate and clean raw data from a source
        
        Args:
            raw_data: Raw data dictionary from source
            source: Name of the data source
        
        Returns:
            Cleaned and validated data dictionary
        """
        cleaned_data = {
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "valid": False,
            "data": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Clean and validate based on source type
            if source == "web_scraper":
                cleaned_data.update(self._clean_web_scraper_data(raw_data))
            elif source == "company_registry":
                cleaned_data.update(self._clean_registry_data(raw_data))
            elif source == "sanctions_checker":
                cleaned_data.update(self._clean_sanctions_data(raw_data))
            else:
                # Generic cleaning
                cleaned_data.update(self._clean_generic_data(raw_data))
            
            # Additional validation
            validation_result = self._validate_cleaned_data(cleaned_data["data"])
            if not validation_result["valid"]:
                cleaned_data["errors"].extend(validation_result["errors"])
                cleaned_data["warnings"].extend(validation_result["warnings"])
            else:
                cleaned_data["valid"] = True
            
        except Exception as e:
            logger.error(f"Error validating data from {source}", error=str(e))
            cleaned_data["errors"].append(f"Validation error: {str(e)}")
        
        return cleaned_data
    
    def _clean_web_scraper_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean web scraper data"""
        cleaned = {
            "data": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Extract and clean website data
            sources = data.get("sources", [])
            if sources:
                # Take first source
                source_data = sources[0]
                cleaned["data"] = {
                    "url": self._clean_url(source_data.get("url")),
                    "title": self._clean_text(source_data.get("title", "")),
                    "description": self._clean_text(source_data.get("description", "")),
                    "content": self._clean_text(source_data.get("content", "")),
                    "content_length": source_data.get("content_length", 0),
                    "links": source_data.get("links", [])[:10]  # Limit links
                }
            else:
                cleaned["warnings"].append("No sources found in scraper data")
        
        except Exception as e:
            cleaned["errors"].append(f"Error cleaning scraper data: {str(e)}")
        
        return cleaned
    
    def _clean_registry_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean company registry data"""
        cleaned = {
            "data": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            registry_data = data.get("registry_data", {})
            if registry_data:
                cleaned["data"] = {
                    "company_name": self._clean_text(data.get("company_name", "")),
                    "country": data.get("country", "").upper(),
                    "registry_sources": data.get("sources", []),
                    "registry_data": registry_data
                }
            else:
                cleaned["warnings"].append("No registry data found")
        
        except Exception as e:
            cleaned["errors"].append(f"Error cleaning registry data: {str(e)}")
        
        return cleaned
    
    def _clean_sanctions_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean sanctions check data"""
        cleaned = {
            "data": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            cleaned["data"] = {
                "entity_name": self._clean_text(data.get("entity_name", "")),
                "country": data.get("country", "").upper(),
                "is_sanctioned": data.get("is_sanctioned", False),
                "sanctions_checks": data.get("sanctions_checks", {}),
                "matches": data.get("matches", [])
            }
            
            if cleaned["data"]["is_sanctioned"]:
                cleaned["warnings"].append("Entity found on sanctions list")
        
        except Exception as e:
            cleaned["errors"].append(f"Error cleaning sanctions data: {str(e)}")
        
        return cleaned
    
    def _clean_generic_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic data cleaning"""
        cleaned = {
            "data": data,
            "errors": [],
            "warnings": []
        }
        
        return cleaned
    
    def _clean_url(self, url: Optional[str]) -> Optional[str]:
        """Clean and validate URL"""
        if not url:
            return None
        
        url = url.strip()
        
        # Basic URL validation
        if url.startswith(("http://", "https://")):
            return url
        
        return None
    
    def _clean_text(self, text: str, max_length: int = 5000) -> str:
        """Clean text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text.strip()
    
    def _validate_cleaned_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate cleaned data
        
        Returns:
            Dictionary with validation result
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Basic validation - data should not be empty
        if not data:
            result["valid"] = False
            result["errors"].append("Data is empty")
        
        return result
    
    def merge_data(self, cleaned_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge data from multiple cleaned sources
        
        Args:
            cleaned_results: List of cleaned data dictionaries
        
        Returns:
            Merged data dictionary
        """
        merged = {
            "sources": [],
            "data": {},
            "timestamp": datetime.utcnow().isoformat(),
            "validation_errors": [],
            "warnings": []
        }
        
        for result in cleaned_results:
            if result.get("valid"):
                source = result.get("source", "unknown")
                merged["sources"].append(source)
                
                # Merge data (later sources override earlier ones)
                source_data = result.get("data", {})
                merged["data"].update(source_data)
            else:
                # Collect errors
                errors = result.get("errors", [])
                merged["validation_errors"].extend(errors)
            
            # Collect warnings
            warnings = result.get("warnings", [])
            merged["warnings"].extend(warnings)
        
        return merged

