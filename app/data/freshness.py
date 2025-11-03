"""
Data freshness tracking
Tracks and scores data freshness for collected information
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataFreshnessTracker:
    """Tracks data freshness and timestamps"""
    
    def __init__(self):
        """Initialize freshness tracker"""
        pass
    
    def calculate_freshness_score(
        self,
        collected_at: datetime,
        current_time: Optional[datetime] = None
    ) -> str:
        """
        Calculate freshness score based on age of data
        
        Args:
            collected_at: Timestamp when data was collected
            current_time: Current time (uses UTC now if None)
        
        Returns:
            Freshness score: "fresh", "recent", "stale", "very_stale"
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        age = current_time - collected_at
        
        # Define freshness thresholds
        if age < timedelta(hours=24):
            return "fresh"  # Less than 24 hours
        elif age < timedelta(days=7):
            return "recent"  # Less than 7 days
        elif age < timedelta(days=30):
            return "stale"  # Less than 30 days
        else:
            return "very_stale"  # More than 30 days
    
    def track_data_collection(
        self,
        source: str,
        collected_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track data collection with timestamp
        
        Args:
            source: Name of data source
            collected_at: Timestamp when data was collected
            metadata: Additional metadata
        
        Returns:
            Dictionary with freshness tracking information
        """
        freshness_score = self.calculate_freshness_score(collected_at)
        
        tracking_info = {
            "source": source,
            "collected_at": collected_at.isoformat(),
            "freshness_score": freshness_score,
            "age_hours": (datetime.utcnow() - collected_at).total_seconds() / 3600,
            "metadata": metadata or {}
        }
        
        logger.info(
            f"Tracked data collection from {source}",
            freshness=freshness_score,
            age_hours=tracking_info["age_hours"]
        )
        
        return tracking_info
    
    def should_refresh_data(
        self,
        last_collected_at: datetime,
        refresh_threshold: timedelta = timedelta(days=7)
    ) -> bool:
        """
        Determine if data should be refreshed
        
        Args:
            last_collected_at: Timestamp when data was last collected
            refresh_threshold: Maximum age before refresh recommended
        
        Returns:
            True if data should be refreshed
        """
        age = datetime.utcnow() - last_collected_at
        should_refresh = age > refresh_threshold
        
        logger.info(
            f"Data refresh check",
            last_collected=last_collected_at.isoformat(),
            age_days=age.days,
            should_refresh=should_refresh
        )
        
        return should_refresh
    
    def get_freshness_info(
        self,
        collected_at: datetime,
        verified_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive freshness information
        
        Args:
            collected_at: Timestamp when data was collected
            verified_at: Optional timestamp when data was last verified
        
        Returns:
            Dictionary with freshness information
        """
        current_time = datetime.utcnow()
        
        freshness_score = self.calculate_freshness_score(collected_at, current_time)
        age = current_time - collected_at
        
        info = {
            "collected_at": collected_at.isoformat(),
            "current_time": current_time.isoformat(),
            "age_hours": age.total_seconds() / 3600,
            "age_days": age.days,
            "freshness_score": freshness_score,
            "is_fresh": freshness_score in ["fresh", "recent"]
        }
        
        if verified_at:
            verification_age = current_time - verified_at
            info.update({
                "verified_at": verified_at.isoformat(),
                "verification_age_hours": verification_age.total_seconds() / 3600,
                "verification_age_days": verification_age.days
            })
        
        return info

