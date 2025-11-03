"""
Prompt Templates for LLM Queries
Templates for different analysis tasks
"""

from typing import Dict, Any, Optional


class PromptTemplates:
    """Prompt templates for LLM analysis"""
    
    # System prompts
    SYSTEM_PROMPT_BASE = """You are an expert analyst for Trade-Based Anti-Money Laundering (TBAML) compliance verification. 
Your role is to analyze company information and provide accurate, objective assessments of business legitimacy and activity levels.

Guidelines:
- Provide factual, evidence-based analysis
- Focus on verifiable information from provided sources
- Identify any compliance concerns or red flags
- Be objective and avoid speculation
- Cite specific evidence for your conclusions"""
    
    # UC1: LOB Verification Prompts
    @staticmethod
    def lob_verification_prompt(
        company_name: str,
        country: str,
        role: str,
        product: str,
        collected_data: Dict[str, Any],
        website_text: Optional[str] = None
    ) -> str:
        """
        Generate prompt for LOB verification
        
        Args:
            company_name: Company name
            country: Country code
            role: Import/Export role
            product: Product name
            collected_data: Collected data from sources
            website_text: Optional website content
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following company for Line of Business (LOB) verification:

COMPANY INFORMATION:
- Name: {company_name}
- Country: {country}
- Role: {role}
- Product: {product}

COLLECTED DATA:
"""
        
        # Add website information
        if website_text:
            prompt += f"""
WEBSITE CONTENT:
{website_text[:2000]}  # Limit length
"""
        
        # Add sources summary
        sources = collected_data.get("sources", [])
        if sources:
            prompt += f"""
DATA SOURCES:
{len(sources)} source(s) were consulted:
"""
            for i, source in enumerate(sources[:5], 1):  # Limit to 5 sources
                source_name = source.get("name", "Unknown") if isinstance(source, dict) else str(source)
                prompt += f"  {i}. {source_name}\n"
        
        prompt += """
ANALYSIS REQUIRED:
Please provide a comprehensive analysis including:

1. BUSINESS LEGITIMACY ASSESSMENT:
   - Is this a legitimate business operation?
   - Is there evidence of actual business activity?
   - Are there any concerns about the business legitimacy?

2. ACTIVITY LEVEL CLASSIFICATION:
   - Classify as one of: Active, Dormant, Inactive, Suspended, Unknown
   - Provide reasoning for the classification

3. RISK INDICATORS:
   - Identify any compliance concerns
   - Flag any suspicious patterns
   - Note any data quality issues

4. CONFIDENCE LEVEL:
   - Rate your confidence in this assessment (High, Medium, Low)
   - Explain any limitations in the available data

Please provide your analysis in a clear, structured format."""

        return prompt
    
    @staticmethod
    def activity_classification_prompt(
        company_name: str,
        evidence_text: str
    ) -> str:
        """Generate prompt for activity level classification"""
        prompt = f"""Classify the business activity level for: {company_name}

Based on the following evidence:
{evidence_text[:1500]}

Classify the business as one of:
- Active: Business is currently operational with evidence of recent activity
- Dormant: Business exists but shows no recent activity
- Inactive: Business appears to be inactive or discontinued
- Suspended: Business operations are suspended
- Unknown: Insufficient data to determine status

Provide:
1. Classification (one of the above)
2. Confidence level (High/Medium/Low)
3. Key evidence supporting your classification"""
        
        return prompt
    
    @staticmethod
    def risk_assessment_prompt(
        company_name: str,
        country: str,
        evidence_text: str,
        sanctions_info: Optional[str] = None
    ) -> str:
        """Generate prompt for risk assessment"""
        prompt = f"""Assess compliance and risk indicators for: {company_name} ({country})

EVIDENCE:
{evidence_text[:1500]}

"""
        
        if sanctions_info:
            prompt += f"""SANCTIONS INFORMATION:
{sanctions_info}

"""
        
        prompt += """Identify:
1. Compliance issues (if any)
2. Risk indicators
3. Data quality concerns
4. Source reliability issues

Format your response with specific flags/categories."""
        
        return prompt
    
    @staticmethod
    def generate_structured_response() -> str:
        """Prompt for structured JSON response"""
        return """Please provide your response in the following JSON format:

{
  "analysis": "Your detailed analysis text here",
  "activity_level": "Active|Dormant|Inactive|Suspended|Unknown",
  "confidence": "High|Medium|Low",
  "flags": ["flag1", "flag2"],
  "risk_score": 0.0-1.0,
  "evidence_cited": ["evidence1", "evidence2"]
}

Ensure the response is valid JSON."""


class ResponseParser:
    """Parse LLM responses into structured format"""
    
    @staticmethod
    def parse_lob_response(response: str) -> Dict[str, Any]:
        """
        Parse LOB verification response
        
        Args:
            response: LLM response text
        
        Returns:
            Parsed structured data
        """
        import json
        import re
        
        # Try to extract JSON if present
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return parsed
            except json.JSONDecodeError:
                pass
        
        # Fallback: Extract key information from text
        parsed = {
            "analysis": response,
            "activity_level": None,
            "confidence": None,
            "flags": [],
            "risk_score": None
        }
        
        # Try to extract activity level
        activity_match = re.search(
            r'(?:Activity|Classification|Status).*?:\s*(Active|Dormant|Inactive|Suspended|Unknown)',
            response,
            re.IGNORECASE
        )
        if activity_match:
            parsed["activity_level"] = activity_match.group(1).capitalize()
        
        # Try to extract confidence
        confidence_match = re.search(
            r'(?:Confidence|Confidence Level).*?:\s*(High|Medium|Low)',
            response,
            re.IGNORECASE
        )
        if confidence_match:
            parsed["confidence"] = confidence_match.group(1)
        
        # Try to extract flags
        flags_match = re.findall(
            r'(?:Flag|Issue|Concern|Alert).*?:\s*([^\n]+)',
            response,
            re.IGNORECASE
        )
        if flags_match:
            parsed["flags"] = [flag.strip() for flag in flags_match[:10]]  # Limit to 10
        
        return parsed

