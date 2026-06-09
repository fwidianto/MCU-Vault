"""
Tests for health classification utilities (Phase 2B).
"""
import pytest
from app.utils.health_classification import (
    HealthClassifier,
    HealthLevel,
    ClassificationResult,
    classify_all_metrics,
    calculate_difference,
    format_metric_value,
    get_trend_indicator
)


class TestHealthClassifierBMI:
    """Tests for BMI classification."""
    
    def test_bmi_underweight(self):
        """BMI under 18.5 should be classified as Underweight."""
        result = HealthClassifier.classify_bmi(17.5)
        assert result.status == 'Underweight'
        assert result.level == HealthLevel.BORDERLINE
        assert result.badge_class == 'bg-warning'
    
    def test_bmi_normal(self):
        """BMI 18.5-24.9 should be classified as Normal."""
        result = HealthClassifier.classify_bmi(22.5)
        assert result.status == 'Normal'
        assert result.level == HealthLevel.NORMAL
        assert result.badge_class == 'bg-success'
    
    def test_bmi_overweight(self):
        """BMI 25.0-29.9 should be classified as Overweight."""
        result = HealthClassifier.classify_bmi(27.5)
        assert result.status == 'Overweight'
        assert result.level == HealthLevel.BORDERLINE
        assert result.badge_class == 'bg-warning'
    
    def test_bmi_obese(self):
        """BMI >= 30 should be classified as Obese."""
        result = HealthClassifier.classify_bmi(32.0)
        assert result.status == 'Obese'
        assert result.level == HealthLevel.HIGH_RISK
        assert result.badge_class == 'bg-danger'
    
    def test_bmi_boundary_normal(self):
        """Test BMI at normal range boundaries."""
        assert HealthClassifier.classify_bmi(18.5).status == 'Normal'
        assert HealthClassifier.classify_bmi(24.9).status == 'Normal'
    
    def test_bmi_boundary_overweight(self):
        """Test BMI at overweight range boundaries."""
        assert HealthClassifier.classify_bmi(25.0).status == 'Overweight'
        assert HealthClassifier.classify_bmi(29.9).status == 'Overweight'
    
    def test_bmi_none(self):
        """None BMI should return Unknown classification."""
        result = HealthClassifier.classify_bmi(None)
        assert result.status == 'Unknown'
        assert result.level == HealthLevel.UNKNOWN
        assert result.badge_class == 'bg-secondary'


class TestHealthClassifierBloodPressure:
    """Tests for blood pressure classification."""
    
    def test_bp_normal(self):
        """Normal BP: < 120 systolic and < 80 diastolic."""
        result = HealthClassifier.classify_blood_pressure(115, 75)
        assert result.status == 'Normal'
        assert result.level == HealthLevel.NORMAL
    
    def test_bp_elevated(self):
        """Elevated BP: 120-129 systolic and < 80 diastolic."""
        result = HealthClassifier.classify_blood_pressure(125, 75)
        assert result.status == 'Elevated'
        assert result.level == HealthLevel.BORDERLINE
    
    def test_bp_hypertension_stage_1(self):
        """Hypertension Stage 1: 130-139 systolic or 80-89 diastolic."""
        result = HealthClassifier.classify_blood_pressure(135, 78)
        assert result.status == 'Hypertension Stage 1'
        assert result.level == HealthLevel.BORDERLINE
    
    def test_bp_hypertension_stage_1_diastolic(self):
        """Hypertension Stage 1 based on diastolic."""
        result = HealthClassifier.classify_blood_pressure(125, 85)
        assert result.status == 'Hypertension Stage 1'
        assert result.level == HealthLevel.BORDERLINE
    
    def test_bp_hypertension_stage_2_systolic(self):
        """Hypertension Stage 2: >= 140 systolic."""
        result = HealthClassifier.classify_blood_pressure(145, 85)
        assert result.status == 'Hypertension Stage 2'
        assert result.level == HealthLevel.HIGH_RISK
    
    def test_bp_hypertension_stage_2_diastolic(self):
        """Hypertension Stage 2: >= 90 diastolic."""
        result = HealthClassifier.classify_blood_pressure(130, 92)
        assert result.status == 'Hypertension Stage 2'
        assert result.level == HealthLevel.HIGH_RISK
    
    def test_bp_none(self):
        """None values should return Unknown."""
        result = HealthClassifier.classify_blood_pressure(None, None)
        assert result.status == 'Unknown'
        assert result.level == HealthLevel.UNKNOWN
    
    def test_bp_partial_none(self):
        """Partial None values should return Unknown."""
        result = HealthClassifier.classify_blood_pressure(120, None)
        assert result.status == 'Unknown'


class TestHealthClassifierHbA1c:
    """Tests for HbA1c classification."""
    
    def test_hba1c_normal(self):
        """HbA1c < 5.7 should be Normal."""
        result = HealthClassifier.classify_hba1c(5.4)
        assert result.status == 'Normal'
        assert result.level == HealthLevel.NORMAL
    
    def test_hba1c_prediabetes(self):
        """HbA1c 5.7-6.4 should be Prediabetes."""
        result = HealthClassifier.classify_hba1c(6.0)
        assert result.status == 'Prediabetes'
        assert result.level == HealthLevel.BORDERLINE
    
    def test_hba1c_diabetes(self):
        """HbA1c >= 6.5 should be Diabetes."""
        result = HealthClassifier.classify_hba1c(7.0)
        assert result.status == 'Diabetes'
        assert result.level == HealthLevel.HIGH_RISK
    
    def test_hba1c_boundary_normal(self):
        """Test HbA1c at normal/prediabetes boundary."""
        assert HealthClassifier.classify_hba1c(5.6).status == 'Normal'
        assert HealthClassifier.classify_hba1c(5.7).status == 'Prediabetes'
    
    def test_hba1c_none(self):
        """None HbA1c should return Unknown."""
        result = HealthClassifier.classify_hba1c(None)
        assert result.status == 'Unknown'


class TestHealthClassifierLDL:
    """Tests for LDL cholesterol classification."""
    
    def test_ldl_optimal(self):
        """LDL < 100 should be Optimal."""
        result = HealthClassifier.classify_ldl(85)
        assert result.status == 'Optimal'
        assert result.level == HealthLevel.NORMAL
    
    def test_ldl_near_optimal(self):
        """LDL 100-129 should be Near Optimal."""
        result = HealthClassifier.classify_ldl(115)
        assert result.status == 'Near Optimal'
        assert result.level == HealthLevel.NORMAL
    
    def test_ldl_borderline_high(self):
        """LDL 130-159 should be Borderline High."""
        result = HealthClassifier.classify_ldl(145)
        assert result.status == 'Borderline High'
        assert result.level == HealthLevel.BORDERLINE
    
    def test_ldl_high(self):
        """LDL 160-189 should be High."""
        result = HealthClassifier.classify_ldl(170)
        assert result.status == 'High'
        assert result.level == HealthLevel.HIGH_RISK
    
    def test_ldl_very_high(self):
        """LDL >= 190 should be Very High."""
        result = HealthClassifier.classify_ldl(200)
        assert result.status == 'Very High'
        assert result.level == HealthLevel.HIGH_RISK
    
    def test_ldl_none(self):
        """None LDL should return Unknown."""
        result = HealthClassifier.classify_ldl(None)
        assert result.status == 'Unknown'


class TestHealthClassifierHDL:
    """Tests for HDL cholesterol classification."""
    
    def test_hdl_low(self):
        """HDL < 40 should be Low (Risk)."""
        result = HealthClassifier.classify_hdl(35)
        assert result.status == 'Low (Risk)'
        assert result.level == HealthLevel.HIGH_RISK
    
    def test_hdl_borderline(self):
        """HDL 40-59 should be Borderline."""
        result = HealthClassifier.classify_hdl(50)
        assert result.status == 'Borderline'
        assert result.level == HealthLevel.BORDERLINE
    
    def test_hdl_normal(self):
        """HDL >= 60 should be Normal (Good)."""
        result = HealthClassifier.classify_hdl(65)
        assert result.status == 'Normal (Good)'
        assert result.level == HealthLevel.NORMAL
    
    def test_hdl_none(self):
        """None HDL should return Unknown."""
        result = HealthClassifier.classify_hdl(None)
        assert result.status == 'Unknown'


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_calculate_difference_positive(self):
        """Test positive difference calculation."""
        diff, trend = calculate_difference(100, 110)
        assert diff == 10
        assert trend == 'unknown'  # unknown because we don't know which direction is better
    
    def test_calculate_difference_negative(self):
        """Test negative difference calculation."""
        diff, trend = calculate_difference(110, 100)
        assert diff == -10
    
    def test_calculate_difference_no_change(self):
        """Test no change difference."""
        diff, trend = calculate_difference(100, 100)
        assert diff == 0
        assert trend == 'no_change'
    
    def test_calculate_difference_none_first(self):
        """Test with None first value."""
        diff, trend = calculate_difference(None, 100)
        assert diff is None
        assert trend == 'unknown'
    
    def test_calculate_difference_none_second(self):
        """Test with None second value."""
        diff, trend = calculate_difference(100, None)
        assert diff is None
        assert trend == 'unknown'
    
    def test_format_metric_value_with_unit(self):
        """Test formatting metric value with unit."""
        assert format_metric_value(75.5, 'kg') == '75.5 kg'
        assert format_metric_value(22.5, '%') == '22.5 %'
    
    def test_format_metric_value_without_unit(self):
        """Test formatting metric value without unit."""
        assert format_metric_value(75.5, '') == '75.5'
    
    def test_format_metric_value_none(self):
        """Test formatting None value."""
        assert format_metric_value(None, 'kg') == 'N/A'
    
    def test_get_trend_indicator_improvement(self):
        """Test improvement trend (lower is better, value decreased)."""
        assert get_trend_indicator(-5.0, lower_is_better=True) == 'improvement'
    
    def test_get_trend_indicator_worsening(self):
        """Test worsening trend (lower is better, value increased)."""
        assert get_trend_indicator(5.0, lower_is_better=True) == 'worsening'
    
    def test_get_trend_indicator_no_change(self):
        """Test no change trend."""
        assert get_trend_indicator(0.0, lower_is_better=True) == 'no_change'
    
    def test_get_trend_indicator_none(self):
        """Test None value."""
        assert get_trend_indicator(None, lower_is_better=True) == 'unknown'
    
    def test_get_trend_indicator_higher_is_better(self):
        """Test trend when higher values are better (HDL case)."""
        assert get_trend_indicator(5.0, lower_is_better=False) == 'improvement'
        assert get_trend_indicator(-5.0, lower_is_better=False) == 'worsening'


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""
    
    def test_classification_result_to_dict(self):
        """Test ClassificationResult to_dict method."""
        result = ClassificationResult(
            category='BMI',
            status='Normal',
            level=HealthLevel.NORMAL,
            color_class='text-success',
            badge_class='bg-success'
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['category'] == 'BMI'
        assert result_dict['status'] == 'Normal'
        assert result_dict['level'] == 'normal'
        assert result_dict['color_class'] == 'text-success'
        assert result_dict['badge_class'] == 'bg-success'


class TestClassifyAllMetrics:
    """Tests for classify_all_metrics function."""
    
    def test_classify_all_metrics(self):
        """Test classifying all metrics from a metrics object."""
        # Create a mock metrics object
        class MockMetrics:
            bmi = 25.5
            systolic_bp = 135
            diastolic_bp = 85
            hba1c = 6.2
            ldl = 145
            hdl = 50
            total_cholesterol = 220
            triglycerides = 160
            fasting_glucose = 110
        
        classifications = classify_all_metrics(MockMetrics())
        
        assert 'bmi' in classifications
        assert 'blood_pressure' in classifications
        assert 'hba1c' in classifications
        assert 'ldl' in classifications
        assert 'hdl' in classifications
        
        assert classifications['bmi'].status == 'Overweight'
        assert classifications['blood_pressure'].status == 'Hypertension Stage 1'
        assert classifications['hba1c'].status == 'Prediabetes'
        assert classifications['ldl'].status == 'Borderline High'