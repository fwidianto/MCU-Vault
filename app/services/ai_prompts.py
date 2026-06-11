"""
AI Prompt Templates for Phase 3A - Health Intelligence.
Safe, educational prompts that explain health metrics without diagnosing.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


# Medical disclaimer
MEDICAL_DISCLAIMER = """
⚠️ MEDICAL DISCLAIMER: This information is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider regarding any medical concerns.
"""


# System prompt for all health AI interactions
HEALTH_AI_SYSTEM_PROMPT = f"""You are a health education assistant helping users understand their medical check-up (MCU) results.

IMPORTANT GUIDELINES:
1. You may EXPLAIN health metrics and their significance
2. You may SUMMARIZE patterns and trends in health data
3. You may EDUCATE about what different values mean
4. You may ENCOURAGE users to consult healthcare professionals

IMPORTANT RESTRICTIONS:
1. NEVER diagnose diseases or conditions
2. NEVER prescribe medication or treatment plans
3. NEVER claim certainty about health outcomes
4. NEVER provide specific medical advice for individuals

Your role is to help users understand their health data in context, not to replace medical professionals.

Always include appropriate disclaimers when discussing health information.
"""


def format_health_metrics_for_ai(metrics: Dict[str, Any]) -> str:
    """Format health metrics dictionary for AI consumption."""
    if not metrics:
        return "No health metrics available."
    
    lines = []
    
    # Basic measurements
    if metrics.get('height_cm') or metrics.get('weight_kg') or metrics.get('bmi'):
        lines.append("📊 BASIC MEASUREMENTS:")
        if metrics.get('height_cm'):
            lines.append(f"  • Height: {metrics['height_cm']} cm")
        if metrics.get('weight_kg'):
            lines.append(f"  • Weight: {metrics['weight_kg']} kg")
        if metrics.get('bmi'):
            lines.append(f"  • BMI: {metrics['bmi']}")
    
    # Vital signs
    if metrics.get('systolic_bp') or metrics.get('diastolic_bp') or metrics.get('heart_rate'):
        lines.append("\n❤️ VITAL SIGNS:")
        if metrics.get('systolic_bp') and metrics.get('diastolic_bp'):
            lines.append(f"  • Blood Pressure: {metrics['systolic_bp']}/{metrics['diastolic_bp']} mmHg")
        if metrics.get('heart_rate'):
            lines.append(f"  • Heart Rate: {metrics['heart_rate']} bpm")
    
    # Blood sugar
    if metrics.get('fasting_glucose') or metrics.get('hba1c'):
        lines.append("\n🩸 BLOOD SUGAR:")
        if metrics.get('fasting_glucose'):
            lines.append(f"  • Fasting Glucose: {metrics['fasting_glucose']} mg/dL")
        if metrics.get('hba1c'):
            lines.append(f"  • HbA1c: {metrics['hba1c']}%")
    
    # Lipid profile
    if any(metrics.get(k) for k in ['total_cholesterol', 'ldl', 'hdl', 'triglycerides']):
        lines.append("\n🧪 LIPID PROFILE:")
        if metrics.get('total_cholesterol'):
            lines.append(f"  • Total Cholesterol: {metrics['total_cholesterol']} mg/dL")
        if metrics.get('ldl'):
            lines.append(f"  • LDL (Bad Cholesterol): {metrics['ldl']} mg/dL")
        if metrics.get('hdl'):
            lines.append(f"  • HDL (Good Cholesterol): {metrics['hdl']} mg/dL")
        if metrics.get('triglycerides'):
            lines.append(f"  • Triglycerides: {metrics['triglycerides']} mg/dL")
    
    # Liver function
    if metrics.get('sgot') or metrics.get('sgpt'):
        lines.append("\n🔬 LIVER FUNCTION:")
        if metrics.get('sgot'):
            lines.append(f"  • SGOT: {metrics['sgot']} U/L")
        if metrics.get('sgpt'):
            lines.append(f"  • SGPT: {metrics['sgpt']} U/L")
    
    # Kidney function
    if metrics.get('creatinine') or metrics.get('uric_acid'):
        lines.append("\n🫘 KIDNEY FUNCTION:")
        if metrics.get('creatinine'):
            lines.append(f"  • Creatinine: {metrics['creatinine']} mg/dL")
        if metrics.get('uric_acid'):
            lines.append(f"  • Uric Acid: {metrics['uric_acid']} mg/dL")
    
    return "\n".join(lines) if lines else "No health metrics available."


def format_comparison_for_ai(
    current: Dict[str, Any], 
    previous: Dict[str, Any],
    current_date: str,
    previous_date: str
) -> str:
    """Format two health metric sets for comparison."""
    lines = [
        f"CURRENT MCU ({current_date}):",
        format_health_metrics_for_ai(current),
        f"\nPREVIOUS MCU ({previous_date}):",
        format_health_metrics_for_ai(previous)
    ]
    return "\n".join(lines)


def format_trend_data_for_ai(records: List[Dict[str, Any]]) -> str:
    """Format multiple MCU records for trend analysis."""
    if not records:
        return "No historical data available."
    
    lines = ["HISTORICAL MCU DATA:"]
    
    for i, record in enumerate(records):
        date = record.get('date', f'Record {i+1}')
        lines.append(f"\n📅 MCU #{i+1} - {date}:")
        
        metrics = record.get('metrics', {})
        if metrics:
            lines.append(format_health_metrics_for_ai(metrics))
        else:
            lines.append("  (No detailed metrics)")
    
    return "\n".join(lines)


# PROMPT TEMPLATES

def health_summary_prompt(patient_name: str, metrics: Dict[str, Any], record_date: str) -> tuple:
    """
    Generate a prompt for creating a health summary.
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = HEALTH_AI_SYSTEM_PROMPT
    
    metrics_text = format_health_metrics_for_ai(metrics)
    
    user_prompt = f"""Please provide an educational health summary for a patient based on their recent medical check-up results.

PATIENT: {patient_name}
MCU DATE: {record_date}

{metrics_text}

Please provide a summary that:
1. Describes the overall health picture based on the metrics
2. Highlights any metrics that may need attention
3. Explains what the values might indicate in general terms
4. Encourages consultation with healthcare professionals

Format the response in clear sections. Keep it informative but not alarming.
"""
    
    return system_prompt, user_prompt


def comparison_prompt(
    patient_name: str,
    current: Dict[str, Any],
    previous: Dict[str, Any],
    current_date: str,
    previous_date: str
) -> tuple:
    """
    Generate a prompt for comparing two MCU records.
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = HEALTH_AI_SYSTEM_PROMPT
    
    comparison_text = format_comparison_for_ai(current, previous, current_date, previous_date)
    
    user_prompt = f"""Please provide an educational comparison between two medical check-ups for a patient.

PATIENT: {patient_name}

{comparison_text}

Please provide a comparison that:
1. Identifies metrics that have changed between the two check-ups
2. Notes whether changes are increases, decreases, or stable
3. Explains what these changes might mean in general terms
4. Emphasizes the importance of discussing changes with a healthcare provider

Focus on the most significant changes. Keep the response informative and educational.
"""
    
    return system_prompt, user_prompt


def trend_analysis_prompt(
    patient_name: str,
    records: List[Dict[str, Any]],
    start_year: int,
    end_year: int
) -> tuple:
    """
    Generate a prompt for analyzing health trends over time.
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = HEALTH_AI_SYSTEM_PROMPT
    
    trend_text = format_trend_data_for_ai(records)
    
    user_prompt = f"""Please provide an educational analysis of health trends for a patient over several years.

PATIENT: {patient_name}
ANALYSIS PERIOD: {start_year} to {end_year}

{trend_text}

Please provide a trend analysis that:
1. Identifies overall patterns and directions (increasing, decreasing, stable)
2. Notes any notable changes or turning points
3. Explains what these trends might suggest in general terms
4. Encourages discussion with healthcare providers about long-term health management

Focus on patterns that span the full time period. Be educational, not diagnostic.
"""
    
    return system_prompt, user_prompt


def timeline_narrative_prompt(
    patient_name: str,
    records: List[Dict[str, Any]],
    summary_by_period: Dict[str, str]
) -> tuple:
    """
    Generate a prompt for creating a health timeline narrative.
    
    Args:
        summary_by_period: Dict mapping period names to brief summaries
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = HEALTH_AI_SYSTEM_PROMPT
    
    # Format period summaries
    period_lines = ["HEALTH SUMMARY BY PERIOD:"]
    for period, summary in summary_by_period.items():
        period_lines.append(f"\n{period}: {summary}")
    
    # Format all records
    records_text = format_trend_data_for_ai(records)
    
    user_prompt = f"""Please create an educational health timeline narrative for a patient based on their medical check-up history.

PATIENT: {patient_name}

{chr(10).join(period_lines)}

DETAILED RECORDS:
{records_text}

Please create a narrative that:
1. Describes the patient's health journey over time
2. Identifies periods of stability vs. change
3. Notes any gradual improvements or concerns
4. Emphasizes that this is educational observation, not medical advice

Write in a storytelling style that helps the patient understand their health history.
"""
    
    return system_prompt, user_prompt


# METRIC EXPLANATIONS - Educational content for "Explain" feature

METRIC_EXPLANATIONS = {
    "bmi": {
        "name": "Body Mass Index (BMI)",
        "description": "A measure of body fat based on height and weight.",
        "what_it_means": "BMI is a screening tool that categorizes weight relative to height. It does not directly measure body fat but correlates with direct fat measures for most people.",
        "ranges": {
            "underweight": "Below 18.5 - May indicate undernutrition or other health issues",
            "normal": "18.5-24.9 - Generally associated with good health for most adults",
            "overweight": "25-29.9 - May increase risk for weight-related health conditions",
            "obese": "30 and above - Associated with higher risk for various health conditions"
        },
        "limitations": "BMI does not distinguish between muscle and fat, so athletes may have high BMI without excess fat. It also doesn't account for fat distribution."
    },
    
    "blood_pressure": {
        "name": "Blood Pressure",
        "description": "The force of blood pushing against artery walls.",
        "what_it_means": "Blood pressure is recorded as two numbers: systolic (top number) measures pressure when heart beats, diastolic (bottom number) measures pressure between beats.",
        "ranges": {
            "normal": "Less than 120/80 mmHg",
            "elevated": "120-129 / less than 80 mmHg",
            "hypertension_stage_1": "130-139 / 80-89 mmHg",
            "hypertension_stage_2": "140+ / 90+ mmHg"
        },
        "importance": "High blood pressure (hypertension) strains the heart and arteries, increasing risk for heart disease and stroke. It's often called the 'silent killer' because it usually has no symptoms."
    },
    
    "hba1c": {
        "name": "Hemoglobin A1c (HbA1c)",
        "description": "A test that measures average blood sugar over the past 2-3 months.",
        "what_it_means": "HbA1c shows how well blood sugar has been controlled over time. Unlike finger-stick tests that show sugar at one moment, A1c reflects long-term control.",
        "ranges": {
            "normal": "Below 5.7%",
            "prediabetes": "5.7-6.4% - Indicates higher risk for developing diabetes",
            "diabetes": "6.5% or above - Used to diagnose diabetes"
        },
        "importance": "Keeping HbA1c in target range reduces risk of diabetes complications affecting eyes, kidneys, nerves, and blood vessels."
    },
    
    "ldl": {
        "name": "LDL Cholesterol (Low-Density Lipoprotein)",
        "description": "Often called 'bad' cholesterol because high levels can build up in artery walls.",
        "what_it_means": "LDL carries cholesterol through the blood and can deposit it in artery walls, forming plaques that narrow arteries.",
        "ranges": {
            "optimal": "Below 100 mg/dL - Lower is generally better",
            "near_optimal": "100-129 mg/dL",
            "borderline_high": "130-159 mg/dL",
            "high": "160-189 mg/dL",
            "very_high": "190+ mg/dL"
        },
        "importance": "High LDL contributes to atherosclerosis (hardening/narrowing of arteries), increasing risk for heart attack and stroke."
    },
    
    "hdl": {
        "name": "HDL Cholesterol (High-Density Lipoprotein)",
        "description": "Often called 'good' cholesterol because it helps remove other forms of cholesterol from the blood.",
        "what_it_means": "HDL carries cholesterol away from arteries and back to the liver for processing and removal.",
        "ranges": {
            "low": "Below 40 mg/dL (men) / Below 50 mg/dL (women) - Higher risk",
            "normal": "40-59 mg/dL (men) / 50-59 mg/dL (women)",
            "high": "60+ mg/dL - Generally protective against heart disease"
        },
        "importance": "Higher HDL levels are associated with lower risk of heart disease. Regular exercise and moderate alcohol consumption may help raise HDL."
    },
    
    "triglycerides": {
        "name": "Triglycerides",
        "description": "The most common type of fat in the body, stored in fat cells for energy.",
        "what_it_means": "Triglyceride levels rise after eating - they're used for energy between meals. High fasting levels may indicate how much fat is stored in the body.",
        "ranges": {
            "normal": "Below 150 mg/dL",
            "borderline_high": "150-199 mg/dL",
            "high": "200-499 mg/dL",
            "very_high": "500+ mg/dL"
        },
        "importance": "High triglycerides often accompany obesity, sedentary lifestyle, smoking, and excessive alcohol. Very high levels can cause inflammation of the pancreas."
    },
    
    "fasting_glucose": {
        "name": "Fasting Blood Glucose",
        "description": "Blood sugar level measured after not eating for at least 8 hours.",
        "what_it_means": "This test shows how well the body maintains blood sugar levels in a fasting state.",
        "ranges": {
            "normal": "Below 100 mg/dL",
            "prediabetes": "100-125 mg/dL",
            "diabetes": "126 mg/dL or higher (on two separate tests)"
        },
        "importance": "Elevated fasting glucose indicates the body may be having difficulty managing blood sugar, which is a key feature of diabetes."
    },
    
    "creatinine": {
        "name": "Creatinine",
        "description": "A waste product filtered from blood by the kidneys.",
        "what_it_means": "Creatinine levels indicate how well the kidneys are filtering blood. Higher levels may suggest reduced kidney function.",
        "ranges": {
            "normal": "0.7-1.3 mg/dL (men) / 0.6-1.1 mg/dL (women) - Varies by muscle mass, age, and lab",
            "elevated": "Above normal range may indicate kidney function concerns"
        },
        "importance": "Kidneys filter waste from blood. Monitoring creatinine helps assess kidney function over time."
    },
    
    "uric_acid": {
        "name": "Uric Acid (Urate)",
        "description": "A waste product formed from the breakdown of purines, found in some foods and body tissues.",
        "what_it_means": "Most uric acid dissolves in blood and passes through kidneys into urine. High levels can form crystals.",
        "ranges": {
            "normal": "3.5-7.2 mg/dL (men) / 2.6-6.0 mg/dL (women) - Varies by lab",
            "elevated": "Above normal range - May indicate risk for gout or kidney stones"
        },
        "importance": "High uric acid can cause gout (painful joint inflammation) and may be associated with other health conditions."
    },
    
    "sgot": {
        "name": "SGOT (AST - Aspartate Aminotransferase)",
        "description": "An enzyme found primarily in the liver, but also in heart and muscle tissue.",
        "what_it_means": "When liver or other organs are damaged, SGOT leaks into bloodstream. Elevated levels may indicate liver stress or damage.",
        "ranges": {
            "normal": "10-40 U/L - Varies by lab",
            "elevated": "Above normal - May indicate liver damage, heart damage, or other conditions"
        },
        "importance": "SGOT is a marker that helps assess liver health. Single elevated readings often aren't concerning, but patterns matter."
    },
    
    "sgpt": {
        "name": "SGPT (ALT - Alanine Aminotransferase)",
        "description": "An enzyme found primarily in the liver.",
        "what_it_means": "SGPT is more specific to the liver than SGOT. Elevated levels are more strongly associated with liver cell damage.",
        "ranges": {
            "normal": "7-56 U/L - Varies by lab",
            "elevated": "Above normal - May indicate liver inflammation or damage"
        },
        "importance": "SGPT helps evaluate liver function. Causes of elevation include medications, alcohol, fatty liver, and infections."
    }
}


def explain_metric_prompt(metric_name: str, metric_value: Optional[float] = None) -> tuple:
    """
    Generate a prompt for explaining a specific health metric.
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = HEALTH_AI_SYSTEM_PROMPT
    
    metric_info = METRIC_EXPLANATIONS.get(metric_name.lower(), {})
    
    if not metric_info:
        user_prompt = f"""Please provide an educational explanation of the health metric '{metric_name}'.
        
If this is a valid medical metric, explain:
1. What it measures
2. What normal ranges are
3. Why it matters for health
4. What factors can affect it

If this is not a recognized medical metric, explain that you cannot provide information about it."""
    else:
        name = metric_info.get("name", metric_name)
        description = metric_info.get("description", "")
        what_it_means = metric_info.get("what_it_means", "")
        ranges = metric_info.get("ranges", {})
        limitations = metric_info.get("limitations", "")
        importance = metric_info.get("importance", "")
        
        ranges_text = "\n".join([f"  • {k.replace('_', ' ').title()}: {v}" for k, v in ranges.items()])
        
        value_note = ""
        if metric_value is not None:
            value_note = f"\nThe patient's value is: {metric_value}\nPlease explain what this specific value might indicate in general terms."
        
        user_prompt = f"""Please provide an educational explanation of {name}.

📋 WHAT IT IS:
{description}

🔍 WHAT IT MEANS:
{what_it_means}

📊 GENERAL REFERENCE RANGES:
{ranges_text}

💡 WHY IT MATTERS:
{importance}
"""
        
        if limitations:
            user_prompt += f"\n⚠️ LIMITATIONS:\n{limitations}\n"
        
        if value_note:
            user_prompt += f"\n{value_note}\n"
        
        user_prompt += f"""

Please explain this in educational terms without making any diagnosis.
Remind the reader to consult healthcare professionals for personalized advice.
{MEDICAL_DISCLAIMER}"""
    
    return system_prompt, user_prompt


def get_metric_explanation(metric_name: str) -> Optional[Dict[str, Any]]:
    """Get the explanation data for a specific metric."""
    return METRIC_EXPLANATIONS.get(metric_name.lower())


def get_all_explainable_metrics() -> List[str]:
    """Get list of all metrics that can be explained."""
    return list(METRIC_EXPLANATIONS.keys())