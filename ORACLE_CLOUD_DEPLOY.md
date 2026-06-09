# Deploy MCU Vault on Oracle Cloud Free Tier

Oracle Cloud Always Free provides:
- 1GB RAM ARM instance (Ampere A1)
- 50GB block storage
- 10TB/month bandwidth
- **Free forever** (never expires)

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

---

## Step 3: Connect to Instance

Get your instance's public IP from the Oracle Console, then connect:

```bash
ssh -i /path/to/your/private/key opc@<YOUR_PUBLIC_IP>
```

Or if using password authentication:
```bash
ssh opc@<YOUR_PUBLIC_IP>
```

---

## Step 4: Run Deployment Script

Copy and run the deployment script on your Oracle instance:

```bash
# On your local machine, copy the script
scp -i /path/to/key deploy_oracle_cloud.sh opc@<YOUR_IP>:~/

# Or create it directly on the server with nano/paste
```

Run the script:
```bash
chmod +x deploy_oracle_cloud.sh
./deploy_oracle_cloud.sh
```

---

## Step 5: (Optional) Configure Domain

If you have a domain name:

1. Create A record pointing to your Oracle instance IP:
   ```
   A    @    <YOUR_PUBLIC_IP>
   A    www  <YOUR_PUBLIC_IP>
   ```

2. Install SSL certificate:
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. Update Nginx config with your domain

---

## Step 6: Access Your App

Open your browser:
```
http://<YOUR_PUBLIC_IP>
```

Or with domain:
```
https://yourdomain.com
```

---

## Troubleshooting

### Check service status:
```bash
sudo systemctl status mcu-vault
sudo systemctl status nginx
```

### View logs:
```bash
sudo journalctl -u mcu-vault -f
sudo tail -f /var/log/nginx/error.log
```

### Restart services:
```bash
sudo systemctl restart mcu-vault
sudo systemctl restart nginx
```

### Firewall issues:
```bash
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443
```

---

## Instance Details

| Resource | Specification |
|----------|---------------|
| **Public IP** | Check Oracle Console |
| **SSH Port** | 22 |
| **Web Port** | 80 |
| **App Location** | `/var/www/mcu-vault` |
| **Socket File** | `/var/www/mcu-vault/mcu-vault.sock` |
| **Service Name** | `mcu-vault` |

---

## Important Notes

1. **Persistence**: Files in `/var/www/mcu-vault/static/uploads/` persist on the boot volume
2. **Never delete**: Don't delete the boot volume
3. **Backup**: Consider regular backups of uploaded files
4. **Security**: Change SSH port, disable password auth (recommended for production)

---

## Quick Commands Reference

```bash
# Start app
sudo systemctl start mcu-vault

# Stop app
sudo systemctl stop mcu-vault

# Restart app
sudo systemctl restart mcu-vault

# Check logs
sudo journalctl -u mcu-vault --since "1 hour ago"

# Update code
cd /var/www/mcu-vault
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mcu-vault
```