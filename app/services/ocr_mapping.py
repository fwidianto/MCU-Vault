"""
OCR Field Mapping Engine for MCU Vault.

Maps extracted OCR text to standardized MCU Vault field names.
Handles common variations and synonyms for health metrics.
"""

import re
from typing import Dict, List, Tuple, Optional


class FieldMapper:
    """
    Maps OCR-extracted text to standardized MCU Vault field names.
    Also extracts confidence scores based on pattern matching.
    """
    
    # Field name patterns and their variations
    FIELD_PATTERNS = {
        # Basic Measurements
        'height_cm': [
            r'height[:\s]*(\d+\.?\d*)\s*(?:cm|centimeter)',
            r'tb[:\s]*(\d+\.?\d*)',
            r'height[:\s]*(\d+\.?\d*)',
            r'tall[:\s]*(\d+\.?\d*)',
        ],
        'weight_kg': [
            r'weight[:\s]*(\d+\.?\d*)\s*(?:kg|kilogram)',
            r'bb[:\s]*(\d+\.?\d*)',
            r'weight[:\s]*(\d+\.?\d*)',
            r'body\s*weight[:\s]*(\d+\.?\d*)',
        ],
        'bmi': [
            r'bmi[:\s]*(\d+\.?\d*)',
            r'body\s*mass\s*index[:\s]*(\d+\.?\d*)',
            r'\bmass\s*index[:\s]*(\d+\.?\d*)',
        ],
        
        # Vital Signs
        'systolic_bp': [
            r'systolic[:\s]*(?:bp|blood\s*pressure)?[:\s]*(\d+)',
            r'sys[:\s]*(\d+)',
            r'sbp[:\s]*(\d+)',
            r'blood\s*pressure[:\s]*(\d+)[\/\s]*(?:\d+)',
            r'td\s*(?:systolic)?[:\s]*(\d+)',
        ],
        'diastolic_bp': [
            r'diastolic[:\s]*(?:bp|blood\s*pressure)?[:\s]*(\d+)',
            r'dia[:\s]*(\d+)',
            r'dbp[:\s]*(\d+)',
            r'blood\s*pressure[:\s]*(?:\d+)[\/\s]*(\d+)',
        ],
        'heart_rate': [
            r'heart\s*rate[:\s]*(\d+)',
            r'hr[:\s]*(\d+)',
            r'pulse[:\s]*(\d+)',
            r'nadi[:\s]*(\d+)',
            r'denyut[:\s]*(\d+)',
        ],
        
        # Blood Sugar
        'fasting_glucose': [
            r'glucose[:\s]*(?:fasting|puasa)?[:\s]*(\d+\.?\d*)',
            r'gds[:\s]*(\d+\.?\d*)',
            r'glucose\s*puasa[:\s]*(\d+\.?\d*)',
            r'glucose\s*fasting[:\s]*(\d+\.?\d*)',
            r'sugar[:\s]*(\d+\.?\d*)',
        ],
        'hba1c': [
            r'hba1c[:\s]*(\d+\.?\d*)',
            r'hb[\s]*a1c[:\s]*(\d+\.?\d*)',
            r'a1c[:\s]*(\d+\.?\d*)',
            r'hemoglobin\s*a1c[:\s]*(\d+\.?\d*)',
            r'hba1[:\s]*(\d+\.?\d*)',
        ],
        
        # Lipid Profile
        'total_cholesterol': [
            r'total\s*cholesterol[:\s]*(\d+\.?\d*)',
            r'cholesterol[:\s]*(\d+\.?\d*)',
            r'kolesterol[:\s]*(\d+\.?\d*)',
            r'tc[:\s]*(\d+\.?\d*)',
            r'chol[:\s]*(\d+\.?\d*)',
        ],
        'ldl': [
            r'ldl[:\s]*(?:cholesterol)?[:\s]*(\d+\.?\d*)',
            r'ldl[\s-]*c[:\s]*(\d+\.?\d*)',
            r'low\s*density\s*lipoprotein[:\s]*(\d+\.?\d*)',
        ],
        'hdl': [
            r'hdl[:\s]*(?:cholesterol)?[:\s]*(\d+\.?\d*)',
            r'hdl[\s-]*c[:\s]*(\d+\.?\d*)',
            r'high\s*density\s*lipoprotein[:\s]*(\d+\.?\d*)',
        ],
        'triglycerides': [
            r'triglycerides?\s*[:\s]*(\d+\.?\d*)',
            r'trig[:\s]*(\d+\.?\d*)',
            r'tg[:\s]*(\d+\.?\d*)',
        ],
        
        # Liver Function
        'sgot': [
            r'sgot[:\s]*(\d+\.?\d*)',
            r'sgot/ast[:\s]*(\d+\.?\d*)',
            r'ast[:\s]*(\d+\.?\d*)',
            r'got[:\s]*(\d+\.?\d*)',
        ],
        'sgpt': [
            r'sgpt[:\s]*(\d+\.?\d*)',
            r'sgpt/alt[:\s]*(\d+\.?\d*)',
            r'alt[:\s]*(\d+\.?\d*)',
            r'gpt[:\s]*(\d+\.?\d*)',
        ],
        
        # Kidney Function
        'creatinine': [
            r'creatinine[:\s]*(\d+\.?\d*)',
            r'creat[:\s]*(\d+\.?\d*)',
            r'sc[:\s]*(\d+\.?\d*)',
        ],
        'uric_acid': [
            r'uric\s*acid[:\s]*(\d+\.?\d*)',
            r'asam\s*urat[:\s]*(\d+\.?\d*)',
            r'ua[:\s]*(\d+\.?\d*)',
            r'uric[:\s]*(\d+\.?\d*)',
        ],
        
        # Meta fields
        'patient_name': [
            r'name[:\s]*([A-Za-z\s]+)',
            r'patient[:\s]*([A-Za-z\s]+)',
            r'nama[:\s]*([A-Za-z\s]+)',
        ],
        'mcu_date': [
            r'date[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'mcu\s*date[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'tanggal[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ],
        'company': [
            r'company[:\s]*([A-Za-z\s]+)',
            r'institution[:\s]*([A-Za-z\s]+)',
            r'perusahaan[:\s]*([A-Za-z\s]+)',
        ],
    }
    
    # Valid ranges for validation (to improve confidence)
    VALID_RANGES = {
        'height_cm': (50, 250),
        'weight_kg': (20, 300),
        'bmi': (10, 60),
        'systolic_bp': (60, 250),
        'diastolic_bp': (40, 150),
        'heart_rate': (30, 200),
        'fasting_glucose': (50, 400),
        'hba1c': (4, 15),
        'total_cholesterol': (50, 400),
        'ldl': (20, 300),
        'hdl': (20, 120),
        'triglycerides': (30, 1000),
        'sgot': (5, 200),
        'sgpt': (5, 200),
        'creatinine': (0.1, 20),
        'uric_acid': (2, 15),
    }
    
    def __init__(self):
        """Initialize the field mapper with compiled regex patterns."""
        self.compiled_patterns = {}
        for field, patterns in self.FIELD_PATTERNS.items():
            self.compiled_patterns[field] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
            ]
    
    def extract_value(self, text: str, field: str) -> Tuple[Optional[float], float]:
        """
        Extract a value for a specific field from OCR text.
        
        Args:
            text: OCR extracted text
            field: Field name to extract
            
        Returns:
            Tuple of (extracted_value, confidence_score)
        """
        if field not in self.compiled_patterns:
            return None, 0.0
        
        patterns = self.compiled_patterns[field]
        
        for i, pattern in enumerate(patterns):
            match = pattern.search(text)
            if match:
                value_str = match.group(1) if match.lastindex else match.group(0)
                try:
                    # Try to extract numeric value
                    value = float(re.search(r'\d+\.?\d*', value_str).group())
                    
                    # Calculate confidence based on pattern specificity
                    # Earlier patterns in list are more specific = higher confidence
                    base_confidence = 90 - (i * 10)  # 90, 80, 70, ...
                    
                    # Boost confidence if value is in valid range
                    if field in self.VALID_RANGES:
                        min_val, max_val = self.VALID_RANGES[field]
                        if min_val <= value <= max_val:
                            base_confidence = min(98, base_confidence + 5)
                        else:
                            base_confidence = max(50, base_confidence - 15)
                    
                    return value, base_confidence
                except (ValueError, AttributeError):
                    continue
        
        return None, 0.0
    
    def extract_all(self, text: str) -> Dict:
        """
        Extract all known fields from OCR text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with field names as keys and (value, confidence) tuples as values
        """
        results = {}
        
        for field in self.FIELD_PATTERNS.keys():
            value, confidence = self.extract_value(text, field)
            if value is not None:
                results[field] = {
                    'value': value,
                    'confidence': confidence
                }
        
        return results
    
    def get_numeric_fields(self) -> List[str]:
        """Return list of numeric health metric fields."""
        return [
            'height_cm', 'weight_kg', 'bmi',
            'systolic_bp', 'diastolic_bp', 'heart_rate',
            'fasting_glucose', 'hba1c',
            'total_cholesterol', 'ldl', 'hdl', 'triglycerides',
            'sgot', 'sgpt', 'creatinine', 'uric_acid'
        ]
    
    def normalize_field_name(self, raw_name: str) -> Optional[str]:
        """
        Normalize a raw field name to standard MCU Vault field.
        
        Args:
            raw_name: Raw field name from OCR
            
        Returns:
            Normalized field name or None if not recognized
        """
        raw_lower = raw_name.lower().strip()
        
        for field, patterns in self.FIELD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, raw_lower):
                    return field
        
        return None


# Global mapper instance
mapper = FieldMapper()


def extract_health_metrics(text: str) -> Dict:
    """
    Convenience function to extract all health metrics from OCR text.
    
    Args:
        text: OCR extracted text
        
    Returns:
        Dictionary with field names and (value, confidence) tuples
    """
    return mapper.extract_all(text)