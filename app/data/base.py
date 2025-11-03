"""
Base classes for data source connectors
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, name: str, rate_limit: int = 10):
        """
        Initialize data source
        
        Args:
            name: Name of the data source
            rate_limit: Maximum requests per minute
        """
        self.name = name
        self.rate_limit = rate_limit
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0
        
    @abstractmethod
    def fetch_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from the source
        
        Args:
            query: Query parameters (client, country, etc.)
        
        Returns:
            Dictionary containing collected data
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate the collected data
        
        Args:
            data: Data to validate
        
        Returns:
            True if data is valid
        """
        pass
    
    def get_source_info(self) -> Dict[str, Any]:
        """
        Get information about this data source
        
        Returns:
            Dictionary with source metadata
        """
        return {
            "name": self.name,
            "rate_limit": self.rate_limit,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        # Simple rate limiting - can be enhanced
        current_time = datetime.utcnow()
        if self.last_request_time:
            time_diff = (current_time - self.last_request_time).total_seconds()
            min_interval = 60.0 / self.rate_limit
            if time_diff < min_interval:
                import time
                sleep_time = min_interval - time_diff
                time.sleep(sleep_time)
        
        self.last_request_time = datetime.utcnow()
        self.request_count += 1


class DataCollectionResult:
    """Result object for data collection operations"""
    
    def __init__(
        self,
        source: str,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.source = source
        self.success = success
        self.data = data or {}
        self.error = error
        self.timestamp = timestamp or datetime.utcnow()
        self.url = None  # Source URL
        self.confidence = None  # Confidence score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "source": self.source,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
            "confidence": self.confidence
        }

