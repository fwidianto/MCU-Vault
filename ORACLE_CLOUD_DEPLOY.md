# Deploy MCU Vault on Oracle Cloud Free Tier - VERIFIED DEPLOYMENT GUIDE

> **Last Updated**: June 2026 - Verified working deployment with Flask template path fix

Oracle Cloud Always Free provides:
- 1GB RAM ARM instance (Ampere A1)
- 50GB block storage
- 10TB/month bandwidth
- **Free forever** (never expires)

---

## Prerequisites

- Oracle Cloud Free Tier account
- SSH key pair (or use Oracle Cloud's generated key)
- Basic Linux command line knowledge

---

## Step 1: Create Oracle Cloud Account

1. Go to https://cloud.oracle.com/
2. Click **Sign Up** → **Create a free account**
3. Fill in your details (email, password, phone verification)
4. Add credit card (for verification only, won't be charged)

---

## Step 2: Create a Compute Instance

1. Log in to Oracle Cloud Console: https://cloud.oracle.com/
2. Go to **Hamburger Menu** → **Compute** → **Instances**
3. Click **Create Instance**

### Configure Instance:
| Setting | Value |
|---------|-------|
| **Name** | `mcu-vault` |
| **Compartment** | Root (or create new) |
| **Image** | Ubuntu 22.04 LTS |
| **Shape** | Ampere (ARM) - Always Free eligible |
| **Shape Name** | VM.Standard.A1.Flex (1GB RAM, 1 OCPU) |
| **Subnet** | Public Subnet |
| **Assign public IP** | ✅ Yes |
| **SSH Keys** | Generate new or use existing |

4. Click **Create** and wait for instance to provision (~2 minutes)
5. **IMPORTANT**: Download the private key file when Oracle generates one for you

---

## Step 3: Connect to Instance

Get your instance's public IP from the Oracle Console, then connect:

```bash
# Set proper permissions on your key file
chmod 600 /path/to/your/private/key.pem

# Connect to the instance
ssh -i /path/to/your/private/key.pem opc@<YOUR_PUBLIC_IP>
```

---

## Step 4: Fresh Ubuntu Setup (Run These Commands on the Server)

Run these commands in sequence on your Oracle Cloud instance:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git ufw

# Create application directory
sudo mkdir -p /var/www/mcu-vault
sudo chown -R opc:opc /var/www/mcu-vault
```

---

## Step 5: Clone Repository and Setup

```bash
# Navigate to app directory
cd /var/www/mcu-vault

# Clone the repository (make sure you're in the right directory)
git clone https://github.com/fwidianto/MCU-Vault.git .

# Verify the clone was successful
ls -la
# You should see: app/  static/  templates/  run.py  requirements.txt

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify Flask can be imported
python -c "from app import create_app; print('Flask setup OK')"
```

---

## Step 6: Configure Environment Variables

```bash
# Create .env file with production settings
cat > /var/www/mcu-vault/.env << 'EOF'
SECRET_KEY=your-production-secret-key-change-this
FLASK_ENV=production
DATABASE_URL=sqlite:///mcu_vault.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
EOF

# Make sure uploads directory exists
mkdir -p /var/www/mcu-vault/static/uploads
chmod 755 /var/www/mcu-vault/static/uploads
```

---

## Step 7: Create Systemd Service

```bash
# Create the systemd service file
sudo tee /etc/systemd/system/mcu-vault.service > /dev/null <<'EOF'
[Unit]
Description=MCU Vault Flask Application
After=network.target

[Service]
User=opc
Group=opc
WorkingDirectory=/var/www/mcu-vault
Environment="PATH=/var/www/mcu-vault/venv/bin"
EnvironmentFile=/var/www/mcu-vault/.env
ExecStart=/var/www/mcu-vault/venv/bin/gunicorn --workers 2 --bind unix:/var/www/mcu-vault/mcu-vault.sock run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable mcu-vault
```

---

## Step 8: Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/mcu-vault > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    # Serve static files directly
    location /static/ {
        alias /var/www/mcu-vault/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn via Unix socket
    location / {
        include /etc/nginx/proxy_params;
        proxy_pass http://unix:/var/www/mcu-vault/mcu-vault.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/mcu-vault /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 9: Start the Application

```bash
# Start the MCU Vault service
sudo systemctl start mcu-vault

# Check the service status
sudo systemctl status mcu-vault

# View logs if there are any issues
sudo journalctl -u mcu-vault -n 50 --no-pager
```

---

## Step 10: Configure Firewall (Optional but Recommended)

```bash
# Allow SSH (already should be)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall (be careful not to lock yourself out!)
sudo ufw enable

# Check firewall status
sudo ufw status
```

---

## Step 11: Verify Deployment

Test from your local machine:

```bash
# Test if the app is running
curl http://<YOUR_PUBLIC_IP>/login

# You should see the login page HTML

# Test static files
curl -I http://<YOUR_PUBLIC_IP>/static/css/styles.css
# Should return 200 OK
```

---

## Step 12: (Optional) Configure Domain with SSL

If you have a domain name:

```bash
# Install SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow the prompts to complete SSL setup
```

---

## Troubleshooting

### Service won't start?
```bash
# Check logs
sudo journalctl -u mcu-vault -f

# Common issues:
# - .env file missing: create it with SECRET_KEY
# - Permissions: sudo chown -R opc:opc /var/www/mcu-vault
# - Port already in use: sudo lsof -i :80
```

### Templates not loading?
```bash
# Verify templates are in the right place
ls -la /var/www/mcu-vault/templates/
# Should contain: base.html, login.html, dashboard.html, etc.

# Check Flask app path
cd /var/www/mcu-vault
source venv/bin/activate
python -c "from app import create_app; app = create_app(); print(app.template_folder)"
# Should show: /var/www/mcu-vault/templates
```

### Database issues?
```bash
# Check if database exists
ls -la /var/www/mcu-vault/*.db

# If not, Flask should create it automatically on first request
# If corrupted, delete and let it recreate:
# rm /var/www/mcu-vault/mcu_vault.db
```

### Nginx 502 Bad Gateway?
```bash
# Check if Gunicorn is running
sudo systemctl status mcu-vault

# Check socket file exists
ls -la /var/www/mcu-vault/mcu-vault.sock

# Restart both services
sudo systemctl restart mcu-vault
sudo systemctl restart nginx
```

---

## Updating the Application

```bash
# Connect to server
ssh -i /path/to/key opc@<YOUR_IP>

# Navigate to app directory
cd /var/www/mcu-vault

# Pull latest changes
git pull origin main

# Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart the service
sudo systemctl restart mcu-vault

# Check status
sudo systemctl status mcu-vault
```

---

## Complete Server Reset (Nuclear Option)

If you need to completely rebuild:

```bash
# STOP AND DISABLE CURRENT SERVICE
sudo systemctl stop mcu-vault
sudo systemctl disable mcu-vault

# REMOVE OLD DIRECTORY (WARNING: THIS DELETES ALL DATA!)
sudo rm -rf /var/www/mcu-vault

# START FRESH FROM STEP 5
```

---

## Files That Need Backup Before Wiping

If you want to preserve data before a nuclear reset:

```bash
# Backup uploads (important files!)
sudo cp -r /var/www/mcu-vault/static/uploads /tmp/mcu-uploads-backup

# Backup database
sudo cp /var/www/mcu-vault/mcu_vault.db /tmp/mcu_vault.db.backup

# Backup .env file (contains your secret key!)
sudo cp /var/www/mcu-vault/.env /tmp/mcu-vault.env.backup
```

---

## Instance Details Reference

| Resource | Specification |
|----------|---------------|
| **Public IP** | Check Oracle Console |
| **SSH Port** | 22 |
| **Web Port** | 80 |
| **App Location** | `/var/www/mcu-vault` |
| **Socket File** | `/var/www/mcu-vault/mcu-vault.sock` |
| **Service Name** | `mcu-vault` |
| **Database** | `/var/www/mcu-vault/mcu_vault.db` |
| **Uploads** | `/var/www/mcu-vault/static/uploads/` |

---

## Quick Commands Reference

```bash
# Start app
sudo systemctl start mcu-vault

# Stop app
sudo systemctl stop mcu-vault

# Restart app
sudo systemctl restart mcu-vault

# Check status
sudo systemctl status mcu-vault

# View logs
sudo journalctl -u mcu-vault -f

# Check Nginx status
sudo systemctl status nginx

# Test locally on server
curl http://localhost/login
```

---

## Important Notes

1. **Persistence**: Files in `/var/www/mcu-vault/static/uploads/` persist on the boot volume
2. **Never delete**: Don't delete the boot volume when terminating instances
3. **Backup**: Regular backups of uploaded files and database recommended
4. **Security**: Change SSH port, disable password auth (recommended for production)
5. **Environment**: Always set `SECRET_KEY` in production