# MCU Vault

MCU Vault is a secure Medical Check-Up (MCU) document management system that allows users to store, search, and manage MCU reports with ease.

## Features

- **User Authentication**: Secure registration, login, and logout functionality
- **Dashboard**: View total records, latest uploads, and user statistics
- **MCU Record Management**: Create, edit, delete, and view MCU records
- **File Upload**: Upload PDF, JPG, JPEG, and PNG files
- **Advanced Search**: Search by patient name, company, or MCU date
- **Responsive Design**: Professional medical-themed UI with sidebar navigation

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
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
│   │   └── mcu_record.py    # MCU Record & UploadedFile models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── dashboard.py     # Dashboard routes
│   │   ├── records.py       # MCU record CRUD routes
│   │   └── upload.py        # File upload routes
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # Utility functions
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
│   ├── dashboard.html       # Dashboard page
│   ├── records/
│   │   ├── list.html        # Records list page
│   │   ├── detail.html      # Record detail page
│   │   ├── create.html      # Create record page
│   │   └── edit.html        # Edit record page
│   └── upload.html          # File upload page
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
   python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created successfully!')"
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

### File Upload
- Supported formats: PDF, JPG, JPEG, PNG
- Maximum file size: 16MB
- Files are associated with specific MCU records

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