"""
MCU Vault Application Entry Point.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine configuration
config_name = os.environ.get('FLASK_ENV', 'development')

# Create and run the application
from app import create_app

app = create_app(config_name)

if __name__ == '__main__':
    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = config_name == 'development'
    
    print(f"\n{'='*50}")
    print("MCU Vault - Medical Check-Up Management System")
    print(f"{'='*50}")
    print(f"Server running at: http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"{'='*50}\n")
    
    app.run(host=host, port=port, debug=debug)