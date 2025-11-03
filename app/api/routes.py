"""
API Routes
REST API endpoints for TBAML system
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from app.api.schemas import (
    LOBVerificationInput,
    LOBVerificationOutput,
    ErrorResponse,
    HealthResponse
)
from app.services.ai_service import AIService
from app.data.connector import DataConnector
from app.models.base import get_session_factory
from app.models.lob import LOBVerification
from app.core.logging import get_logger
from datetime import datetime
import datetime as dt

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Initialize services
ai_service = AIService()
data_connector = DataConnector()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Service health status
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0"
    )


@router.post("/api/v1/lob/verify", response_model=LOBVerificationOutput, tags=["UC1"])
async def verify_lob(input_data: LOBVerificationInput):
    """
    UC1: Line of Business Verification
    
    Performs complete LOB verification including:
    - Data collection from multiple sources
    - AI/ML analysis
    - Activity level classification
    - Risk assessment
    - Flag generation
    
    Args:
        input_data: LOB verification input (company, country, role, product)
    
    Returns:
        Complete LOB verification output with all UC1 fields
    """
    try:
        logger.info(
            f"LOB verification request",
            company=input_data.client,
            country=input_data.client_country,
            role=input_data.client_role
        )
        
        # Step 1: Prepare input data
        input_dict = {
            "client": input_data.client,
            "client_country": input_data.client_country,
            "client_role": input_data.client_role,
            "product_name": input_data.product_name
        }
        
        # Step 2: Collect data from sources
        logger.info("Collecting data from sources...")
        
        # Initialize data sources
        from app.data.scraper import WebScraper
        from app.data.company_registry import CompanyRegistryFetcher
        from app.data.sanctions_checker import SanctionsChecker
        
        # Register sources
        data_connector.register_source(WebScraper())
        data_connector.register_source(CompanyRegistryFetcher())
        data_connector.register_source(SanctionsChecker())
        
        # Collect from all sources
        results = data_connector.collect_from_all_sources(input_dict)
        
        # Format collected data
        collected_data = {
            "sources": [],
            "data": {}
        }
        
        for result in results:
            if result.success:
                collected_data["sources"].append({
                    "name": result.source,
                    "data": result.data,
                    "timestamp": result.timestamp.isoformat() if result.timestamp else None
                })
                # Merge data
                if result.data:
                    collected_data["data"].update(result.data)
        
        # Step 3: Aggregate and validate data
        logger.info("Aggregating and validating data...")
        aggregated_data = data_connector.aggregate_results(results)
        
        # Step 4: Store collected data (without AI outputs yet)
        from app.data.storage import DataStorage
        storage = DataStorage()
        verification_id = storage.store_verification(
            input_data=input_dict,
            collected_data=collected_data,
            aggregated_data=aggregated_data
        )
        
        if not verification_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store verification data"
            )
        
        # Step 5: Run AI analysis and update
        logger.info("Running AI analysis...")
        ai_result = ai_service.analyze_and_update(
            verification_id=verification_id,
            force_update=False
        )
        
        if not ai_result or ai_result.get("status") == "error":
            logger.warning("AI analysis encountered issues, returning partial results")
        
        # Step 6: Get updated record
        SessionLocal, _ = get_session_factory()
        db = SessionLocal()
        
        try:
            verification = db.query(LOBVerification).filter(
                LOBVerification.id == verification_id
            ).first()
            
            if not verification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Verification record not found"
                )
            
            # Step 7: Format response
            sources_list = verification.sources if isinstance(verification.sources, list) else [verification.sources] if verification.sources else []
            sources_names = [s.get("name") if isinstance(s, dict) else str(s) for s in sources_list] if sources_list else []
            
            flags_list = verification.flags if isinstance(verification.flags, list) else [verification.flags] if verification.flags else []
            
            output = LOBVerificationOutput(
                id=verification.id,
                ai_response=verification.ai_response or "Analysis in progress...",
                website_source=verification.website_source,
                publication_date=verification.publication_date,
                activity_level=verification.activity_level or "Unknown",
                flags=flags_list,
                sources=sources_names,
                confidence_score=verification.confidence_score or "Low",
                is_red_flag=verification.is_red_flag,
                created_at=verification.created_at,
                updated_at=verification.updated_at
            )
            
            logger.info(
                f"LOB verification complete",
                verification_id=verification_id,
                activity_level=output.activity_level,
                flags_count=len(output.flags)
            )
            
            return output
        
        finally:
            db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in LOB verification", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/api/v1/lob/{verification_id}", response_model=LOBVerificationOutput, tags=["UC1"])
async def get_lob_verification(verification_id: int):
    """
    Get LOB verification by ID
    
    Args:
        verification_id: Verification record ID
    
    Returns:
        LOB verification output
    """
    SessionLocal, _ = get_session_factory()
    db = SessionLocal()
    
    try:
        verification = db.query(LOBVerification).filter(
            LOBVerification.id == verification_id
        ).first()
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verification {verification_id} not found"
            )
        
        sources_list = verification.sources if isinstance(verification.sources, list) else [verification.sources] if verification.sources else []
        sources_names = [s.get("name") if isinstance(s, dict) else str(s) for s in sources_list] if sources_list else []
        
        flags_list = verification.flags if isinstance(verification.flags, list) else [verification.flags] if verification.flags else []
        
        return LOBVerificationOutput(
            id=verification.id,
            ai_response=verification.ai_response or "",
            website_source=verification.website_source,
            publication_date=verification.publication_date,
            activity_level=verification.activity_level or "Unknown",
            flags=flags_list,
            sources=sources_names,
            confidence_score=verification.confidence_score,
            is_red_flag=verification.is_red_flag,
            created_at=verification.created_at,
            updated_at=verification.updated_at
        )
    
    finally:
        db.close()


@router.get("/api/v1/lob", response_model=List[LOBVerificationOutput], tags=["UC1"])
async def list_lob_verifications(limit: int = 10, offset: int = 0):
    """
    List LOB verifications
    
    Args:
        limit: Maximum number of records to return
        offset: Offset for pagination
    
    Returns:
        List of LOB verification outputs
    """
    SessionLocal, _ = get_session_factory()
    db = SessionLocal()
    
    try:
        verifications = db.query(LOBVerification).offset(offset).limit(limit).all()
        
        results = []
        for v in verifications:
            sources_list = v.sources if isinstance(v.sources, list) else [v.sources] if v.sources else []
            sources_names = [s.get("name") if isinstance(s, dict) else str(s) for s in sources_list] if sources_list else []
            
            flags_list = v.flags if isinstance(v.flags, list) else [v.flags] if v.flags else []
            
            results.append(LOBVerificationOutput(
                id=v.id,
                ai_response=v.ai_response or "",
                website_source=v.website_source,
                publication_date=v.publication_date,
                activity_level=v.activity_level or "Unknown",
                flags=flags_list,
                sources=sources_names,
                confidence_score=v.confidence_score,
                is_red_flag=v.is_red_flag,
                created_at=v.created_at,
                updated_at=v.updated_at
            ))
        
        return results
    
    finally:
        db.close()

