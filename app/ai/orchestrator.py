"""
AI Orchestrator Module
Main orchestrator that coordinates all AI/ML components for UC1
"""

from typing import Dict, List, Optional, Any
from app.core.logging import get_logger
from app.ai.config import AIConfig
from app.ai.llm_client import LLMClient
from app.ai.text_processor import TextProcessor
from app.ai.classifier import ActivityClassifier, RiskClassifier
from app.ai.flag_generator import FlagGenerator
from app.ai.prompts import PromptTemplates, ResponseParser

logger = get_logger(__name__)


class AIOrchestrator:
    """Orchestrates AI/ML analysis for LOB verification"""
    
    def __init__(self, config: Optional[AIConfig] = None):
        """Initialize AI orchestrator"""
        self.config = config or AIConfig()
        
        # Initialize components
        self.llm_client = LLMClient(self.config)
        self.text_processor = TextProcessor(self.config)
        self.activity_classifier = ActivityClassifier(self.config, self.llm_client)
        self.risk_classifier = RiskClassifier(self.config, self.llm_client)
        self.flag_generator = FlagGenerator(self.config, self.risk_classifier)
        self.response_parser = ResponseParser()
        
        logger.info("AIOrchestrator initialized")
    
    def analyze_lob(
        self,
        input_data: Dict[str, Any],
        collected_data: Dict[str, Any],
        aggregated_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform complete LOB analysis
        
        Args:
            input_data: Input data (company_name, country, role, product)
            collected_data: Collected data from sources
            aggregated_data: Aggregated and cleaned data
        
        Returns:
            Complete analysis result with all UC1 outputs
        """
        try:
            company_name = input_data.get("client", "")
            country = input_data.get("client_country", "")
            role = input_data.get("client_role", "")
            product = input_data.get("product_name", "")
            
            logger.info(f"Starting LOB analysis for: {company_name} ({country})")
            
            # Step 1: Extract and prepare text from collected data
            evidence_text = self._prepare_evidence_text(collected_data, aggregated_data)
            
            # Step 2: Extract features
            features = self.text_processor.extract_features(evidence_text)
            
            # Step 3: Generate main AI response
            ai_response = self._generate_ai_response(
                company_name=company_name,
                country=country,
                role=role,
                product=product,
                collected_data=collected_data,
                evidence_text=evidence_text
            )
            
            # Step 4: Classify activity level
            activity_result = self.activity_classifier.classify(
                company_name=company_name,
                evidence_text=evidence_text,
                additional_context={
                    "features": features,
                    "input_data": input_data
                }
            )
            
            # Step 5: Assess risk
            sanctions_info = self._extract_sanctions_info(collected_data)
            risk_result = self.risk_classifier.assess_risk(
                company_name=company_name,
                country=country,
                evidence_text=evidence_text,
                sanctions_info=sanctions_info,
                additional_context={
                    "features": features,
                    "input_data": input_data
                }
            )
            
            # Step 6: Generate flags
            flags = self.flag_generator.generate_flags(
                company_name=company_name,
                country=country,
                evidence_text=evidence_text,
                sanctions_info=sanctions_info,
                risk_assessment=risk_result,
                additional_context={
                    "features": features,
                    "input_data": input_data,
                    "collected_data": collected_data
                }
            )
            
            # Step 7: Determine if red flag (needed for confidence calculation)
            is_red_flag = self._determine_red_flag(risk_result, flags)
            
            # Step 8: Calculate confidence score (after determining red flag)
            confidence_score = self._calculate_confidence_score(
                features=features,
                activity_result=activity_result,
                risk_result=risk_result,
                evidence_text=evidence_text,
                flags=flags,
                is_red_flag=is_red_flag
            )
            
            # Step 9: Format response
            result = {
                "ai_response": ai_response.get("content", "") or ai_response.get("analysis", ""),
                "activity_level": activity_result.get("activity_level", "Unknown"),
                "flags": self.flag_generator.format_flags_for_storage(flags),
                "confidence_score": confidence_score,
                "is_red_flag": is_red_flag,
                "risk_score": risk_result.get("risk_score", 0.0),
                "risk_level": risk_result.get("risk_level", "Medium"),
                "metadata": {
                    "features": features,
                    "activity_reasoning": activity_result.get("reasoning", ""),
                    "risk_reasoning": risk_result.get("reasoning", ""),
                    "llm_metadata": ai_response.get("metadata", {})
                }
            }
            
            logger.info(
                f"LOB analysis complete",
                company=company_name,
                activity_level=result["activity_level"],
                risk_level=result["risk_level"],
                flags_count=len(result["flags"]),
                is_red_flag=is_red_flag
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error in LOB analysis", error=str(e))
            return {
                "ai_response": f"Error in analysis: {str(e)}",
                "activity_level": "Unknown",
                "flags": [{"category": "system_error", "message": str(e)}],
                "confidence_score": "Low",
                "is_red_flag": False,
                "error": str(e)
            }
    
    def _prepare_evidence_text(
        self,
        collected_data: Dict[str, Any],
        aggregated_data: Dict[str, Any]
    ) -> str:
        """Prepare evidence text from collected data"""
        texts = []
        
        # Extract from aggregated data
        data = aggregated_data.get("data", {})
        if isinstance(data, dict):
            # Website content
            if "website_content" in data:
                texts.append(f"Website: {data['website_content'][:1000]}")
            if "description" in data:
                texts.append(f"Description: {data['description']}")
        
        # Extract from collected_data sources
        sources = collected_data.get("sources", [])
        for source in sources:
            if isinstance(source, dict):
                content = source.get("content") or source.get("text") or source.get("data")
                if content:
                    if isinstance(content, str):
                        texts.append(content[:500])
                    elif isinstance(content, dict):
                        texts.append(str(content)[:500])
        
        evidence = "\n\n".join(texts)
        
        # Prepare text for LLM (limit length)
        return self.text_processor.prepare_text_for_llm(evidence, max_length=4000)
    
    def _generate_ai_response(
        self,
        company_name: str,
        country: str,
        role: str,
        product: str,
        collected_data: Dict[str, Any],
        evidence_text: str
    ) -> Dict[str, Any]:
        """Generate main AI response"""
        # Get website text if available
        website_text = None
        data = collected_data.get("data", {})
        if isinstance(data, dict) and "website_content" in data:
            website_text = data["website_content"]
        
        prompt = PromptTemplates.lob_verification_prompt(
            company_name=company_name,
            country=country,
            role=role,
            product=product,
            collected_data=collected_data,
            website_text=website_text or evidence_text
        )
        
        response = self.llm_client.generate_response(
            prompt=prompt,
            system_prompt=PromptTemplates.SYSTEM_PROMPT_BASE
        )
        
        # Parse response
        if response.get("content"):
            parsed = self.response_parser.parse_lob_response(response["content"])
            response.update(parsed)
        
        return response
    
    def _extract_sanctions_info(self, collected_data: Dict[str, Any]) -> Optional[str]:
        """Extract sanctions information from collected data"""
        sources = collected_data.get("sources", [])
        for source in sources:
            if isinstance(source, dict):
                if source.get("name") == "sanctions_checker":
                    sanctions_data = source.get("data") or source.get("result")
                    if sanctions_data:
                        if isinstance(sanctions_data, dict):
                            if sanctions_data.get("match"):
                                return f"Sanctions match found: {sanctions_data}"
                        else:
                            return str(sanctions_data)
        
        return None
    
    def _calculate_confidence_score(
        self,
        features: Dict[str, Any],
        activity_result: Dict[str, Any],
        risk_result: Dict[str, Any],
        evidence_text: str,
        flags: Optional[List[Dict[str, Any]]] = None,
        is_red_flag: Optional[bool] = None
    ) -> str:
        """
        Calculate overall confidence score
        
        NOTE: High confidence = Strong evidence found (even if negative)
        - Sanctions match = HIGH confidence (we found concrete evidence)
        - Red flags = HIGH confidence (we found clear risk indicators)
        - Limited evidence = LOW confidence (but sanctions match overrides this)
        """
        flags = flags or []
        
        # Check for sanctions match - this is STRONG evidence (high confidence)
        sanctions_flags = [
            flag for flag in flags
            if flag.get("category") == "sanctions_match"
        ]
        if sanctions_flags:
            # Sanctions match is concrete evidence, so HIGH confidence
            return "High"
        
        # Red flag with concrete evidence = HIGH confidence
        if is_red_flag:
            # If we have a red flag, we found clear evidence, so HIGH confidence
            return "High"
        
        # Base confidence from text quality
        quality_score = features.get("text_quality_score", 0.0)
        
        # Confidence from activity classification
        activity_confidence = activity_result.get("confidence", "Medium")
        activity_scores = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
        activity_score = activity_scores.get(activity_confidence, 0.6)
        
        # Confidence from evidence quantity
        evidence_score = min(len(evidence_text) / 1000, 1.0) * 0.3
        
        # Calculate combined score
        combined_score = (quality_score * 0.3) + (activity_score * 0.4) + (evidence_score * 0.3)
        
        # Map to confidence level
        if combined_score >= 0.7:
            return "High"
        elif combined_score >= 0.4:
            return "Medium"
        else:
            return "Low"
    
    def _determine_red_flag(
        self,
        risk_result: Dict[str, Any],
        flags: List[Dict[str, Any]]
    ) -> bool:
        """Determine if this is a red flag case"""
        # High risk score
        if risk_result.get("risk_score", 0.0) >= self.config.risk_threshold_high:
            return True
        
        # High severity flags
        high_severity_flags = [
            flag for flag in flags
            if flag.get("severity") == "high"
        ]
        if len(high_severity_flags) >= 2:  # 2+ high severity flags
            return True
        
        # Sanctions match
        sanctions_flags = [
            flag for flag in flags
            if flag.get("category") == "sanctions_match"
        ]
        if sanctions_flags:
            return True
        
        return False

