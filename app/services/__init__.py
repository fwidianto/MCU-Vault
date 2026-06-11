"""
Services package for MCU Vault.
"""
from app.services.ocr_mapping import FieldMapper, mapper, extract_health_metrics
from app.services.ai_service import (
    AIService, 
    get_ai_service,
    BaseAIProvider,
    OpenAIProvider,
    AnthropicProvider,
    LocalLLMProvider,
    AIProviderError,
    AIProviderUnavailableError,
    AIProviderResponseError
)
from app.services.health_intelligence import (
    HealthIntelligenceService,
    get_health_intelligence_service
)
from app.services.ai_prompts import (
    get_metric_explanation,
    get_all_explainable_metrics,
    MEDICAL_DISCLAIMER
)

__all__ = [
    # OCR
    'FieldMapper', 
    'mapper', 
    'extract_health_metrics',
    # AI
    'AIService', 
    'get_ai_service',
    'BaseAIProvider',
    'OpenAIProvider',
    'AnthropicProvider',
    'LocalLLMProvider',
    'AIProviderError',
    'AIProviderUnavailableError',
    'AIProviderResponseError',
    # Health Intelligence
    'HealthIntelligenceService',
    'get_health_intelligence_service',
    # Prompts
    'get_metric_explanation',
    'get_all_explainable_metrics',
    'MEDICAL_DISCLAIMER'
]