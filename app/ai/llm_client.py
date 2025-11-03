"""
LLM Client Module
Handles integration with OpenAI and Ollama
"""

from typing import Dict, Optional, Any
import openai
from app.core.logging import get_logger
from app.ai.config import AIConfig

logger = get_logger(__name__)


class LLMClient:
    """Client for interacting with OpenAI or Ollama"""
    
    def __init__(self, config: Optional[AIConfig] = None):
        """Initialize LLM client"""
        self.config = config or AIConfig()
        
        if self.config.llm_provider == "openai":
            openai.api_key = self.config.openai_api_key
            logger.info(f"LLMClient initialized with OpenAI model: {self.config.llm_model}")
        else:
            logger.info(f"LLMClient initialized with Ollama model: {self.config.llm_model}")
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate response from LLM (OpenAI or Ollama)
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature for generation (defaults to config)
            max_tokens: Max tokens for response (defaults to config)
        
        Returns:
            Dictionary with 'content' and 'metadata'
        """
        try:
            if self.config.llm_provider == "openai":
                return self._generate_openai(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                return self._generate_ollama(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
        
        except Exception as e:
            logger.error(f"Error generating LLM response", error=str(e))
            return {
                "content": None,
                "error": str(e),
                "metadata": {
                    "provider": self.config.llm_provider,
                    "model": self.config.llm_model
                }
            }
            
    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate response using OpenAI"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = openai.chat.completions.create(
                model=self.config.llm_model,
                messages=messages,
                temperature=temperature or self.config.llm_temperature,
                max_tokens=max_tokens or self.config.llm_max_tokens
            )
            
            content = response.choices[0].message.content
            
            return {
                "content": content,
                "metadata": {
                    "provider": "openai",
                    "model": self.config.llm_model,
                    "tokens_used": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error", error=str(e))
            return {
                "content": None,
                "error": str(e),
                "metadata": {"provider": "openai", "model": self.config.llm_model}
            }
    
    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate response using Ollama (local LLM)"""
        try:
            import requests
            
            base_url = self.config.ollama_base_url
            model = self.config.ollama_model
            
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Ollama API endpoint
            url = f"{base_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature or self.config.ollama_temperature,
                    "num_predict": max_tokens or self.config.ollama_max_tokens
                }
            }
            
            logger.debug(f"Calling Ollama API: {url} with model {model}")
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "")
            
            # Calculate tokens (Ollama provides this)
            tokens_used = result.get("eval_count", 0) + result.get("prompt_eval_count", 0)
            
            logger.debug(
                f"Ollama response generated",
                model=model,
                tokens_used=tokens_used
            )
            
            return {
                "content": content,
                "metadata": {
                    "provider": "ollama",
                    "model": model,
                    "tokens_used": tokens_used,
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0)
                }
            }
        
        except ImportError:
            logger.error("requests library not installed. Install with: pip install requests")
            return {
                "content": None,
                "error": "requests library not installed",
                "metadata": {"provider": "ollama"}
            }
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Make sure Ollama is running.")
            return {
                "content": None,
                "error": "Cannot connect to Ollama. Make sure Ollama is running on localhost:11434",
                "metadata": {"provider": "ollama"}
            }
        except Exception as e:
            logger.error(f"Ollama API error", error=str(e))
            return {
                "content": None,
                "error": str(e),
                "metadata": {"provider": "ollama"}
            }
