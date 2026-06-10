"""
OCR Tests for MCU Vault - Phase 2C

Tests OCR extraction, mapping, and record creation workflow.
"""

import pytest
from app import create_app, db
from app.models.user import User
from app.models.mcu_record import MCURecord, UploadedFile
from app.models.health_metrics import HealthMetrics
from app.services.ocr_mapping import FieldMapper, extract_health_metrics


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Create authenticated test client."""
    with app.app_context():
        user = User(username='testuser', email='test@test.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
    
    client.post('/login', data={'username': 'testuser', 'password': 'testpass123'})
    return client


class TestFieldMapper:
    """Tests for the OCR field mapping engine."""
    
    def test_extract_height(self):
        """Test height extraction from various formats."""
        mapper = FieldMapper()
        
        # Standard format
        text = "Height: 175 cm"
        value, confidence = mapper.extract_value(text, 'height_cm')
        assert value == 175.0
        assert confidence > 70
        
        # TB format (Indonesian)
        text = "TB: 180"
        value, confidence = mapper.extract_value(text, 'height_cm')
        assert value == 180.0
        
        # No unit
        text = "Height 170"
        value, confidence = mapper.extract_value(text, 'height_cm')
        assert value == 170.0
    
    def test_extract_weight(self):
        """Test weight extraction from various formats."""
        mapper = FieldMapper()
        
        # Standard format
        text = "Weight: 75 kg"
        value, confidence = mapper.extract_value(text, 'weight_kg')
        assert value == 75.0
        
        # BB format (Indonesian)
        text = "BB: 68.5"
        value, confidence = mapper.extract_value(text, 'weight_kg')
        assert value == 68.5
    
    def test_extract_blood_pressure(self):
        """Test blood pressure extraction."""
        mapper = FieldMapper()
        
        # Systolic
        text = "Systolic BP: 120 mmHg"
        value, confidence = mapper.extract_value(text, 'systolic_bp')
        assert value == 120.0
        
        # Combined format
        text = "Blood Pressure: 130/85 mmHg"
        sys_value, _ = mapper.extract_value(text, 'systolic_bp')
        dia_value, _ = mapper.extract_value(text, 'diastolic_bp')
        assert sys_value == 130.0
        assert dia_value == 85.0
    
    def test_extract_glucose(self):
        """Test glucose extraction."""
        mapper = FieldMapper()
        
        text = "Fasting Glucose: 95 mg/dL"
        value, confidence = mapper.extract_value(text, 'fasting_glucose')
        assert value == 95.0
        
        # GDS format (Indonesian)
        text = "GDS: 102"
        value, _ = mapper.extract_value(text, 'fasting_glucose')
        assert value == 102.0
    
    def test_extract_hba1c(self):
        """Test HbA1c extraction."""
        mapper = FieldMapper()
        
        text = "HbA1c: 5.8 %"
        value, confidence = mapper.extract_value(text, 'hba1c')
        assert value == 5.8
        
        # Alternative formats
        text = "A1c 6.2"
        value, _ = mapper.extract_value(text, 'hba1c')
        assert value == 6.2
    
    def test_extract_cholesterol(self):
        """Test cholesterol extraction."""
        mapper = FieldMapper()
        
        text = "Total Cholesterol: 195 mg/dL"
        value, _ = mapper.extract_value(text, 'total_cholesterol')
        assert value == 195.0
        
        text = "LDL: 120 mg/dL"
        value, _ = mapper.extract_value(text, 'ldl')
        assert value == 120.0
        
        text = "HDL: 55 mg/dL"
        value, _ = mapper.extract_value(text, 'hdl')
        assert value == 55.0
    
    def test_extract_all_fields(self):
        """Test extracting all fields at once."""
        mapper = FieldMapper()
        
        sample_text = """
        Medical Check-Up Report
        Date: 15/04/2024
        
        Patient Name: John Doe
        Height: 175 cm
        Weight: 75 kg
        BMI: 24.5
        
        Blood Pressure: 120/80 mmHg
        Heart Rate: 72 bpm
        
        Fasting Glucose: 95 mg/dL
        HbA1c: 5.5 %
        
        Total Cholesterol: 195 mg/dL
        LDL: 120 mg/dL
        HDL: 55 mg/dL
        Triglycerides: 130 mg/dL
        
        SGOT: 28 U/L
        SGPT: 30 U/L
        Creatinine: 0.95 mg/dL
        Uric Acid: 5.8 mg/dL
        """
        
        results = mapper.extract_all(sample_text)
        
        assert 'height_cm' in results
        assert 'weight_kg' in results
        assert 'systolic_bp' in results
        assert 'diastolic_bp' in results
        assert 'fasting_glucose' in results
        assert 'hba1c' in results
        assert 'total_cholesterol' in results
        assert 'ldl' in results
        assert 'hdl' in results
        assert 'triglycerides' in results
        assert 'sgot' in results
        assert 'sgpt' in results
    
    def test_confidence_scoring(self):
        """Test that confidence is properly calculated."""
        mapper = FieldMapper()
        
        # Value in valid range should have higher confidence
        text_valid = "Weight: 75 kg"
        _, conf_valid = mapper.extract_value(text_valid, 'weight_kg')
        
        # Value outside valid range should have lower confidence
        text_invalid = "Weight: 750 kg"  # Unlikely value
        _, conf_invalid = mapper.extract_value(text_invalid, 'weight_kg')
        
        assert conf_valid > conf_invalid
    
    def test_invalid_field_returns_none(self):
        """Test that non-existent fields return None."""
        mapper = FieldMapper()
        
        text = "Some random text without health data"
        value, confidence = mapper.extract_value(text, 'height_cm')
        
        assert value is None
        assert confidence == 0.0


class TestExtractHealthMetrics:
    """Tests for the extract_health_metrics convenience function."""
    
    def test_extract_health_metrics_basic(self):
        """Test basic health metrics extraction."""
        text = "Height: 175 cm, Weight: 75 kg, Glucose: 95"
        results = extract_health_metrics(text)
        
        assert 'height_cm' in results
        assert 'weight_kg' in results
        assert 'fasting_glucose' in results
    
    def test_extract_health_metrics_empty_text(self):
        """Test extraction with empty text."""
        results = extract_health_metrics("")
        assert len(results) == 0
    
    def test_extract_health_metrics_partial(self):
        """Test extraction with partial data."""
        text = "Weight: 80 kg only"
        results = extract_health_metrics(text)
        
        assert 'weight_kg' in results
        assert 'height_cm' not in results


class TestOCRRoutes:
    """Tests for OCR routes (requires authentication)."""
    
    def test_ocr_page_requires_login(self, client):
        """Test that OCR page redirects to login."""
        response = client.get('/ocr/', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')
    
    def test_ocr_page_loads_when_authenticated(self, auth_client):
        """Test that OCR page loads for authenticated users."""
        response = auth_client.get('/ocr/')
        assert response.status_code == 200
    
    def test_ocr_bulk_page_loads(self, auth_client):
        """Test that bulk import page loads."""
        response = auth_client.get('/ocr/bulk')
        assert response.status_code == 200
    
    def test_ocr_status_endpoint(self, auth_client):
        """Test OCR status check endpoint."""
        response = auth_client.get('/ocr/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'ocr_available' in data


class TestOCRWorkflow:
    """Tests for the complete OCR workflow."""
    
    def test_invalid_file_type_rejected(self, auth_client):
        """Test that invalid file types are rejected."""
        import io
        
        # Upload a text file (should be rejected)
        data = {
            'file': (io.BytesIO(b'not an image'), 'test.txt')
        }
        response = auth_client.post('/ocr/upload', data=data, content_type='multipart/form-data', follow_redirects=False)
        
        # Should redirect back to upload page with error
        assert response.status_code == 302
    
    def test_upload_with_no_file(self, auth_client):
        """Test upload with no file selected."""
        response = auth_client.post('/ocr/upload', data={}, follow_redirects=True)
        assert response.status_code == 200
        assert b'No file selected' in response.data or b'error' in response.data.lower()


class TestErrorHandling:
    """Tests for OCR error handling."""
    
    def test_ocr_service_graceful_failure(self):
        """Test that OCR service handles failures gracefully."""
        from app.services.ocr_service import OCRService
        
        service = OCRService()
        
        # Test with non-existent file
        result = service.extract('/nonexistent/file.pdf')
        
        assert result.success == False
        assert result.error_message is not None
    
    def test_field_mapper_with_malformed_text(self):
        """Test field mapper with malformed text."""
        mapper = FieldMapper()
        
        # Malformed text should not crash
        text = "###...   --  ---  123abc xyz"
        results = mapper.extract_all(text)
        
        # Should return empty or partial results, not crash
        assert isinstance(results, dict)


class TestRecordCreation:
    """Tests for creating MCU records from OCR data."""
    
    def test_create_record_from_extracted_data(self, app, auth_client):
        """Test creating a record from extracted data."""
        with app.app_context():
            # Simulate extracted data
            extracted_data = {
                'height_cm': {'value': 175.0, 'confidence': 90},
                'weight_kg': {'value': 75.0, 'confidence': 85},
                'systolic_bp': {'value': 120.0, 'confidence': 80},
                'diastolic_bp': {'value': 80.0, 'confidence': 80},
            }
            
            # Create record
            record = MCURecord(
                patient_name='Test Patient',
                mcu_date=db.func.date('2024-04-15'),
                status='pending',
                user_id=1
            )
            db.session.add(record)
            db.session.flush()
            
            # Create metrics
            metrics = HealthMetrics(
                mcu_record_id=record.id,
                height_cm=extracted_data['height_cm']['value'],
                weight_kg=extracted_data['weight_kg']['value'],
                systolic_bp=int(extracted_data['systolic_bp']['value']),
                diastolic_bp=int(extracted_data['diastolic_bp']['value'])
            )
            db.session.add(metrics)
            db.session.commit()
            
            # Verify
            saved_record = MCURecord.query.first()
            assert saved_record is not None
            assert saved_record.health_metrics.height_cm == 175.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])