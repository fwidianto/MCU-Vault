"""
Health Intelligence Service for Phase 3A.
Uses AI to generate insights from MCU health data.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from app.services.ai_service import (
    get_ai_service, 
    AIProviderUnavailableError,
    AIProviderResponseError,
    AIService
)
from app.services.ai_prompts import (
    health_summary_prompt,
    comparison_prompt,
    trend_analysis_prompt,
    timeline_narrative_prompt,
    explain_metric_prompt,
    get_metric_explanation,
    get_all_explainable_metrics,
    MEDICAL_DISCLAIMER,
    format_health_metrics_for_ai,
    format_comparison_for_ai,
    format_trend_data_for_ai
)

logger = logging.getLogger(__name__)


class HealthIntelligenceService:
    """
    Service for generating AI-powered health insights.
    Provides summaries, comparisons, trends, and explanations.
    """
    
    def __init__(self, ai_service: Optional[AIService] = None):
        self._ai_service = ai_service or get_ai_service()
    
    @property
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self._ai_service.is_available
    
    @property
    def provider_name(self) -> Optional[str]:
        """Get the active AI provider name."""
        return self._ai_service.active_provider_name
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current AI service status."""
        return {
            'available': self.is_available,
            'provider': self.provider_name,
            'explainable_metrics': get_all_explainable_metrics() if self.is_available else []
        }
    
    def generate_summary(
        self,
        patient_name: str,
        metrics: Dict[str, Any],
        record_date: str
    ) -> Dict[str, Any]:
        """
        Generate an AI health summary for a single MCU record.
        
        Args:
            patient_name: Name of the patient
            metrics: Dictionary of health metrics
            record_date: Date of the MCU record
            
        Returns:
            Dict with 'success', 'summary', and optional 'error' keys
        """
        if not self.is_available:
            return {
                'success': False,
                'error': 'AI service is not available. Please configure an AI provider.',
                'summary': None
            }
        
        try:
            system_prompt, user_prompt = health_summary_prompt(
                patient_name, metrics, record_date
            )
            
            summary = self._ai_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1500
            )
            
            # Add disclaimer
            summary_with_disclaimer = f"{summary}\n\n{MEDICAL_DISCLAIMER}"
            
            return {
                'success': True,
                'summary': summary_with_disclaimer,
                'error': None
            }
            
        except AIProviderUnavailableError as e:
            logger.error(f"AI provider unavailable: {e}")
            return {
                'success': False,
                'error': 'AI service is currently unavailable. Please try again later.',
                'summary': None
            }
        except AIProviderResponseError as e:
            logger.error(f"AI provider error: {e}")
            return {
                'success': False,
                'error': 'AI service encountered an error. Please try again.',
                'summary': None
            }
        except Exception as e:
            logger.error(f"Unexpected error generating summary: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred. Please try again.',
                'summary': None
            }
    
    def generate_comparison(
        self,
        patient_name: str,
        current: Dict[str, Any],
        previous: Dict[str, Any],
        current_date: str,
        previous_date: str
    ) -> Dict[str, Any]:
        """
        Generate an AI comparison between two MCU records.
        
        Args:
            patient_name: Name of the patient
            current: Current MCU metrics
            previous: Previous MCU metrics
            current_date: Date of current MCU
            previous_date: Date of previous MCU
            
        Returns:
            Dict with 'success', 'comparison', and optional 'error' keys
        """
        if not self.is_available:
            return {
                'success': False,
                'error': 'AI service is not available. Please configure an AI provider.',
                'comparison': None
            }
        
        try:
            system_prompt, user_prompt = comparison_prompt(
                patient_name, current, previous, current_date, previous_date
            )
            
            comparison = self._ai_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1500
            )
            
            # Add disclaimer
            comparison_with_disclaimer = f"{comparison}\n\n{MEDICAL_DISCLAIMER}"
            
            return {
                'success': True,
                'comparison': comparison_with_disclaimer,
                'error': None
            }
            
        except AIProviderUnavailableError as e:
            logger.error(f"AI provider unavailable: {e}")
            return {
                'success': False,
                'error': 'AI service is currently unavailable. Please try again later.',
                'comparison': None
            }
        except AIProviderResponseError as e:
            logger.error(f"AI provider error: {e}")
            return {
                'success': False,
                'error': 'AI service encountered an error. Please try again.',
                'comparison': None
            }
        except Exception as e:
            logger.error(f"Unexpected error generating comparison: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred. Please try again.',
                'comparison': None
            }
    
    def generate_trend_analysis(
        self,
        patient_name: str,
        records: List[Dict[str, Any]],
        start_year: int,
        end_year: int
    ) -> Dict[str, Any]:
        """
        Generate an AI trend analysis from multiple MCU records.
        
        Args:
            patient_name: Name of the patient
            records: List of MCU records with dates and metrics
            start_year: First year in the analysis
            end_year: Last year in the analysis
            
        Returns:
            Dict with 'success', 'analysis', and optional 'error' keys
        """
        if not self.is_available:
            return {
                'success': False,
                'error': 'AI service is not available. Please configure an AI provider.',
                'analysis': None
            }
        
        if len(records) < 2:
            return {
                'success': False,
                'error': 'At least 2 MCU records are needed for trend analysis.',
                'analysis': None
            }
        
        try:
            system_prompt, user_prompt = trend_analysis_prompt(
                patient_name, records, start_year, end_year
            )
            
            analysis = self._ai_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Add disclaimer
            analysis_with_disclaimer = f"{analysis}\n\n{MEDICAL_DISCLAIMER}"
            
            return {
                'success': True,
                'analysis': analysis_with_disclaimer,
                'error': None
            }
            
        except AIProviderUnavailableError as e:
            logger.error(f"AI provider unavailable: {e}")
            return {
                'success': False,
                'error': 'AI service is currently unavailable. Please try again later.',
                'analysis': None
            }
        except AIProviderResponseError as e:
            logger.error(f"AI provider error: {e}")
            return {
                'success': False,
                'error': 'AI service encountered an error. Please try again.',
                'analysis': None
            }
        except Exception as e:
            logger.error(f"Unexpected error generating trend analysis: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred. Please try again.',
                'analysis': None
            }
    
    def generate_timeline(
        self,
        patient_name: str,
        records: List[Dict[str, Any]],
        summary_by_period: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate an AI health timeline narrative.
        
        Args:
            patient_name: Name of the patient
            records: List of MCU records with dates and metrics
            summary_by_period: Dict mapping periods to brief summaries
            
        Returns:
            Dict with 'success', 'timeline', and optional 'error' keys
        """
        if not self.is_available:
            return {
                'success': False,
                'error': 'AI service is not available. Please configure an AI provider.',
                'timeline': None
            }
        
        if len(records) < 2:
            return {
                'success': False,
                'error': 'At least 2 MCU records are needed for timeline generation.',
                'timeline': None
            }
        
        try:
            system_prompt, user_prompt = timeline_narrative_prompt(
                patient_name, records, summary_by_period
            )
            
            timeline = self._ai_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=2500
            )
            
            # Add disclaimer
            timeline_with_disclaimer = f"{timeline}\n\n{MEDICAL_DISCLAIMER}"
            
            return {
                'success': True,
                'timeline': timeline_with_disclaimer,
                'error': None
            }
            
        except AIProviderUnavailableError as e:
            logger.error(f"AI provider unavailable: {e}")
            return {
                'success': False,
                'error': 'AI service is currently unavailable. Please try again later.',
                'timeline': None
            }
        except AIProviderResponseError as e:
            logger.error(f"AI provider error: {e}")
            return {
                'success': False,
                'error': 'AI service encountered an error. Please try again.',
                'timeline': None
            }
        except Exception as e:
            logger.error(f"Unexpected error generating timeline: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred. Please try again.',
                'timeline': None
            }
    
    def explain_metric(
        self,
        metric_name: str,
        metric_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate an AI explanation of a health metric.
        
        Args:
            metric_name: Name of the metric to explain
            metric_value: Optional value to include in explanation
            
        Returns:
            Dict with 'success', 'explanation', and optional 'error' keys
        """
        # First check if we have static explanation data
        static_explanation = get_metric_explanation(metric_name)
        
        if not self.is_available:
            # Return static explanation if AI is not available
            if static_explanation:
                return {
                    'success': True,
                    'explanation': self._format_static_explanation(
                        metric_name, static_explanation, metric_value
                    ),
                    'error': None,
                    'is_ai_generated': False
                }
            return {
                'success': False,
                'error': 'AI service is not available and no explanation data exists for this metric.',
                'explanation': None,
                'is_ai_generated': False
            }
        
        try:
            system_prompt, user_prompt = explain_metric_prompt(
                metric_name, metric_value
            )
            
            explanation = self._ai_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                'success': True,
                'explanation': explanation,
                'error': None,
                'is_ai_generated': True
            }
            
        except AIProviderUnavailableError as e:
            logger.error(f"AI provider unavailable: {e}")
            # Fall back to static explanation
            if static_explanation:
                return {
                    'success': True,
                    'explanation': self._format_static_explanation(
                        metric_name, static_explanation, metric_value
                    ),
                    'error': 'AI unavailable. Showing static information.',
                    'is_ai_generated': False
                }
            return {
                'success': False,
                'error': 'AI service is currently unavailable.',
                'explanation': None,
                'is_ai_generated': False
            }
        except AIProviderResponseError as e:
            logger.error(f"AI provider error: {e}")
            if static_explanation:
                return {
                    'success': True,
                    'explanation': self._format_static_explanation(
                        metric_name, static_explanation, metric_value
                    ),
                    'error': 'AI error. Showing static information.',
                    'is_ai_generated': False
                }
            return {
                'success': False,
                'error': 'AI service encountered an error.',
                'explanation': None,
                'is_ai_generated': False
            }
        except Exception as e:
            logger.error(f"Unexpected error explaining metric: {e}")
            if static_explanation:
                return {
                    'success': True,
                    'explanation': self._format_static_explanation(
                        metric_name, static_explanation, metric_value
                    ),
                    'error': 'Unexpected error. Showing static information.',
                    'is_ai_generated': False
                }
            return {
                'success': False,
                'error': 'An unexpected error occurred.',
                'explanation': None,
                'is_ai_generated': False
            }
    
    def _format_static_explanation(
        self,
        metric_name: str,
        explanation: Dict[str, Any],
        metric_value: Optional[float] = None
    ) -> str:
        """Format static explanation data into readable text."""
        lines = [
            f"## {explanation.get('name', metric_name)}",
            "",
            f"**What it is:** {explanation.get('description', 'No description available.')}",
            "",
            f"**What it means:** {explanation.get('what_it_means', 'No explanation available.')}",
            ""
        ]
        
        ranges = explanation.get('ranges', {})
        if ranges:
            lines.append("**General Reference Ranges:**")
            for key, value in ranges.items():
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        importance = explanation.get('importance', '')
        if importance:
            lines.append(f"**Why it matters:** {importance}")
            lines.append("")
        
        limitations = explanation.get('limitations', '')
        if limitations:
            lines.append(f"**Important limitations:** {limitations}")
            lines.append("")
        
        if metric_value is not None:
            lines.append(f"\n*Patient's value: {metric_value}*")
        
        lines.append(f"\n{MEDICAL_DISCLAIMER}")
        
        return "\n".join(lines)


# Global service instance
_health_intelligence_service: Optional[HealthIntelligenceService] = None


def get_health_intelligence_service() -> HealthIntelligenceService:
    """Get the global Health Intelligence service instance."""
    global _health_intelligence_service
    if _health_intelligence_service is None:
        _health_intelligence_service = HealthIntelligenceService()
    return _health_intelligence_service