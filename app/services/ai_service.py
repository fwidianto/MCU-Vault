"""
AI Service Layer for Phase 3A - Health Intelligence.
Provider-agnostic AI interface supporting OpenAI, Anthropic, and Local LLMs.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
import logging

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class AIProviderUnavailableError(AIProviderError):
    """Raised when AI provider is not configured or unavailable."""
    pass


class AIProviderResponseError(AIProviderError):
    """Raised when AI provider returns an error response."""
    pass


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.
    All providers must implement these methods.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate a response from the AI.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    def format_health_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format health metrics for AI consumption."""
        lines = ["Health Metrics:"]
        for key, value in metrics.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def format_comparison(self, current: Dict[str, Any], previous: Dict[str, Any]) -> str:
        """Format two health metric sets for comparison."""
        lines = ["Current MCU:"]
        for key, value in current.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
        
        lines.append("\nPrevious MCU:")
        for key, value in previous.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI provider implementation.
    Supports GPT-4, GPT-4 Turbo, and GPT-3.5 models.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o')
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            from openai import OpenAI
            if self._client is None:
                self._client = OpenAI(api_key=self.api_key)
            return True
        except ImportError:
            logger.warning("OpenAI package not installed")
            return False
        except Exception as e:
            logger.error(f"OpenAI availability check failed: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.is_available():
            raise AIProviderUnavailableError("OpenAI is not configured")
        
        from openai import OpenAI
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise AIProviderResponseError(f"OpenAI error: {e}")


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic provider implementation.
    Supports Claude 3.5 Sonnet, Claude 3 Opus, and Claude 3 Haiku.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "Anthropic"
    
    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            from anthropic import Anthropic
            if self._client is None:
                self._client = Anthropic(api_key=self.api_key)
            return True
        except ImportError:
            logger.warning("Anthropic package not installed")
            return False
        except Exception as e:
            logger.error(f"Anthropic availability check failed: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.is_available():
            raise AIProviderUnavailableError("Anthropic is not configured")
        
        from anthropic import Anthropic
        
        try:
            client = Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 2000),
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise AIProviderResponseError(f"Anthropic error: {e}")


class LocalLLMProvider(BaseAIProvider):
    """
    Local LLM provider implementation.
    Supports Ollama, LM Studio, and other OpenAI-compatible local APIs.
    """
    
    def __init__(self):
        self.base_url = os.environ.get('LOCAL_LLM_URL', 'http://localhost:11434/v1')
        self.api_key = os.environ.get('LOCAL_LLM_API_KEY', 'not-needed')
        self.model = os.environ.get('LOCAL_LLM_MODEL', 'llama3.2')
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "Local LLM"
    
    def is_available(self) -> bool:
        try:
            import requests
            # Try to ping the base URL
            response = requests.get(
                self.base_url.replace('/v1', '/api/tags'),
                timeout=5
            )
            return response.status_code == 200
        except ImportError:
            logger.warning("requests package not installed for Local LLM check")
            return False
        except Exception as e:
            logger.error(f"Local LLM availability check failed: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        if not self.is_available():
            raise AIProviderUnavailableError("Local LLM is not available")
        
        try:
            import requests
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": kwargs.get('temperature', 0.7),
                    "max_tokens": kwargs.get('max_tokens', 2000)
                },
                timeout=kwargs.get('timeout', 120)
            )
            
            if response.status_code != 200:
                raise AIProviderResponseError(f"Local LLM error: {response.status_code}")
            
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Local LLM generation error: {e}")
            raise AIProviderResponseError(f"Local LLM error: {e}")


class AIService:
    """
    Main AI service that provides a unified interface to AI providers.
    Automatically selects the first available provider.
    """
    
    # Provider priority order
    PROVIDER_ORDER = [
        OpenAIProvider,
        AnthropicProvider,
        LocalLLMProvider
    ]
    
    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all available providers."""
        for provider_class in self.PROVIDER_ORDER:
            try:
                provider = provider_class()
                self._providers[provider.provider_name] = provider
                logger.info(f"Initialized AI provider: {provider.provider_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize {provider_class.__name__}: {e}")
    
    @property
    def available_providers(self) -> List[str]:
        """Return list of available provider names."""
        return [name for name, provider in self._providers.items() if provider.is_available()]
    
    @property
    def active_provider_name(self) -> Optional[str]:
        """Return the name of the active (first available) provider."""
        available = self.available_providers
        return available[0] if available else None
    
    @property
    def is_available(self) -> bool:
        """Check if any AI provider is available."""
        return len(self.available_providers) > 0
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate AI response using available provider.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            provider: Specific provider to use (optional)
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        if not self.is_available:
            raise AIProviderUnavailableError(
                "No AI provider available. Please configure OpenAI, Anthropic, or Local LLM."
            )
        
        # Use specified provider or first available
        if provider:
            if provider not in self._providers:
                raise AIProviderError(f"Unknown provider: {provider}")
            selected_provider = self._providers[provider]
            if not selected_provider.is_available():
                raise AIProviderUnavailableError(f"Provider {provider} is not available")
        else:
            # Use first available provider
            for provider_name in self.available_providers:
                selected_provider = self._providers[provider_name]
                if selected_provider.is_available():
                    break
            else:
                raise AIProviderUnavailableError("No AI provider is available")
        
        logger.info(f"Using AI provider: {selected_provider.provider_name}")
        return selected_provider.generate(prompt, system_prompt, **kwargs)
    
    def format_health_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format health metrics for AI consumption."""
        if not self.active_provider_name:
            return ""
        
        provider = self._providers.get(self.active_provider_name)
        if provider:
            return provider.format_health_metrics(metrics)
        return ""
    
    def format_comparison(self, current: Dict[str, Any], previous: Dict[str, Any]) -> str:
        """Format two health metric sets for comparison."""
        if not self.active_provider_name:
            return ""
        
        provider = self._providers.get(self.active_provider_name)
        if provider:
            return provider.format_comparison(current, previous)
        return ""


# Global AI service instance
ai_service = AIService()


def get_ai_service() -> AIService:
    """Get the global AI service instance."""
    return ai_service