"""
Data storage for collected LOB verification data
Handles storage and retrieval of collected data
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.base import get_session_factory
from app.models.lob import LOBVerification
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataStorage:
    """Handles storage of collected data"""
    
    def __init__(self):
        """Initialize data storage"""
        self.SessionLocal, _ = get_session_factory()
    
    def store_verification(
        self,
        input_data: Dict[str, Any],
        collected_data: Dict[str, Any],
        aggregated_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        Store LOB verification data
        
        Args:
            input_data: Original input (client, country, role, product)
            collected_data: Raw collected data from sources
            aggregated_data: Aggregated and cleaned data
        
        Returns:
            ID of created record or None
        """
        db: Session = self.SessionLocal()
        try:
            # Create verification record
            verification = LOBVerification(
                client=input_data.get("client", ""),
                client_country=input_data.get("client_country", ""),
                client_role=input_data.get("client_role", ""),
                product_name=input_data.get("product_name", ""),
                
                # Output fields (will be filled by AI layer later)
                ai_response=None,
                website_source=aggregated_data.get("data", {}).get("url"),
                publication_date=None,
                activity_level=None,
                flags=None,
                sources=aggregated_data.get("sources", []),
                is_red_flag=False,
                confidence_score=None
            )
            
            db.add(verification)
            db.commit()
            db.refresh(verification)
            
            logger.info(f"Stored verification record: {verification.id}")
            return verification.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing verification data", error=str(e))
            return None
        finally:
            db.close()
    
    def update_verification(
        self,
        verification_id: int,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update existing verification record
        
        Args:
            verification_id: ID of verification record
            update_data: Dictionary with fields to update
        
        Returns:
            True if update successful
        """
        db: Session = self.SessionLocal()
        try:
            verification = db.query(LOBVerification).filter(
                LOBVerification.id == verification_id
            ).first()
            
            if not verification:
                logger.warning(f"Verification record not found: {verification_id}")
                return False
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(verification, key):
                    setattr(verification, key, value)
            
            db.commit()
            logger.info(f"Updated verification record: {verification_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating verification data", error=str(e))
            return False
        finally:
            db.close()
    
    def get_verification(self, verification_id: int) -> Optional[Dict[str, Any]]:
        """
        Get verification record by ID
        
        Args:
            verification_id: ID of verification record
        
        Returns:
            Dictionary with verification data or None
        """
        db: Session = self.SessionLocal()
        try:
            verification = db.query(LOBVerification).filter(
                LOBVerification.id == verification_id
            ).first()
            
            if not verification:
                return None
            
            return {
                "id": verification.id,
                "client": verification.client,
                "client_country": verification.client_country,
                "client_role": verification.client_role,
                "product_name": verification.product_name,
                "ai_response": verification.ai_response,
                "website_source": verification.website_source,
                "publication_date": verification.publication_date,
                "activity_level": verification.activity_level,
                "flags": verification.flags,
                "sources": verification.sources,
                "is_red_flag": verification.is_red_flag,
                "confidence_score": verification.confidence_score,
                "created_at": verification.created_at.isoformat() if verification.created_at else None,
                "updated_at": verification.updated_at.isoformat() if verification.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting verification data", error=str(e))
            return None
        finally:
            db.close()
    
    def track_data_source(
        self,
        verification_id: int,
        source_name: str,
        source_url: Optional[str] = None,
        collected_at: Optional[datetime] = None
    ) -> bool:
        """
        Track data source attribution
        
        Args:
            verification_id: ID of verification record
            source_name: Name of data source
            source_url: URL of data source
            collected_at: Timestamp when data was collected
        
        Returns:
            True if tracking successful
        """
        # This would be stored in a separate table or in the sources field
        # For now, we'll store it in the sources JSON field
        db: Session = self.SessionLocal()
        try:
            verification = db.query(LOBVerification).filter(
                LOBVerification.id == verification_id
            ).first()
            
            if not verification:
                return False
            
            # Get existing sources
            sources = verification.sources or []
            
            # Add new source with attribution
            new_source = {
                "name": source_name,
                "url": source_url,
                "collected_at": (collected_at or datetime.utcnow()).isoformat()
            }
            
            sources.append(new_source)
            verification.sources = sources
            
            db.commit()
            logger.info(f"Tracked data source for verification {verification_id}", 
                       source=source_name)
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error tracking data source", error=str(e))
            return False
        finally:
            db.close()

