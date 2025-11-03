"""Line of Business database models"""

from sqlalchemy import Column, String, Text, JSON, Boolean, DateTime
from app.models.base import BaseModel


class LOBVerification(BaseModel):
    """Line of Business Verification record"""
    __tablename__ = "lob_verifications"
    
    client = Column(String(255), nullable=False, index=True)
    client_country = Column(String(100), nullable=False)
    client_role = Column(String(50), nullable=False)  # Import/Export
    product_name = Column(String(500), nullable=False)
    
    # Output fields
    ai_response = Column(Text, nullable=True)
    website_source = Column(String(500), nullable=True)
    publication_date = Column(String(50), nullable=True)
    activity_level = Column(String(50), nullable=True)  # Active, Dormant, etc.
    flags = Column(JSON, nullable=True)  # List of flags/alerts
    sources = Column(JSON, nullable=True)  # List of data sources
    
    # Metadata
    is_red_flag = Column(Boolean, default=False)
    confidence_score = Column(String(50), nullable=True)
    
    # Data freshness tracking
    data_collected_at = Column(DateTime, nullable=True)  # When data was collected
    data_freshness_score = Column(String(50), nullable=True)  # Freshness rating
    last_verified_at = Column(DateTime, nullable=True)  # Last verification timestamp

