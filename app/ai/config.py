"""
AI/ML Configuration
Settings for LLM APIs, model parameters, and AI processing
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIConfig(BaseSettings):
    """AI/ML configuration settings"""
    
    # LLM Provider Settings
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # openai or ollama
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # OpenAI Settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Ollama Settings (Local LLM)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Feature Extraction
    min_text_length: int = 50  # Minimum text length for analysis
    max_text_length: int = 8000  # Maximum text length (will be truncated)
    
    # Activity Classification
    activity_classes: list = [
        "Active",
        "Dormant",
        "Inactive",
        "Suspended",
        "Unknown"
    ]
    
    # Risk Scoring
    risk_threshold_high: float = 0.7
    risk_threshold_medium: float = 0.4
    
    # Flag Generation
    enable_flag_generation: bool = True
    flag_categories: list = [
        "compliance_issue",
        "sanctions_match",
        "suspicious_activity",
        "data_quality",
        "source_reliability"
    ]
    
    # Confidence Scoring
    min_confidence_threshold: float = 0.5
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
        "env_prefix": "AI_"
    }
    
    def __init__(self, **kwargs):
        """Initialize config"""
        super().__init__(**kwargs)

