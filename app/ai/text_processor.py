"""
Text Processing Module
Handles NLP text processing, feature extraction, and entity extraction
"""

import re
from typing import Dict, List, Optional, Any
from app.core.logging import get_logger
from app.ai.config import AIConfig

logger = get_logger(__name__)


class TextProcessor:
    """Processes and extracts features from text data"""
    
    def __init__(self, config: Optional[AIConfig] = None):
        """Initialize text processor"""
        self.config = config or AIConfig()
        logger.info("TextProcessor initialized")
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        Extract features from text
        
        Args:
            text: Input text to process
        
        Returns:
            Dictionary of extracted features
        """
        if not text or len(text.strip()) < self.config.min_text_length:
            return {
                "word_count": 0,
                "char_count": 0,
                "has_company_mention": False,
                "has_location_mention": False,
                "has_activity_mention": False,
                "extracted_entities": [],
                "text_quality_score": 0.0
            }
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Extract basic features
        features = {
            "word_count": len(cleaned_text.split()),
            "char_count": len(cleaned_text),
            "has_company_mention": self._has_company_mention(cleaned_text),
            "has_location_mention": self._has_location_mention(cleaned_text),
            "has_activity_mention": self._has_activity_mention(cleaned_text),
            "extracted_entities": self._extract_entities(cleaned_text),
            "text_quality_score": self._calculate_quality_score(cleaned_text)
        }
        
        logger.debug(f"Extracted {len(features['extracted_entities'])} entities from text")
        return features
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
        
        return text.strip()
    
    def _has_company_mention(self, text: str) -> bool:
        """Check if text mentions company-related keywords"""
        company_keywords = [
            'company', 'corporation', 'corp', 'inc', 'ltd', 'limited',
            'group', 'holdings', 'enterprises', 'business', 'firm'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in company_keywords)
    
    def _has_location_mention(self, text: str) -> bool:
        """Check if text mentions location-related keywords"""
        location_keywords = [
            'country', 'city', 'region', 'address', 'located', 'headquarters',
            'office', 'branch', 'international', 'global'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in location_keywords)
    
    def _has_activity_mention(self, text: str) -> bool:
        """Check if text mentions business activity keywords"""
        activity_keywords = [
            'trade', 'import', 'export', 'commerce', 'trading', 'business',
            'operations', 'activities', 'services', 'products'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in activity_keywords)
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract entities from text (simple rule-based extraction)
        For production, use spaCy or NER models
        
        Returns:
            List of extracted entities with type and value
        """
        entities = []
        
        # Extract potential company names (capitalized words/phrases)
        company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        companies = re.findall(company_pattern, text)
        
        # Filter out common words that aren't companies
        exclude_words = {
            'The', 'This', 'That', 'These', 'Those', 'Where', 'When',
            'What', 'Who', 'Which', 'How', 'Why', 'Monday', 'Tuesday'
        }
        
        for company in companies[:10]:  # Limit to first 10
            if company not in exclude_words and len(company.split()) <= 4:
                entities.append({
                    "type": "COMPANY",
                    "value": company,
                    "confidence": 0.6
                })
        
        # Extract potential locations (countries, cities)
        # This is simplified - in production use proper NER
        location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        # Could add country/city lists here
        
        # Extract dates
        date_pattern = r'\b(\d{4})\b|\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b'
        dates = re.findall(date_pattern, text)
        for date in dates[:5]:  # Limit to first 5
            date_str = date[0] if date[0] else date[1]
            entities.append({
                "type": "DATE",
                "value": date_str,
                "confidence": 0.7
            })
        
        return entities
    
    def _calculate_quality_score(self, text: str) -> float:
        """Calculate text quality score (0.0 to 1.0)"""
        if not text or len(text) < self.config.min_text_length:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length score (longer is better, up to a point)
        length_score = min(len(text) / 1000, 1.0) * 0.2
        score += length_score
        
        # Word diversity (simple measure)
        words = text.split()
        unique_words = len(set(words))
        if len(words) > 0:
            diversity = unique_words / len(words)
            score += diversity * 0.2
        
        # Has meaningful content indicators
        if self._has_company_mention(text):
            score += 0.05
        if self._has_location_mention(text):
            score += 0.05
        if self._has_activity_mention(text):
            score += 0.05
        
        return min(score, 1.0)
    
    def prepare_text_for_llm(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Prepare text for LLM input
        
        Args:
            text: Input text
            max_length: Maximum length (defaults to config max_text_length)
        
        Returns:
            Prepared text ready for LLM
        """
        if not text:
            return ""
        
        max_len = max_length or self.config.max_text_length
        
        if len(text) > max_len:
            # Truncate but try to preserve sentences
            truncated = text[:max_len]
            last_period = truncated.rfind('.')
            if last_period > max_len * 0.8:  # If period is reasonably close
                return truncated[:last_period + 1]
            return truncated + "..."
        
        return text
    
    def aggregate_text_from_sources(self, sources: List[Dict[str, Any]]) -> str:
        """
        Aggregate text from multiple sources
        
        Args:
            sources: List of source dictionaries with 'content' or 'text' keys
        
        Returns:
            Aggregated text
        """
        texts = []
        
        for source in sources:
            content = source.get('content') or source.get('text') or source.get('data', {})
            
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, dict):
                # Try to extract text from dict
                text = content.get('text') or content.get('description') or str(content)
                texts.append(text)
        
        aggregated = "\n\n".join(texts)
        return self.prepare_text_for_llm(aggregated)

