"""
Classification Module
Activity level and risk classification
"""

from typing import Dict, List, Optional, Any
from app.core.logging import get_logger
from app.ai.config import AIConfig
from app.ai.llm_client import LLMClient
from app.ai.prompts import PromptTemplates, ResponseParser

logger = get_logger(__name__)


class ActivityClassifier:
    """Classifies business activity levels"""
    
    def __init__(self, config: Optional[AIConfig] = None, llm_client: Optional[LLMClient] = None):
        """Initialize activity classifier"""
        self.config = config or AIConfig()
        self.llm_client = llm_client or LLMClient(config)
        self.parser = ResponseParser()
        logger.info("ActivityClassifier initialized")
    
    def classify(
        self,
        company_name: str,
        evidence_text: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify activity level
        
        Args:
            company_name: Company name
            evidence_text: Evidence text to analyze
            additional_context: Optional additional context
        
        Returns:
            Classification result with activity_level and confidence
        """
        try:
            prompt = PromptTemplates.activity_classification_prompt(
                company_name=company_name,
                evidence_text=evidence_text
            )
            
            system_prompt = PromptTemplates.SYSTEM_PROMPT_BASE + "\n\nFocus on activity level classification based on evidence."
            
            response = self.llm_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            if response.get("error"):
                logger.error(f"LLM error in activity classification", error=response.get("error"))
                return {
                    "activity_level": "Unknown",
                    "confidence": "Low",
                    "reasoning": "Error in classification",
                    "error": response.get("error")
                }
            
            content = response.get("content", "")
            if not content:
                return {
                    "activity_level": "Unknown",
                    "confidence": "Low",
                    "reasoning": "No response from LLM"
                }
            
            # Parse response
            parsed = self.parser.parse_lob_response(content)
            
            # Extract activity level
            activity_level = parsed.get("activity_level")
            if not activity_level:
                # Try to find in text
                activity_level = self._extract_activity_level(content)
            
            # Validate activity level
            if activity_level not in self.config.activity_classes:
                activity_level = "Unknown"
            
            result = {
                "activity_level": activity_level,
                "confidence": parsed.get("confidence", "Medium"),
                "reasoning": parsed.get("analysis", content[:500]),
                "raw_response": content
            }
            
            logger.info(f"Activity classified: {activity_level} (confidence: {result['confidence']})")
            return result
        
        except Exception as e:
            logger.error(f"Error in activity classification", error=str(e))
            return {
                "activity_level": "Unknown",
                "confidence": "Low",
                "reasoning": f"Error: {str(e)}",
                "error": str(e)
            }
    
    def _extract_activity_level(self, text: str) -> str:
        """Extract activity level from text using keywords"""
        text_lower = text.lower()
        
        # Keyword matching (fallback)
        if any(word in text_lower for word in ["active", "operational", "operating", "current"]):
            return "Active"
        elif any(word in text_lower for word in ["dormant", "inactive", "no activity"]):
            return "Dormant"
        elif any(word in text_lower for word in ["suspended", "suspension"]):
            return "Suspended"
        elif any(word in text_lower for word in ["discontinued", "closed", "shut down"]):
            return "Inactive"
        else:
            return "Unknown"


class RiskClassifier:
    """Classifies business risk levels"""
    
    def __init__(self, config: Optional[AIConfig] = None, llm_client: Optional[LLMClient] = None):
        """Initialize risk classifier"""
        self.config = config or AIConfig()
        self.llm_client = llm_client or LLMClient(config)
        self.parser = ResponseParser()
        logger.info("RiskClassifier initialized")
    
    def assess_risk(
        self,
        company_name: str,
        country: str,
        evidence_text: str,
        sanctions_info: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess risk level
        
        Args:
            company_name: Company name
            country: Country code
            evidence_text: Evidence text
            sanctions_info: Optional sanctions information
            additional_context: Optional additional context
        
        Returns:
            Risk assessment with risk_score and flags
        """
        try:
            prompt = PromptTemplates.risk_assessment_prompt(
                company_name=company_name,
                country=country,
                evidence_text=evidence_text,
                sanctions_info=sanctions_info
            )
            
            system_prompt = PromptTemplates.SYSTEM_PROMPT_BASE + "\n\nFocus on risk and compliance assessment."
            
            response = self.llm_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            if response.get("error"):
                logger.error(f"LLM error in risk assessment", error=response.get("error"))
                return {
                    "risk_score": 0.5,
                    "risk_level": "Medium",
                    "flags": [],
                    "error": response.get("error")
                }
            
            content = response.get("content", "")
            if not content:
                return {
                    "risk_score": 0.5,
                    "risk_level": "Medium",
                    "flags": []
                }
            
            # Parse response
            parsed = self.parser.parse_lob_response(content)
            
            # Extract risk score
            risk_score = parsed.get("risk_score")
            if risk_score is None:
                risk_score = self._calculate_risk_score(content, parsed.get("flags", []))
            
            # Determine risk level
            if risk_score >= self.config.risk_threshold_high:
                risk_level = "High"
            elif risk_score >= self.config.risk_threshold_medium:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            result = {
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "flags": parsed.get("flags", []),
                "reasoning": parsed.get("analysis", content[:500]),
                "raw_response": content
            }
            
            logger.info(f"Risk assessed: {risk_level} (score: {risk_score:.2f})")
            return result
        
        except Exception as e:
            logger.error(f"Error in risk assessment", error=str(e))
            return {
                "risk_score": 0.5,
                "risk_level": "Medium",
                "flags": [],
                "error": str(e)
            }
    
    def _calculate_risk_score(self, text: str, flags: List[str]) -> float:
        """Calculate risk score from text and flags"""
        score = 0.3  # Base risk score
        
        text_lower = text.lower()
        
        # High-risk keywords
        high_risk_keywords = [
            "sanctions", "prohibited", "illegal", "violation",
            "suspicious", "fraud", "money laundering"
        ]
        high_risk_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        score += min(high_risk_count * 0.1, 0.4)  # Max 0.4 from keywords
        
        # Medium-risk keywords
        medium_risk_keywords = [
            "concern", "issue", "risk", "warning",
            "uncertainty", "unverified"
        ]
        medium_risk_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
        score += min(medium_risk_count * 0.05, 0.2)  # Max 0.2 from keywords
        
        # Flags increase risk
        score += min(len(flags) * 0.1, 0.3)  # Max 0.3 from flags
        
        return min(score, 1.0)

