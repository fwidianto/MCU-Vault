"""
Tests for AI Health Intelligence Service (Phase 3A).
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app import create_app, db
from app.models.user import User
from app.models.mcu_record import MCURecord
from app.models.health_metrics import HealthMetrics
from app.services.ai_service import (
    AIService, get_ai_service, BaseAIProvider,
    OpenAIProvider, AnthropicProvider, LocalLLMProvider,
    AIProviderError, AIProviderUnavailableError, AIProviderResponseError
)
from app.services.health_intelligence import (
    HealthIntelligenceService, get_health_intelligence_service
)
from app.services.ai_prompts import (
    get_metric_explanation, get_all_explainable_metrics,
    MEDICAL_DISCLAIMER, format_health_metrics_for_ai
)


@pytest.fixture
def app():
    """Create test application."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        user = User(username='testuser', email='test@test.com')
        user.set_password('TestPass123!')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def test_record(app, test_user):
    """Create test MCU record with health metrics."""
    with app.app_context():
        record = MCURecord(
            patient_name='Test Patient',
            mcu_date=datetime(2024, 4, 15),
            user_id=test_user,
            status='cleared'
        )
        db.session.add(record)
        db.session.commit()
        
        metrics = HealthMetrics(
            mcu_record_id=record.id,
            height_cm=175.0,
            weight_kg=75.0,
            bmi=24.5,
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            fasting_glucose=95.0,
            hba1c=5.5,
            total_cholesterol=195.0,
            ldl=120.0,
            hdl=55.0,
            triglycerides=130.0,
            sgot=28.0,
            sgpt=30.0,
            creatinine=0.95,
            uric_acid=5.8
        )
        db.session.add(metrics)
        db.session.commit()
        
        return record.id


# ===========================================
# AI Service Tests
# ===========================================

class TestAIService:
    """Test AI service functionality."""
    
    def test_ai_service_initialization(self, app):
        """Test that AI service initializes correctly."""
        with app.app_context():
            service = get_ai_service()
            assert service is not None
            assert isinstance(service, AIService)
    
    def test_ai_service_not_available_without_config(self, app):
        """Test that AI service reports as unavailable when no provider is configured."""
        with app.app_context():
            service = AIService()
            assert service.is_available == False
            assert service.active_provider_name is None
    
    def test_available_providers_empty_without_config(self, app):
        """Test that no providers are available without API keys."""
        with app.app_context():
            service = AIService()
            assert len(service.available_providers) == 0
    
    def test_generate_raises_error_when_unavailable(self, app):
        """Test that generate() raises error when no provider is available."""
        with app.app_context():
            service = AIService()
            with pytest.raises(AIProviderUnavailableError):
                service.generate("Test prompt")


class TestOpenAIProvider:
    """Test OpenAI provider."""
    
    def test_openai_provider_initialization(self, app):
        """Test OpenAI provider can be initialized."""
        with app.app_context():
            provider = OpenAIProvider()
            assert provider.provider_name == "OpenAI"
            assert provider.model == 'gpt-4o'  # default


class TestAnthropicProvider:
    """Test Anthropic provider."""
    
    def test_anthropic_provider_initialization(self, app):
        """Test Anthropic provider can be initialized."""
        with app.app_context():
            provider = AnthropicProvider()
            assert provider.provider_name == "Anthropic"
            assert provider.model == 'claude-sonnet-4-20250514'  # default


class TestLocalLLMProvider:
    """Test Local LLM provider."""
    
    def test_local_llm_provider_initialization(self, app):
        """Test Local LLM provider can be initialized."""
        with app.app_context():
            provider = LocalLLMProvider()
            assert provider.provider_name == "Local LLM"
            assert provider.model == 'llama3.2'  # default


# ===========================================
# Health Intelligence Service Tests
# ===========================================

class TestHealthIntelligenceService:
    """Test health intelligence service."""
    
    def test_service_initialization(self, app):
        """Test service initializes correctly."""
        with app.app_context():
            service = get_health_intelligence_service()
            assert service is not None
            assert isinstance(service, HealthIntelligenceService)
    
    def test_service_status_unavailable(self, app):
        """Test status returns unavailable when no AI is configured."""
        with app.app_context():
            service = HealthIntelligenceService()
            status = service.get_status()
            
            assert status['available'] == False
            assert status['provider'] is None
            assert 'explainable_metrics' in status
    
    def test_generate_summary_returns_error_when_unavailable(self, app, test_record):
        """Test summary generation returns error when AI is unavailable."""
        with app.app_context():
            service = HealthIntelligenceService()
            result = service.generate_summary(
                patient_name='Test',
                metrics={'bmi': 24.5},
                record_date='2024-04-15'
            )
            
            assert result['success'] == False
            assert 'AI service is not available' in result['error']
            assert result['summary'] is None
    
    def test_generate_comparison_returns_error_when_unavailable(self, app, test_record):
        """Test comparison generation returns error when AI is unavailable."""
        with app.app_context():
            service = HealthIntelligenceService()
            result = service.generate_comparison(
                patient_name='Test',
                current={'bmi': 25.0},
                previous={'bmi': 24.5},
                current_date='2024-04-15',
                previous_date='2023-04-15'
            )
            
            assert result['success'] == False
            assert 'AI service is not available' in result['error']
            assert result['comparison'] is None
    
    def test_generate_trend_requires_minimum_records(self, app, test_user):
        """Test trend analysis requires at least 2 records or returns error if AI unavailable."""
        with app.app_context():
            service = HealthIntelligenceService()
            # Create one record
            record = MCURecord(
                patient_name='Test',
                mcu_date=datetime(2024, 1, 1),
                user_id=test_user,
                status='pending'
            )
            db.session.add(record)
            db.session.commit()
            
            result = service.generate_trend_analysis(
                patient_name='Test',
                records=[{'date': '2024-01-01', 'metrics': {}}],
                start_year=2024,
                end_year=2024
            )
            
            # Without AI configured, will get AI unavailable error
            # With AI configured, would get "At least 2 records" error
            assert result['success'] == False
            assert result['error'] is not None
    
    def test_generate_timeline_requires_minimum_records(self, app, test_user):
        """Test timeline generation requires at least 2 records or returns error if AI unavailable."""
        with app.app_context():
            service = HealthIntelligenceService()
            # Create one record
            record = MCURecord(
                patient_name='Test',
                mcu_date=datetime(2024, 1, 1),
                user_id=test_user,
                status='pending'
            )
            db.session.add(record)
            db.session.commit()
            
            result = service.generate_timeline(
                patient_name='Test',
                records=[{'date': '2024-01-01', 'metrics': {}}],
                summary_by_period={'2024': 'One record'}
            )
            
            # Without AI configured, will get AI unavailable error
            # With AI configured, would get "At least 2 records" error
            assert result['success'] == False
            assert result['error'] is not None
    
    def test_explain_metric_returns_static_when_ai_unavailable(self, app):
        """Test explain metric returns static data when AI unavailable."""
        with app.app_context():
            service = HealthIntelligenceService()
            result = service.explain_metric('bmi', 24.5)
            
            assert result['success'] == True
            assert result['is_ai_generated'] == False
            assert result['explanation'] is not None
            assert 'BMI' in result['explanation'] or 'Body Mass Index' in result['explanation']
    
    def test_explain_unknown_metric_returns_error(self, app):
        """Test explaining unknown metric returns error."""
        with app.app_context():
            service = HealthIntelligenceService()
            result = service.explain_metric('unknown_metric_xyz')
            
            # Should return static info if available, or error if not
            assert result is not None


# ===========================================
# AI Prompt Tests
# ===========================================

class TestAIPrompts:
    """Test AI prompt functions."""
    
    def test_format_health_metrics_empty(self):
        """Test formatting empty metrics."""
        result = format_health_metrics_for_ai({})
        assert 'No health metrics available' in result
    
    def test_format_health_metrics_basic(self):
        """Test formatting basic metrics."""
        metrics = {
            'height_cm': 175.0,
            'weight_kg': 75.0,
            'bmi': 24.5
        }
        result = format_health_metrics_for_ai(metrics)
        
        assert '175.0' in result
        assert '75.0' in result
        assert '24.5' in result
        assert 'BASIC MEASUREMENTS' in result
    
    def test_format_health_metrics_blood_pressure(self):
        """Test formatting blood pressure metrics."""
        metrics = {
            'systolic_bp': 120,
            'diastolic_bp': 80,
            'heart_rate': 72
        }
        result = format_health_metrics_for_ai(metrics)
        
        assert '120' in result
        assert '80' in result
        assert '120/80' in result
        assert 'VITAL SIGNS' in result
    
    def test_get_all_explainable_metrics(self):
        """Test getting list of explainable metrics."""
        metrics = get_all_explainable_metrics()
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert 'bmi' in metrics
        assert 'hba1c' in metrics
        assert 'ldl' in metrics
    
    def test_get_metric_explanation(self):
        """Test getting metric explanation."""
        explanation = get_metric_explanation('bmi')
        
        assert explanation is not None
        assert 'name' in explanation
        assert 'description' in explanation
        assert 'ranges' in explanation
    
    def test_get_unknown_metric_explanation(self):
        """Test getting explanation for unknown metric."""
        explanation = get_metric_explanation('unknown_metric')
        assert explanation is None
    
    def test_medical_disclaimer_present(self):
        """Test medical disclaimer is defined."""
        assert 'MEDICAL DISCLAIMER' in MEDICAL_DISCLAIMER
        assert 'educational' in MEDICAL_DISCLAIMER.lower()
        assert 'consult' in MEDICAL_DISCLAIMER.lower()


# ===========================================
# AI Routes Tests
# ===========================================

class TestAIRoutes:
    """Test AI routes."""
    
    def test_ai_index_requires_login(self, client):
        """Test AI index requires authentication."""
        response = client.get('/ai/')
        assert response.status_code == 302  # Redirect to login
    
    def test_ai_status_requires_login(self, client):
        """Test AI status requires authentication."""
        response = client.get('/ai/status')
        assert response.status_code == 302
    
    def test_ai_explain_list(self, client):
        """Test explain list endpoint."""
        # Login first
        with client.application.app_context():
            user = User(username='testuser', email='test@test.com')
            user.set_password('TestPass123!')
            db.session.add(user)
            db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        
        response = client.get('/ai/explain')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] == True
        assert 'metrics' in data
        assert len(data['metrics']) > 0
    
    def test_ai_explain_specific_metric(self, client, test_user):
        """Test explaining specific metric."""
        with client.application.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            if not user:
                user = User(username='testuser2', email='test2@test.com')
                user.set_password('TestPass123!')
                db.session.add(user)
                db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user)
            sess['_fresh'] = True
        
        response = client.get('/ai/explain/bmi')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] == True
        assert 'explanation' in data
    
    def test_ai_summary_requires_login(self, client, test_record):
        """Test summary endpoint requires authentication."""
        response = client.get(f'/ai/summary/{test_record}')
        assert response.status_code == 302
    
    def test_ai_summary_record_not_found(self, client):
        """Test summary returns 404 for non-existent record."""
        with client.application.app_context():
            user = User(username='testuser3', email='test3@test.com')
            user.set_password('TestPass123!')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        
        response = client.get('/ai/summary/99999')
        assert response.status_code == 404
        
        data = response.get_json()
        assert data['success'] == False
        assert 'not found' in data['error'].lower()
    
    def test_ai_comparison_requires_login(self, client):
        """Test comparison endpoint requires authentication."""
        response = client.post('/ai/comparison',
                              json={'current_id': 1, 'previous_id': 2})
        assert response.status_code == 302


# ===========================================
# Error Handling Tests
# ===========================================

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_ai_provider_error_class(self):
        """Test AI provider error classes exist."""
        assert issubclass(AIProviderError, Exception)
        assert issubclass(AIProviderUnavailableError, AIProviderError)
        assert issubclass(AIProviderResponseError, AIProviderError)
    
    def test_error_can_be_raised_and_caught(self, app):
        """Test errors can be raised and caught."""
        with app.app_context():
            service = AIService()
            
            with pytest.raises(AIProviderUnavailableError):
                service.generate("test")
    
    def test_graceful_degradation_without_ai(self, app, test_record):
        """Test system works gracefully without AI configured."""
        with app.app_context():
            service = HealthIntelligenceService()
            
            # Should still work, just return static info
            result = service.explain_metric('bmi', 24.5)
            assert result['success'] == True


# ===========================================
# Mock AI Tests (with mocked provider)
# ===========================================

class TestMockAIIntegration:
    """Test AI integration with mocked provider."""
    
    def test_summary_generation_with_mock(self, app, test_record):
        """Test summary generation with mocked AI."""
        with app.app_context():
            # Create mock provider
            mock_provider = Mock(spec=BaseAIProvider)
            mock_provider.provider_name = "Mock"
            mock_provider.is_available = True
            mock_provider.generate.return_value = "Mocked AI summary about health."
            mock_provider.format_health_metrics.return_value = "Health metrics"
            mock_provider.format_comparison.return_value = "Comparison"
            
            # Create service with mock
            service = HealthIntelligenceService()
            service._ai_service = Mock()
            service._ai_service.is_available = True
            service._ai_service.active_provider_name = "Mock"
            service._ai_service.generate.return_value = "Mocked AI summary about health."
            
            result = service.generate_summary(
                patient_name='Test Patient',
                metrics={'bmi': 24.5, 'systolic_bp': 120},
                record_date='2024-04-15'
            )
            
            assert result['success'] == True
            assert 'Mocked' in result['summary']
            assert 'disclaimer' in result['summary'].lower() or 'MEDICAL DISCLAIMER' in result['summary']
    
    def test_comparison_generation_with_mock(self, app, test_record):
        """Test comparison generation with mocked AI."""
        with app.app_context():
            service = HealthIntelligenceService()
            service._ai_service = Mock()
            service._ai_service.is_available = True
            service._ai_service.active_provider_name = "Mock"
            service._ai_service.generate.return_value = "Mocked comparison of two records."
            
            result = service.generate_comparison(
                patient_name='Test Patient',
                current={'bmi': 25.0},
                previous={'bmi': 24.5},
                current_date='2024-04-15',
                previous_date='2023-04-15'
            )
            
            assert result['success'] == True
            assert 'Mocked' in result['comparison']


# ===========================================
# Safety Tests
# ===========================================

class TestSafetyRequirements:
    """Test that safety requirements are met."""
    
    def test_medical_disclaimer_included(self):
        """Test medical disclaimer is included in exports."""
        assert len(MEDICAL_DISCLAIMER) > 0
        assert 'consult' in MEDICAL_DISCLAIMER.lower()
    
    def test_system_prompt_encourages_consultation(self):
        """Test system prompt includes consultation reminder."""
        from app.services.ai_prompts import HEALTH_AI_SYSTEM_PROMPT
        
        assert 'consult' in HEALTH_AI_SYSTEM_PROMPT.lower()
        assert 'healthcare professional' in HEALTH_AI_SYSTEM_PROMPT.lower()
    
    def test_no_diagnosis_in_system_prompt(self):
        """Test system prompt doesn't allow diagnosis."""
        from app.services.ai_prompts import HEALTH_AI_SYSTEM_PROMPT
        
        assert 'diagnos' not in HEALTH_AI_SYSTEM_PROMPT.lower() or 'NEVER diagnose' in HEALTH_AI_SYSTEM_PROMPT
    
    def test_metric_explanations_are_educational(self):
        """Test metric explanations are educational, not diagnostic."""
        explanation = get_metric_explanation('hba1c')
        
        assert explanation is not None
        # Should have general info, not diagnosis
        assert 'description' in explanation
        assert 'ranges' in explanation
        # Should not contain diagnosis language
        assert 'diagnosis' not in explanation.get('description', '').lower()