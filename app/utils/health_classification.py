"""
Health classification utilities for Phase 2B.
Rule-based health status classifications without AI.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum


class HealthLevel(Enum):
    """Health risk levels for classification badges."""
    NORMAL = "normal"
    BORDERLINE = "borderline"
    HIGH_RISK = "high_risk"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of health metric classification."""
    category: str
    status: str
    level: HealthLevel
    color_class: str
    badge_class: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'category': self.category,
            'status': self.status,
            'level': self.level.value,
            'color_class': self.color_class,
            'badge_class': self.badge_class
        }


class HealthClassifier:
    """
    Rule-based health classifier for various health metrics.
    No AI or machine learning - purely rule-based thresholds.
    """
    
    # BMI Classification Thresholds
    BMI_UNDERWEIGHT = 18.5
    BMI_NORMAL_MAX = 24.9
    BMI_OVERWEIGHT_MAX = 29.9
    
    # Blood Pressure Thresholds
    BP_NORMAL_SYS = 120
    BP_ELEVATED_SYS = 129
    BP_HYPERTENSION_1_SYS = 130  # Start of Stage 1 range
    BP_HYPERTENSION_2_SYS = 140
    
    BP_NORMAL_DIA = 80
    BP_ELEVATED_DIA = 89
    BP_HYPERTENSION_1_DIA = 80  # Start of Stage 1 range (80-89)
    BP_HYPERTENSION_2_DIA = 90
    
    # HbA1c Classification Thresholds
    HBA1C_PREDIABETES = 5.7
    HBA1C_DIABETES = 6.5
    
    # LDL Classification Thresholds
    LDL_OPTIMAL = 100
    LDL_NEAR_OPTIMAL = 130
    LDL_BORDERLINE_HIGH = 160
    LDL_HIGH = 190
    
    # HDL Classification Thresholds (mg/dL)
    HDL_LOW_MALE = 40
    HDL_LOW_FEMALE = 50
    
    # Total Cholesterol
    TC_DESIRABLE = 200
    TC_BORDERLINE = 240
    
    # Triglycerides (mg/dL)
    TG_NORMAL = 150
    TG_BORDERLINE = 200
    TG_HIGH = 500
    
    # Fasting Glucose (mg/dL)
    GLUCOSE_NORMAL = 100
    GLUCOSE_PREDIABETES = 126
    
    @staticmethod
    def classify_bmi(bmi: Optional[float]) -> ClassificationResult:
        """Classify BMI value."""
        if bmi is None:
            return ClassificationResult(
                category='BMI',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        if bmi < HealthClassifier.BMI_UNDERWEIGHT:
            return ClassificationResult(
                category='BMI',
                status='Underweight',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        elif bmi <= HealthClassifier.BMI_NORMAL_MAX:
            return ClassificationResult(
                category='BMI',
                status='Normal',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
        elif bmi <= HealthClassifier.BMI_OVERWEIGHT_MAX:
            return ClassificationResult(
                category='BMI',
                status='Overweight',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        else:
            return ClassificationResult(
                category='BMI',
                status='Obese',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
    
    @staticmethod
    def classify_blood_pressure(
        systolic: Optional[int], 
        diastolic: Optional[int]
    ) -> ClassificationResult:
        """Classify blood pressure."""
        if systolic is None or diastolic is None:
            return ClassificationResult(
                category='Blood Pressure',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        # Hypertension Stage 2 (highest priority) - >= 140 systolic OR >= 90 diastolic
        if systolic >= HealthClassifier.BP_HYPERTENSION_2_SYS or \
           diastolic >= HealthClassifier.BP_HYPERTENSION_2_DIA:
            return ClassificationResult(
                category='Blood Pressure',
                status='Hypertension Stage 2',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
        
        # Hypertension Stage 1 - (130-139 systolic OR 80-89 diastolic) but not Stage 2
        if (systolic >= HealthClassifier.BP_HYPERTENSION_1_SYS and systolic < HealthClassifier.BP_HYPERTENSION_2_SYS) or \
           (diastolic >= HealthClassifier.BP_NORMAL_DIA and diastolic < HealthClassifier.BP_HYPERTENSION_2_DIA):
            return ClassificationResult(
                category='Blood Pressure',
                status='Hypertension Stage 1',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        
        # Elevated - 120-129 systolic and < 80 diastolic
        if systolic >= HealthClassifier.BP_NORMAL_SYS and systolic < HealthClassifier.BP_HYPERTENSION_1_SYS and \
           diastolic < HealthClassifier.BP_NORMAL_DIA:
            return ClassificationResult(
                category='Blood Pressure',
                status='Elevated',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        
        # Normal
        return ClassificationResult(
            category='Blood Pressure',
            status='Normal',
            level=HealthLevel.NORMAL,
            color_class='text-success',
            badge_class='bg-success'
        )
    
    @staticmethod
    def classify_hba1c(hba1c: Optional[float]) -> ClassificationResult:
        """Classify HbA1c value."""
        if hba1c is None:
            return ClassificationResult(
                category='HbA1c',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        if hba1c < HealthClassifier.HBA1C_PREDIABETES:
            return ClassificationResult(
                category='HbA1c',
                status='Normal',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
        elif hba1c < HealthClassifier.HBA1C_DIABETES:
            return ClassificationResult(
                category='HbA1c',
                status='Prediabetes',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        else:
            return ClassificationResult(
                category='HbA1c',
                status='Diabetes',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
    
    @staticmethod
    def classify_ldl(ldl: Optional[float]) -> ClassificationResult:
        """Classify LDL cholesterol value."""
        if ldl is None:
            return ClassificationResult(
                category='LDL',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        if ldl < HealthClassifier.LDL_OPTIMAL:
            return ClassificationResult(
                category='LDL',
                status='Optimal',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
        elif ldl < HealthClassifier.LDL_NEAR_OPTIMAL:
            return ClassificationResult(
                category='LDL',
                status='Near Optimal',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
        elif ldl < HealthClassifier.LDL_BORDERLINE_HIGH:
            return ClassificationResult(
                category='LDL',
                status='Borderline High',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        elif ldl < HealthClassifier.LDL_HIGH:
            return ClassificationResult(
                category='LDL',
                status='High',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
        else:
            return ClassificationResult(
                category='LDL',
                status='Very High',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
    
    @staticmethod
    def classify_hdl(hdl: Optional[float]) -> ClassificationResult:
        """Classify HDL cholesterol value."""
        if hdl is None:
            return ClassificationResult(
                category='HDL',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        if hdl < HealthClassifier.HDL_LOW_MALE:
            return ClassificationResult(
                category='HDL',
                status='Low (Risk)',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
        elif hdl < 60:
            return ClassificationResult(
                category='HDL',
                status='Borderline',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        else:
            return ClassificationResult(
                category='HDL',
                status='Normal (Good)',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
    
    @staticmethod
    def classify_total_cholesterol(tc: Optional[float]) -> ClassificationResult:
        """Classify total cholesterol value."""
        if tc is None:
            return ClassificationResult(
                category='Total Cholesterol',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        if tc < HealthClassifier.TC_DESIRABLE:
            return ClassificationResult(
                category='Total Cholesterol',
                status='Desirable',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
        elif tc < HealthClassifier.TC_BORDERLINE:
            return ClassificationResult(
                category='Total Cholesterol',
                status='Borderline High',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        else:
            return ClassificationResult(
                category='Total Cholesterol',
                status='High',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
    
    @staticmethod
    def classify_triglycerides(tg: Optional[float]) -> ClassificationResult:
        """Classify triglycerides value."""
        if tg is None:
            return ClassificationResult(
                category='Triglycerides',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        if tg < HealthClassifier.TG_NORMAL:
            return ClassificationResult(
                category='Triglycerides',
                status='Normal',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
        elif tg < HealthClassifier.TG_BORDERLINE:
            return ClassificationResult(
                category='Triglycerides',
                status='Borderline High',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        elif tg < HealthClassifier.TG_HIGH:
            return ClassificationResult(
                category='Triglycerides',
                status='High',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
        else:
            return ClassificationResult(
                category='Triglycerides',
                status='Very High',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )
    
    @staticmethod
    def classify_fasting_glucose(glucose: Optional[float]) -> ClassificationResult:
        """Classify fasting glucose value."""
        if glucose is None:
            return ClassificationResult(
                category='Fasting Glucose',
                status='Unknown',
                level=HealthLevel.UNKNOWN,
                color_class='text-muted',
                badge_class='bg-secondary'
            )
        
        if glucose < HealthClassifier.GLUCOSE_NORMAL:
            return ClassificationResult(
                category='Fasting Glucose',
                status='Normal',
                level=HealthLevel.NORMAL,
                color_class='text-success',
                badge_class='bg-success'
            )
        elif glucose < HealthClassifier.GLUCOSE_PREDIABETES:
            return ClassificationResult(
                category='Fasting Glucose',
                status='Prediabetes',
                level=HealthLevel.BORDERLINE,
                color_class='text-warning',
                badge_class='bg-warning'
            )
        else:
            return ClassificationResult(
                category='Fasting Glucose',
                status='Diabetes Range',
                level=HealthLevel.HIGH_RISK,
                color_class='text-danger',
                badge_class='bg-danger'
            )


def classify_all_metrics(metrics) -> Dict[str, ClassificationResult]:
    """
    Classify all health metrics from a HealthMetrics object.
    
    Args:
        metrics: HealthMetrics model instance
        
    Returns:
        Dictionary of metric name to ClassificationResult
    """
    return {
        'bmi': HealthClassifier.classify_bmi(metrics.bmi),
        'blood_pressure': HealthClassifier.classify_blood_pressure(
            metrics.systolic_bp, metrics.diastolic_bp
        ),
        'hba1c': HealthClassifier.classify_hba1c(metrics.hba1c),
        'ldl': HealthClassifier.classify_ldl(metrics.ldl),
        'hdl': HealthClassifier.classify_hdl(metrics.hdl),
        'total_cholesterol': HealthClassifier.classify_total_cholesterol(metrics.total_cholesterol),
        'triglycerides': HealthClassifier.classify_triglycerides(metrics.triglycerides),
        'fasting_glucose': HealthClassifier.classify_fasting_glucose(metrics.fasting_glucose),
    }


def calculate_difference(value1: Optional[float], value2: Optional[float]) -> Tuple[Optional[float], str]:
    """
    Calculate the difference between two values and determine trend.
    
    Args:
        value1: First value
        value2: Second value
        
    Returns:
        Tuple of (difference, trend)
        trend can be: 'improvement', 'worsening', 'no_change', 'unknown'
    """
    if value1 is None or value2 is None:
        return None, 'unknown'
    
    diff = round(value2 - value1, 2)
    
    if abs(diff) < 0.01:  # Essentially equal
        return diff, 'no_change'
    
    return diff, 'unknown'  # Trend depends on metric type


def format_metric_value(value: Optional[float], unit: str = '') -> str:
    """Format a metric value for display."""
    if value is None:
        return 'N/A'
    if unit:
        return f"{value} {unit}"
    return str(value)


def get_trend_indicator(difference: Optional[float], lower_is_better: bool = False) -> str:
    """
    Get trend indicator based on difference and metric type.
    
    Args:
        difference: The calculated difference (new - old)
        lower_is_better: Whether lower values indicate improvement
        
    Returns:
        'improvement', 'worsening', 'no_change', or 'unknown'
    """
    if difference is None:
        return 'unknown'
    
    if abs(difference) < 0.01:
        return 'no_change'
    
    if lower_is_better:
        return 'improvement' if difference < 0 else 'worsening'
    else:
        # For most health metrics, lower is better
        # Exceptions would be HDL (where higher is better)
        return 'worsening' if difference < 0 else 'improvement'