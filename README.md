# MCU Vault

MCU Vault is a secure Medical Check-Up (MCU) document management system that allows users to store, search, and manage MCU reports with ease.

## Features

- **User Authentication**: Secure registration, login, and logout functionality
- **Dashboard**: View total records, latest uploads, and user statistics
- **MCU Record Management**: Create, edit, delete, and view MCU records
- **File Upload**: Upload PDF, JPG, JPEG, and PNG files
- **Advanced Search**: Search by patient name, company, or MCU date
- **Responsive Design**: Professional medical-themed UI with sidebar navigation
- **Health Metrics (Phase 2A)**: Structured health data entry for medical check-up records
  - Basic Measurements (height, weight, BMI)
  - Vital Signs (blood pressure, heart rate)
  - Blood Sugar (fasting glucose, HbA1c)
  - Lipid Profile (cholesterol, LDL, HDL, triglycerides)
  - Liver Function (SGOT, SGPT)
  - Kidney Function (creatinine, uric acid)
  - Doctor's notes
- **Health Analytics (Phase 2B)**: Analytics, visualization, and comparison
  - Health Analytics Dashboard with latest health snapshot
  - Interactive Trend Charts (Chart.js) for body measurements, blood pressure, blood sugar, and lipid profiles
  - MCU Record Comparison with side-by-side analysis
  - Rule-based Health Status Classification (BMI, Blood Pressure, HbA1c, LDL, HDL, etc.)
  - Color-coded status badges (Green: Normal, Yellow: Borderline, Red: High Risk)
  - CSV export for comparison results

- **OCR Import (Phase 2C)**: Document ingestion and automatic data extraction
  - Upload MCU reports (PDF, JPG, JPEG, PNG)
  - Automatic OCR text extraction using Tesseract
  - Smart field mapping engine for common MCU variations (TB/BB, GDS, SGOT/SGPT, etc.)
  - Review screen with confidence indicators
  - User confirmation before saving (never auto-save)
  - Bulk import for batch processing
  - Error handling for poor quality images, rotated documents, and missing values

- **AI Health Intelligence (Phase 3A)**: AI-powered health insights and explanations
  - AI Health Summary: Natural language summaries of MCU records
  - Historical Comparison: Compare two MCU records with AI analysis
  - Trend Analysis: Analyze health patterns over multiple years
  - Health Timeline: Longitudinal narrative of health journey
  - Explain Metrics: Educational explanations of health metrics
  - AI Health Reports: Downloadable PDF reports with AI-generated insights
  - Provider Abstraction: Supports OpenAI, Anthropic, and Local LLMs
  - Safety First: Medical disclaimers, no diagnoses, encourages professional consultation

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js for interactive trend visualization
- **Authentication**: Flask-Login

## Project Structure

```
mcu-vault/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── config.py             # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # User model
│   │   ├── mcu_record.py    # MCU Record & UploadedFile models
│   │   └── health_metrics.py # Health Metrics model (Phase 2A)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── dashboard.py     # Dashboard routes
│   │   ├── records.py       # MCU record CRUD routes
│   │   ├── upload.py        # File upload routes
│   │   ├── analytics.py     # Health analytics routes (Phase 2B)
│   │   ├── ocr.py           # OCR import routes (Phase 2C)
│   │   └── ai.py            # AI health intelligence routes (Phase 3A)
│   └── services/
│       ├── __init__.py
│       ├── ocr_service.py    # OCR service layer (Phase 2C)
│       └── ocr_mapping.py   # Field mapping engine (Phase 2C)
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py    # AI provider abstraction (Phase 3A)
│       ├── ai_prompts.py    # AI prompt templates (Phase 3A)
│       ├── health_intelligence.py # Health intelligence service (Phase 3A)
│       ├── ocr_service.py   # OCR service layer (Phase 2C)
│       └── ocr_mapping.py   # Field mapping engine (Phase 2C)
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py       # Utility functions
│       └── health_classification.py # Health classification rules (Phase 2B)
├── migrations/
│   └── add_health_metrics.py # Database migration script
├── static/
│   ├── css/
│   │   └── styles.css       # Main stylesheet
│   ├── js/
│   │   └── main.js          # Main JavaScript
│   └── uploads/             # Uploaded files storage
├── templates/
│   ├── base.html            # Base template
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   ├── dashboard.html       # Dashboard page (enhanced in Phase 2B)
│   ├── analytics/
│   │   └── health_dashboard.html # Health analytics dashboard (Phase 2B)
│   ├── ocr/
│   │   ├── upload.html      # OCR upload page (Phase 2C)
│   │   ├── review.html      # OCR review screen (Phase 2C)
│   │   ├── bulk.html        # Bulk import page (Phase 2C)
│   │   └── bulk_progress.html # Bulk processing progress (Phase 2C)
│   ├── ai/
│   │   ├── index.html       # AI health main page (Phase 3A)
│   │   ├── compare.html     # AI comparison page (Phase 3A)
│   │   ├── trends.html      # AI trends analysis (Phase 3A)
│   │   └── timeline.html    # AI timeline narrative (Phase 3A)
│   ├── records/
│   │   ├── list.html        # Records list page
│   │   ├── detail.html      # Record detail page
│   │   ├── create.html      # Create record page
│   │   ├── edit.html        # Edit record page
│   │   └── compare.html     # Record comparison page (Phase 2B)
│   └── upload.html          # File upload page
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_health_classification.py # Health classification tests (Phase 2B)
│   ├── test_analytics_routes.py      # Analytics routes tests (Phase 2B)
│   ├── test_auth.py         # Authentication tests
│   ├── test_ocr.py          # OCR tests (Phase 2C)
│   └── test_ai_health.py    # AI health tests (Phase 3A)
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md                # This file
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mcu-vault
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set your SECRET_KEY
   ```

5. **Initialize the database**
   The database will be automatically created on first run.
   Alternatively, you can create it manually:
   ```bash
   python -c "from app import create_app; from app import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created successfully!')"
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   Open your browser and navigate to: `http://localhost:5000`

## Usage

### Registration & Login
1. Visit the application URL
2. Click "Register" to create a new account
3. Fill in your details and submit
4. Login with your credentials

### Managing MCU Records
1. After login, you'll be directed to the dashboard
2. Click "New Record" to create an MCU record
3. Fill in patient information and upload relevant files
4. Use the search bar to find records by patient name, company, or date
5. Click on any record to view details, edit, or delete

### Health Analytics (Phase 2B)
1. Access the Health Analytics dashboard from the sidebar
2. View your latest health snapshot with status classifications
3. Explore trend charts for body measurements, blood pressure, blood sugar, and lipid profiles
4. Use the Compare Records feature to analyze changes between two check-ups
5. Export comparison results as CSV for further analysis

### File Upload
- Supported formats: PDF, JPG, JPEG, PNG
- Maximum file size: 16MB
- Files are associated with specific MCU records

## Health Classification Guidelines (Phase 2B)

The system uses rule-based classification for health metrics:

### BMI
| Classification | Range |
|----------------|-------|
| Underweight | < 18.5 |
| Normal | 18.5 - 24.9 |
| Overweight | 25.0 - 29.9 |
| Obese | >= 30 |

### Blood Pressure
| Classification | Systolic | Diastolic |
|----------------|----------|-----------|
| Normal | < 120 | < 80 |
| Elevated | 120-129 | < 80 |
| Hypertension Stage 1 | 130-139 | 80-89 |
| Hypertension Stage 2 | >= 140 | >= 90 |

### HbA1c
| Classification | Range |
|----------------|-------|
| Normal | < 5.7% |
| Prediabetes | 5.7 - 6.4% |
| Diabetes | >= 6.5% |

### LDL Cholesterol
| Classification | Range (mg/dL) |
|----------------|---------------|
| Optimal | < 100 |
| Near Optimal | 100 - 129 |
| Borderline High | 130 - 159 |
| High | 160 - 189 |
| Very High | >= 190 |

## Testing

Run the automated tests:

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_health_classification.py -v
pytest tests/test_analytics_routes.py -v
```

## Security Considerations

- Passwords are hashed using Werkzeug's security functions
- Sessions are managed securely with Flask-Login
- File uploads are validated for type and size
- All user inputs are sanitized
- CSRF protection is implemented

## Database Schema

### Users Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | VARCHAR(80) | Unique username |
| email | VARCHAR(120) | Unique email address |
| password_hash | VARCHAR(256) | Hashed password |
| created_at | DATETIME | Account creation timestamp |

### MCU Records Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| patient_name | VARCHAR(200) | Patient's full name |
| company | VARCHAR(200) | Company name |
| mcu_date | DATE | Date of medical check-up |
| status | VARCHAR(50) | Health status |
| notes | TEXT | Additional notes |
| user_id | INTEGER | Foreign key to users |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

### Uploaded Files Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| filename | VARCHAR(255) | Stored filename |
| original_filename | VARCHAR(255) | Original filename |
| file_type | VARCHAR(50) | MIME type |
| file_size | INTEGER | File size in bytes |
| mcu_record_id | INTEGER | Foreign key to MCU records |
| uploaded_at | DATETIME | Upload timestamp |

### Health Metrics Table (Phase 2A)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| mcu_record_id | INTEGER | Foreign key to MCU records (unique) |
| height_cm | FLOAT | Height in centimeters |
| weight_kg | FLOAT | Weight in kilograms |
| bmi | FLOAT | Body Mass Index |
| systolic_bp | INTEGER | Systolic blood pressure (mmHg) |
| diastolic_bp | INTEGER | Diastolic blood pressure (mmHg) |
| heart_rate | INTEGER | Heart rate (bpm) |
| fasting_glucose | FLOAT | Fasting glucose (mg/dL) |
| hba1c | FLOAT | HbA1c percentage |
| total_cholesterol | FLOAT | Total cholesterol (mg/dL) |
| ldl | FLOAT | LDL cholesterol (mg/dL) |
| hdl | FLOAT | HDL cholesterol (mg/dL) |
| triglycerides | FLOAT | Triglycerides (mg/dL) |
| sgot | FLOAT | SGOT/AST (U/L) |
| sgpt | FLOAT | SGPT/ALT (U/L) |
| creatinine | FLOAT | Creatinine (mg/dL) |
| uric_acid | FLOAT | Uric acid (mg/dL) |
| doctor_notes | TEXT | Doctor's observations |
| created_at | DATETIME | Record creation timestamp |
| updated_at | DATETIME | Last update timestamp |

## Data Seeding Utility

MCU Vault includes a data seeding utility for generating realistic test data with historical health progression.

### Usage

```bash
# Seed demo data (default demo user)
python scripts/seed_data.py

# Reset and reseed (clears existing demo data)
python scripts/seed_data.py --reset

# Seed data for a specific user email
python scripts/seed_data.py --user-email user@example.com
```

### What Gets Created

- **1 Demo User**: `demo@mcu-vault.com` / `demo123`
- **15 MCU Records**: Spanning 2012-2026
- **15 Health Metrics**: One for each record

### Health Progression Timeline

The seed data creates believable health trends over 14 years:

| Period | Health Status |
|--------|---------------|
| 2012-2017 | Healthy baseline with normal metrics |
| 2018-2021 | Weight gain, LDL increasing |
| 2021 | Prediabetes threshold (fasting glucose ~112) |
| 2023 | Borderline hypertension (BP 138/88) |
| 2024-2025 | Lifestyle improvements begin |
| 2026 | Improved BMI, glucose, and blood pressure |

### Generated Metrics

Each health record includes:
- Body measurements: height, weight, BMI
- Vital signs: blood pressure, heart rate
- Blood sugar: fasting glucose, HbA1c
- Lipid profile: total cholesterol, LDL, HDL, triglycerides
- Liver function: SGOT, SGPT
- Kidney function: creatinine, uric acid

### Running Tests

```bash
# Run seed data tests
pytest tests/test_seed_data.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, please open an issue on the repository.