"""
AI Service Module
Service layer that integrates AI analysis with data storage
Updates database records with AI-generated UC1 outputs
"""

from typing import Dict, List, Optional, Any
from app.core.logging import get_logger
from app.ai.orchestrator import AIOrchestrator
from app.models.base import get_session_factory
from app.models.lob import LOBVerification
from app.data.storage import DataStorage

logger = get_logger(__name__)


class AIService:
    """Service for AI analysis and database updates"""
    
    def __init__(self):
        """Initialize AI service"""
        self.orchestrator = AIOrchestrator()
        self.data_storage = DataStorage()
        self.SessionLocal, _ = get_session_factory()
        logger.info("AIService initialized")
    
    def analyze_and_update(
        self,
        verification_id: int,
        force_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze LOB verification and update database with AI outputs
        
        Args:
            verification_id: Verification record ID
            force_update: Whether to force update even if analysis exists
        
        Returns:
            Updated verification record or None
        """
        db = self.SessionLocal()
        try:
            # Get verification record
            verification = db.query(LOBVerification).filter(
                LOBVerification.id == verification_id
            ).first()
            
            if not verification:
                logger.error(f"Verification not found: {verification_id}")
                return None
            
            # Check if already analyzed (unless force update)
            if not force_update and verification.ai_response:
                logger.info(f"Verification {verification_id} already analyzed, skipping")
                return {
                    "id": verification.id,
                    "company": verification.client,
                    "status": "already_analyzed",
                    "existing_ai_response": verification.ai_response[:200] + "..."
                }
            
            logger.info(f"Analyzing verification {verification_id}: {verification.client}")
            
            # Prepare input data
            input_data = {
                "client": verification.client,
                "client_country": verification.client_country,
                "client_role": verification.client_role,
                "product_name": verification.product_name
            }
            
            # Prepare collected data from stored sources
            sources_list = verification.sources if isinstance(verification.sources, list) else [verification.sources] if verification.sources else []
            
            collected_data = {
                "sources": sources_list,
                "data": {
                    "website_content": None,  # Could be extracted from website_source
                    "description": f"{verification.client} is a company in {verification.client_country}"
                }
            }
            
            # Prepare aggregated data
            aggregated_data = {
                "data": {
                    "url": verification.website_source,
                    "description": f"{verification.client} ({verification.client_country}) - {verification.product_name}"
                },
                "sources": [s.get("name") if isinstance(s, dict) else str(s) for s in sources_list] if sources_list else []
            }
            
            # Run AI analysis
            try:
                ai_result = self.orchestrator.analyze_lob(
                    input_data=input_data,
                    collected_data=collected_data,
                    aggregated_data=aggregated_data
                )
                
                # Update database record
                verification.ai_response = ai_result.get("ai_response", "")
                verification.activity_level = ai_result.get("activity_level", "Unknown")
                verification.flags = ai_result.get("flags", [])
                verification.is_red_flag = ai_result.get("is_red_flag", False)
                verification.confidence_score = ai_result.get("confidence_score", "Low")
                
                # Update timestamp
                from datetime import datetime
                verification.last_verified_at = datetime.utcnow()
                
                db.commit()
                db.refresh(verification)
                
                logger.info(
                    f"Updated verification {verification_id}",
                    activity_level=verification.activity_level,
                    flags_count=len(verification.flags or []),
                    is_red_flag=verification.is_red_flag
                )
                
                return {
                    "id": verification.id,
                    "company": verification.client,
                    "status": "analyzed",
                    "activity_level": verification.activity_level,
                    "risk_level": ai_result.get("risk_level"),
                    "flags_count": len(verification.flags or []),
                    "is_red_flag": verification.is_red_flag,
                    "confidence_score": verification.confidence_score
                }
            
            except Exception as e:
                logger.error(f"Error in AI analysis for {verification_id}", error=str(e))
                db.rollback()
                return {
                    "id": verification.id,
                    "company": verification.client,
                    "status": "error",
                    "error": str(e)
                }
        
        except Exception as e:
            logger.error(f"Error updating verification {verification_id}", error=str(e))
            db.rollback()
            return None
        finally:
            db.close()
    
    def analyze_batch(
        self,
        limit: Optional[int] = None,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze multiple verifications
        
        Args:
            limit: Maximum number of records to analyze (None for all)
            force_update: Whether to force update even if analysis exists
        
        Returns:
            Dictionary with batch results
        """
        db = self.SessionLocal()
        
        results = {
            "total": 0,
            "analyzed": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }
        
        try:
            # Get verifications to analyze
            query = db.query(LOBVerification)
            
            if not force_update:
                query = query.filter(LOBVerification.ai_response.is_(None))
            
            if limit:
                query = query.limit(limit)
            
            verifications = query.all()
            results["total"] = len(verifications)
            
            logger.info(f"Starting batch analysis for {results['total']} verifications")
            
            for v in verifications:
                result = self.analyze_and_update(v.id, force_update=force_update)
                
                if result:
                    status = result.get("status", "unknown")
                    if status == "analyzed":
                        results["analyzed"] += 1
                    elif status == "already_analyzed":
                        results["skipped"] += 1
                    elif status == "error":
                        results["errors"] += 1
                    
                    results["details"].append(result)
                else:
                    results["errors"] += 1
            
            logger.info(
                f"Batch analysis complete",
                total=results["total"],
                analyzed=results["analyzed"],
                skipped=results["skipped"],
                errors=results["errors"]
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Error in batch analysis", error=str(e))
            return results
        finally:
            db.close()
    
    def get_analysis_status(self) -> Dict[str, Any]:
        """Get status of AI analysis for all records"""
        db = self.SessionLocal()
        
        try:
            total = db.query(LOBVerification).count()
            with_ai = db.query(LOBVerification).filter(
                LOBVerification.ai_response.isnot(None)
            ).count()
            with_activity = db.query(LOBVerification).filter(
                LOBVerification.activity_level.isnot(None),
                LOBVerification.activity_level != "Unknown"
            ).count()
            with_flags = db.query(LOBVerification).filter(
                LOBVerification.flags.isnot(None)
            ).count()
            red_flags = db.query(LOBVerification).filter(
                LOBVerification.is_red_flag == True
            ).count()
            
            return {
                "total_records": total,
                "with_ai_response": with_ai,
                "with_activity_level": with_activity,
                "with_flags": with_flags,
                "red_flags": red_flags,
                "completion_percentage": (with_ai / total * 100) if total > 0 else 0
            }
        
        finally:
            db.close()

