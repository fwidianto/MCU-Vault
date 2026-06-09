#!/bin/bash
# Oracle Cloud Always Free - MCU Vault Deployment Script
# Run this on your Oracle Cloud instance after creation

set -e

echo "=========================================="
echo "  MCU Vault - Oracle Cloud Deployment"
echo "=========================================="

# Update system
echo "[1/8] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "[2/8] Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Create app directory
echo "[3/8] Setting up application directory..."
sudo mkdir -p /var/www/mcu-vault
sudo chown -R ubuntu:ubuntu /var/www/mcu-vault

# Clone repository (replace with your repo URL)
echo "[4/8] Cloning MCU Vault repository..."
cd /var/www/mcu-vault
git clone https://github.com/fwidianto/MCU-Vault.git .
# Or if you want to use local files, upload them instead

# Create virtual environment
echo "[5/8] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create systemd service
echo "[6/8] Creating systemd service..."
sudo tee /etc/systemd/system/mcu-vault.service > /dev/null <<EOF
[Unit]
Description=MCU Vault Flask Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/mcu-vault
Environment="PATH=/var/www/mcu-vault/venv/bin"
ExecStart=/var/www/mcu-vault/venv/bin/gunicorn --workers 2 --bind unix:/var/www/mcu-vault/mcu-vault.sock run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "[7/8] Configuring Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/mcu-vault > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /var/www/mcu-vault/static/;
        expires 30d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/mcu-vault/mcu-vault.sock;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/mcu-vault /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Start services
echo "[8/8] Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable mcu-vault
sudo systemctl start mcu-vault
sudo systemctl restart nginx

# Firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Your MCU Vault should be accessible at:"
echo "http://$(curl -s ifconfig.me):80"
echo ""
echo "To check status:"
echo "  sudo systemctl status mcu-vault"
echo "  sudo systemctl status nginx"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u mcu-vault -f"
echo "=========================================="