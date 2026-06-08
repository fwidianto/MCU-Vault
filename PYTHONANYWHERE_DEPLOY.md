# PythonAnywhere Deployment Guide

## Quick Deploy (Using API)

### Prerequisites
1. Get your PythonAnywhere API token from:
   https://www.pythonanywhere.com/account/#api_token

2. Install the deployment script:
```bash
pip install requests
```

### Deploy with API
```bash
python deploy_pythonanywhere.py \
    --username YOUR_USERNAME \
    --token YOUR_API_TOKEN \
    --source .
```

## Manual Deployment Steps

### Step 1: Login to PythonAnywhere
Go to https://www.pythonanywhere.com/login/

### Step 2: Create Web App
1. Go to the **Web** tab
2. Click **Add a new web app**
3. Select **Flask** as framework
4. Choose **Python 3.11**
5. For the app directory, enter: `/home/YOUR_USERNAME/mcu-vault`

### Step 3: Upload Code
Option A - Using Files tab:
1. Go to **Files** tab
2. Navigate to `/home/YOUR_USERNAME/`
3. Click **New directory** → name it `mcu-vault`
4. Upload all project files

Option B - Using Bash:
```bash
cd ~
git clone https://github.com/fwidianto/MCU-Vault.git mcu-vault
cd mcu-vault
```

### Step 4: Set Up Virtual Environment
Open a **Bash console** and run:
```bash
cd ~/mcu-vault
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 5: Configure WSGI File
1. Go to **Web** tab
2. Click on the WSGI configuration file link
3. Replace the content with:

```python
import sys
import os

# Add your project directory to the path
path = '/home/YOUR_USERNAME/mcu-vault'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['SECRET_KEY'] = 'your-secret-key-here'
os.environ['FLASK_ENV'] = 'production'

# Import and run the Flask app
from run import app as application
```

### Step 6: Configure Static Files
In the Web tab, add a static files mapping:
- URL: `/static/`
- Directory: `/home/YOUR_USERNAME/mcu-vault/static/`

### Step 7: Reload
Click the **Reload** button on the Web tab.

### Step 8: Visit Your Site
Your app will be live at: `https://YOUR_USERNAME.pythonanywhere.com`

## Free Tier Limitations

The free tier has some limitations:
- No API access for file operations
- Web app sleeps after 3 months of inactivity
- No custom domain support
- Limited to pythonanywhere.com subdomain

For persistent hosting, consider upgrading to a paid plan or using Render.com.

## Troubleshooting

### Import Errors
Make sure the virtual environment is set correctly in the Web tab.

### Database Errors
SQLite works but the path must be absolute. Edit `app/__init__.py`:
```python
basedir = os.path.abspath(os.path.dirname(__file__)
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'mcu_vault.db')}"
```

### Static Files Not Loading
Check the static files mapping in the Web tab and ensure the path is correct.

## Environment Variables

Set these in the Web tab's environment variables section:
- `SECRET_KEY`: A random secure string
- `FLASK_ENV`: `production`