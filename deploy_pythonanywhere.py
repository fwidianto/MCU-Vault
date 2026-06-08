#!/usr/bin/env python3
"""
PythonAnywhere Deployment Script for MCU-Vault

Usage:
    python deploy_pythonanywhere.py --username YOUR_USERNAME --token YOUR_API_TOKEN

Or set environment variables:
    export PYTHONANYWHERE_USERNAME=your_username
    export PYTHONANYWHERE_API_TOKEN=your_api_token
    python deploy_pythonanywhere.py
"""

import argparse
import os
import sys
import zipfile
import tempfile
import requests
from pathlib import Path


class PythonAnywhereDeployer:
    """Deploy MCU-Vault to PythonAnywhere using their API."""
    
    BASE_URL = "https://www.pythonanywhere.com/api/v0"
    
    def __init__(self, username: str, api_token: str):
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        })
    
    def _api_url(self, endpoint: str) -> str:
        return f"{self.BASE_URL}/{endpoint}"
    
    def check_status(self) -> dict:
        """Check API connection status."""
        response = self.session.get(self._api_url("status/"))
        response.raise_for_status()
        return response.json()
    
    def get_account_info(self) -> dict:
        """Get account information."""
        response = self.session.get(self._api_url(f"account/{self.username}/"))
        response.raise_for_status()
        return response.json()
    
    def create_webapp(self, domain: str) -> dict:
        """Create a new webapp."""
        response = self.session.post(
            self._api_url("webapps/"),
            json={"domain": domain}
        )
        if response.status_code == 400:
            # Webapp might already exist
            return {"message": "Webapp already exists or domain taken"}
        response.raise_for_status()
        return response.json()
    
    def get_webapp(self, domain: str) -> dict:
        """Get webapp configuration."""
        response = self.session.get(self._api_url(f"webapps/{domain}/"))
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    
    def set_python_version(self, domain: str, version: str = "3.11") -> dict:
        """Set Python version for the webapp."""
        response = self.session.patch(
            self._api_url(f"webapps/{domain}/"),
            json={"python_version": version}
        )
        response.raise_for_status()
        return response.json()
    
    def upload_files(self, domain: str, source_dir: str) -> dict:
        """Upload files to the webapp using File Upload API."""
        # For PythonAnywhere, we need to use their file upload API
        # This is a simplified version - in production, you might use ssh/scp
        source_path = Path(source_dir)
        
        # Create a zip of the source code
        zip_path = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        with zipfile.ZipFile(zip_path.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_path.rglob('*'):
                if file_path.is_file() and '__pycache__' not in str(file_path):
                    arcname = file_path.relative_to(source_path)
                    zipf.write(file_path, arcname)
        
        # Upload using the files API
        with open(zip_path.name, 'rb') as f:
            files = {'content': (f.name, f, 'application/zip')}
            # Note: PythonAnywhere File Upload API requires different approach
            # We'll return instructions for manual upload
            pass
        
        os.unlink(zip_path.name)
        return {"message": "Files prepared for upload. Use SSH or manual upload."}
    
    def configure_virtualenv(self, domain: str, virtualenv_path: str) -> dict:
        """Configure virtual environment."""
        response = self.session.post(
            self._api_url(f"webapps/{domain}/virtualenvs/"),
            json={"path": virtualenv_path}
        )
        if response.status_code == 400:
            return {"message": "Virtualenv already configured"}
        response.raise_for_status()
        return response.json()
    
    def set_startup_file(self, domain: str, script_path: str) -> dict:
        """Set the WSGI configuration file."""
        response = self.session.patch(
            self._api_url(f"webapps/{domain}/"),
            json={"source_directory": script_path}
        )
        response.raise_for_status()
        return response.json()
    
    def reload_webapp(self, domain: str) -> dict:
        """Reload the webapp to apply changes."""
        response = self.session.post(
            self._api_url(f"webapps/{domain}/reload/")
        )
        response.raise_for_status()
        return response.json()
    
    def deploy(self, source_dir: str, domain: str = None) -> dict:
        """
        Full deployment process.
        
        Args:
            source_dir: Path to the MCU-Vault source code
            domain: The domain subdomain (e.g., 'yourusername.pythonanywhere.com')
        """
        if domain is None:
            domain = f"{self.username}.pythonanywhere.com"
        
        print(f"🚀 Starting deployment to {domain}")
        
        # Step 1: Check API status
        print("📡 Checking API connection...")
        status = self.check_status()
        print(f"   ✓ API connected: {status.get('status', 'unknown')}")
        
        # Step 2: Create or get webapp
        print("🔧 Configuring webapp...")
        webapp = self.get_webapp(domain)
        if webapp is None:
            result = self.create_webapp(domain)
            print(f"   ✓ Webapp created")
        else:
            print(f"   ✓ Webapp exists")
        
        # Step 3: Set Python version
        print("🐍 Setting Python version to 3.11...")
        self.set_python_version(domain, "3.11")
        print("   ✓ Python version set")
        
        # Step 4: Provide deployment instructions
        print("\n" + "="*60)
        print("📋 DEPLOYMENT INSTRUCTIONS FOR PythonAnywhere")
        print("="*60)
        print(f"""
Since the PythonAnywhere Free tier has limited API access, 
here's how to deploy manually:

1. LOGIN to PythonAnywhere:
   https://www.pythonanywhere.com/login/

2. Go to: Web tab → Create a new web app

3. Choose:
   - Framework: Flask
   - Python version: Python 3.11
   - App directory: /home/{self.username}/mcu-vault

4. Upload your code:
   - Use the Files tab to navigate to /home/{self.username}/
   - Create folder 'mcu-vault'
   - Upload all files from your project

5. Open a Bash console and run:
   cd ~/mcu-vault
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

6. Configure WSGI file:
   - Edit /var/www/{self.username}_pythonanywhere_com_wsgi.py
   - Point it to your Flask app

7. Reload your webapp from the Web tab

Your app will be live at: https://{domain}
""")
        print("="*60 + "\n")
        
        return {"domain": domain, "status": "instructions_provided"}


def main():
    parser = argparse.ArgumentParser(description="Deploy MCU-Vault to PythonAnywhere")
    parser.add_argument("--username", "-u", help="PythonAnywhere username")
    parser.add_argument("--token", "-t", help="PythonAnywhere API token")
    parser.add_argument("--domain", "-d", help="Domain (default: username.pythonanywhere.com)")
    parser.add_argument("--source", "-s", default=".", help="Source directory to deploy")
    
    args = parser.parse_args()
    
    # Get credentials from args or environment
    username = args.username or os.environ.get("PYTHONANYWHERE_USERNAME")
    token = args.token or os.environ.get("PYTHONANYWHERE_API_TOKEN")
    
    if not username or not token:
        print("❌ Error: PythonAnywhere credentials required!")
        print("\nProvide credentials via:")
        print("  1. Command line: --username YOUR_USER --token YOUR_TOKEN")
        print("  2. Environment: PYTHONANYWHERE_USERNAME and PYTHONANYWHERE_API_TOKEN")
        print("\nGet your API token from: https://www.pythonanywhere.com/account/#api_token")
        sys.exit(1)
    
    # Run deployment
    deployer = PythonAnywhereDeployer(username, token)
    
    try:
        result = deployer.deploy(source_dir=args.source, domain=args.domain)
        print(f"✅ Deployment configuration complete!")
        print(f"   Domain: {result['domain']}")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()