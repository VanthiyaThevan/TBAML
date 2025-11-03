"""
Flag Generation Module
Generates compliance flags and alerts
"""

from typing import Dict, List, Optional, Any
from app.core.logging import get_logger
from app.ai.config import AIConfig
from app.ai.classifier import RiskClassifier

logger = get_logger(__name__)


class FlagGenerator:
    """Generates compliance flags and alerts"""
    
    def __init__(self, config: Optional[AIConfig] = None, risk_classifier: Optional[RiskClassifier] = None):
        """Initialize flag generator"""
        self.config = config or AIConfig()
        self.risk_classifier = risk_classifier or RiskClassifier(config)
        logger.info("FlagGenerator initialized")
    
    def generate_flags(
        self,
        company_name: str,
        country: str,
        evidence_text: str,
        sanctions_info: Optional[str] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate flags and alerts
        
        Args:
            company_name: Company name
            country: Country code
            evidence_text: Evidence text
            sanctions_info: Optional sanctions information
            risk_assessment: Optional risk assessment (if already computed)
            additional_context: Optional additional context
        
        Returns:
            List of flag dictionaries
        """
        flags = []
        
        try:
            # Get risk assessment if not provided
            if not risk_assessment:
                risk_assessment = self.risk_classifier.assess_risk(
                    company_name=company_name,
                    country=country,
                    evidence_text=evidence_text,
                    sanctions_info=sanctions_info,
                    additional_context=additional_context
                )
            
            # Generate flags based on risk assessment
            risk_flags = self._generate_risk_flags(risk_assessment)
            flags.extend(risk_flags)
            
            # Generate compliance flags
            compliance_flags = self._generate_compliance_flags(
                company_name=company_name,
                country=country,
                evidence_text=evidence_text,
                sanctions_info=sanctions_info
            )
            flags.extend(compliance_flags)
            
            # Generate data quality flags
            data_quality_flags = self._generate_data_quality_flags(
                evidence_text=evidence_text,
                additional_context=additional_context
            )
            flags.extend(data_quality_flags)
            
            logger.info(f"Generated {len(flags)} flags for {company_name}")
            return flags
        
        except Exception as e:
            logger.error(f"Error generating flags", error=str(e))
            return [{
                "category": "system_error",
                "severity": "medium",
                "message": f"Error in flag generation: {str(e)}"
            }]
    
    def _generate_risk_flags(self, risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate flags based on risk assessment"""
        flags = []
        
        risk_score = risk_assessment.get("risk_score", 0.0)
        risk_level = risk_assessment.get("risk_level", "Low")
        
        if risk_score >= self.config.risk_threshold_high:
            flags.append({
                "category": "high_risk",
                "severity": "high",
                "message": f"High risk identified (score: {risk_score:.2f})",
                "risk_level": risk_level
            })
        
        assessment_flags = risk_assessment.get("flags", [])
        for flag_text in assessment_flags:
            flags.append({
                "category": "risk_indicator",
                "severity": "medium" if risk_score < 0.7 else "high",
                "message": str(flag_text),
                "source": "risk_assessment"
            })
        
        return flags
    
    def _generate_compliance_flags(
        self,
        company_name: str,
        country: str,
        evidence_text: str,
        sanctions_info: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate compliance-related flags"""
        flags = []
        
        evidence_lower = evidence_text.lower()
        
        # Check for sanctions
        if sanctions_info:
            if "sanctions" in sanctions_info.lower() or "prohibited" in sanctions_info.lower():
                flags.append({
                    "category": "sanctions_match",
                    "severity": "high",
                    "message": "Potential sanctions match detected",
                    "details": sanctions_info[:200]
                })
        
        # Check for common compliance concerns
        compliance_keywords = {
            "unregistered": ("compliance_issue", "Company may be unregistered"),
            "no website": ("data_quality", "No website found - limited verification"),
            "insufficient data": ("data_quality", "Insufficient data for verification"),
            "suspicious": ("suspicious_activity", "Suspicious activity indicators"),
        }
        
        for keyword, (category, message) in compliance_keywords.items():
            if keyword in evidence_lower:
                flags.append({
                    "category": category,
                    "severity": "medium",
                    "message": message
                })
        
        return flags
    
    def _generate_data_quality_flags(
        self,
        evidence_text: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate data quality flags"""
        flags = []
        
        # Check text length
        if not evidence_text or len(evidence_text.strip()) < 100:
            flags.append({
                "category": "data_quality",
                "severity": "low",
                "message": "Limited evidence available - low data quality"
            })
        
        # Check source reliability
        if additional_context:
            sources = additional_context.get("sources", [])
            if not sources or len(sources) < 2:
                flags.append({
                    "category": "source_reliability",
                    "severity": "medium",
                    "message": "Limited number of data sources"
                })
        
        return flags
    
    def format_flags_for_storage(self, flags: List[Dict[str, Any]]) -> List[str]:
        """
        Format flags for storage in database
        
        Args:
            flags: List of flag dictionaries
        
        Returns:
            List of formatted flag strings
        """
        formatted = []
        for flag in flags:
            category = flag.get("category", "unknown")
            severity = flag.get("severity", "medium")
            message = flag.get("message", "")
            formatted.append(f"[{severity.upper()}] {category}: {message}")
        
        return formatted

