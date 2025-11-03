"""
API Schemas (Pydantic Models)
Request and response schemas for UC1 API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# UC1 Input Schemas
class LOBVerificationInput(BaseModel):
    """Input schema for LOB verification"""
    client: str = Field(..., description="Company name", min_length=1, max_length=255)
    client_country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)", min_length=2, max_length=2)
    client_role: str = Field(..., description="Role: Import or Export", pattern="^(Import|Export)$")
    product_name: str = Field(..., description="Product name/category", min_length=1, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "client": "Shell plc",
                "client_country": "GB",
                "client_role": "Export",
                "product_name": "Oil & Gas"
            }
        }


# UC1 Output Schemas
class FlagOutput(BaseModel):
    """Flag/Alert output schema"""
    category: str = Field(..., description="Flag category")
    severity: str = Field(..., description="Flag severity: high, medium, low")
    message: str = Field(..., description="Flag message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "compliance_issue",
                "severity": "medium",
                "message": "Limited data sources available"
            }
        }


class LOBVerificationOutput(BaseModel):
    """Output schema for LOB verification"""
    id: Optional[int] = Field(None, description="Verification record ID")
    
    # UC1 Required Outputs
    ai_response: str = Field(..., description="AI-generated analysis response")
    website_source: Optional[str] = Field(None, description="Website URL source")
    publication_date: Optional[str] = Field(None, description="Publication date of information")
    activity_level: str = Field(..., description="Activity level: Active, Dormant, Inactive, Suspended, Unknown")
    flags: List[str] = Field(default_factory=list, description="List of flags/alerts")
    sources: List[str] = Field(default_factory=list, description="List of data sources")
    
    # Additional Outputs
    confidence_score: Optional[str] = Field(None, description="Confidence level: High, Medium, Low")
    is_red_flag: bool = Field(default=False, description="Whether this is a red flag case")
    risk_score: Optional[float] = Field(None, description="Risk score (0.0 to 1.0)")
    risk_level: Optional[str] = Field(None, description="Risk level: High, Medium, Low")
    
    # Metadata
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "ai_response": "Shell plc is a legitimate British multinational oil and gas company...",
                "website_source": "https://www.shell.com",
                "publication_date": "2025-10-30",
                "activity_level": "Active",
                "flags": ["[MEDIUM] source_reliability: Limited number of data sources"],
                "sources": ["web_scraper", "company_registry", "sanctions_checker"],
                "confidence_score": "High",
                "is_red_flag": False,
                "risk_score": 0.25,
                "risk_level": "Low"
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Validation Error",
                "detail": "client_country must be 2 characters",
                "status_code": 422
            }
        }


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2025-11-01T10:00:00Z"
            }
        }

