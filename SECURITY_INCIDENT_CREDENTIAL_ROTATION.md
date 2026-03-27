# SECURITY INCIDENT - Credential Rotation Guide

## ⚠️ CRITICAL: Compromised Credentials Detected

**Date:** November 15, 2025  
**Severity:** HIGH  
**Status:** Action Required Immediately

The following credentials were exposed in public GitHub commits and must be rotated immediately.

## Affected Services and Credentials

### 1. PostgreSQL Database
- **Exposed:** Username `grain`, Password `teomeo2358`, Host `65.108.68.57:5433`
- **Impact:** Full database access
- **Action Required:**
  ```bash
  # Connect to PostgreSQL and change password
  psql -h 65.108.68.57 -p 5433 -U grain postgres
  ALTER USER grain WITH PASSWORD 'new_secure_password_here';
  ```
- **Update in:** All `.env.prod` files
- **Reference:** https://howtorotate.com/docs/services/postgresql/

### 2. RabbitMQ
- **Exposed:** User `civaschenko`, Password `Teodorathome11`, Host `65.108.68.57:5672`
- **Impact:** Message queue access, potential data manipulation
- **Action Required:**
  ```bash
  # Access RabbitMQ management interface or CLI
  rabbitmqctl change_password civaschenko new_secure_password
  # OR create a new user and delete the old one
  rabbitmqctl add_user new_user new_secure_password
  rabbitmqctl set_permissions -p / new_user ".*" ".*" ".*"
  rabbitmqctl delete_user civaschenko
  ```
- **Update in:** `backend/.env.prod`, `notifications/.env.prod`, `chat-room/.env.prod`
- **Reference:** https://howtorotate.com/docs/services/rabbitmq/

### 3. Redis
- **Exposed:** Password `Teodorathome`, Host `65.108.68.57:6379`
- **Impact:** Cache access, session hijacking potential
- **Action Required:**
  ```bash
  # Connect to Redis and set new password
  redis-cli -h 65.108.68.57 -p 6379
  AUTH Teodorathome
  CONFIG SET requirepass new_secure_password
  CONFIG REWRITE
  ```
- **Update in:** All `.env.prod` files
- **Reference:** https://howtorotate.com/docs/services/redis/

### 4. JWT Secret
- **Exposed:** `Avy8XuxvccZkogNVOi7DSeKIb+VxTc1Wwspits6rs0I7cUFTYngnwlC1xJioUVyX6bP7xVf/VQkp0Cal8mJhJA==`
- **Impact:** Critical - Token forgery, authentication bypass
- **Action Required:**
  ```python
  # Generate new JWT secret
  import secrets
  new_secret = secrets.token_urlsafe(64)
  print(new_secret)
  ```
- **Note:** This will invalidate all existing JWT tokens. Users will need to re-authenticate.
- **Update in:** All `.env.prod` files

### 5. Payment API Keys

#### FONDY
- **Exposed:** Merchant ID `1555037`, Key `z0LvpvmJZOXo14ezf3oL43Fs5p18XNbQ`
- **Impact:** Unauthorized payment processing
- **Action Required:**
  1. Log into FONDY merchant dashboard
  2. Generate new API key
  3. Revoke the compromised key
- **Update in:** `backend/.env.prod`

#### LiqPay
- **Exposed:** Public Key `i75916062378`, Private Key `2gIF3eZlTmG3eDGB8nGETJlMMe0igw76nWy2wlZb`
- **Impact:** Payment manipulation, potential financial loss
- **Action Required:**
  1. Log into LiqPay account
  2. Navigate to API section
  3. Regenerate private key
  4. Update public key if needed
- **Update in:** `backend/.env.prod`
- **Reference:** https://howtorotate.com/docs/services/liqpay/

#### NOWPayments
- **Exposed:** API Key `S4AFSMN-Y4142XR-JX4MEMY-S0D1ASM`, IPN Secret `kkqP3jd/yCLDxT8/N0PUAqY46ZaNBf94`
- **Impact:** Cryptocurrency payment manipulation
- **Action Required:**
  1. Log into NOWPayments dashboard
  2. Revoke current API key
  3. Generate new API key and IPN secret
- **Update in:** `backend/.env.prod`
- **Reference:** https://howtorotate.com/docs/services/nowpayments/

### 6. Mailtrap
- **Exposed:** 
  - Transactional Pass: `f8af4ff711938653adca6a9b825d2214`
  - Bulk Pass: `4afc13f87ce874bac30477264b3786ac`
- **Impact:** Email service abuse, spam potential
- **Action Required:**
  1. Log into Mailtrap account
  2. Navigate to SMTP settings
  3. Regenerate passwords for both transactional and bulk accounts
- **Update in:** `notifications/.env.prod`
- **Reference:** https://howtorotate.com/docs/services/mailtrap/

### 7. Telegram Bot
- **Exposed:** Token `8475535343:AAGSV-T_P0j5uJAdaLthvqeBi4pgldsXVWo`
- **Impact:** Bot impersonation, unauthorized messages
- **Action Required:**
  1. Contact @BotFather on Telegram
  2. Use `/revoke` command for your bot
  3. Generate new token
  4. Update webhook if configured
- **Update in:** `notifications/.env.prod`
- **Reference:** https://howtorotate.com/docs/services/telegram/

### 8. Password Recovery Secret
- **Exposed:** `3dda5e0169748efd2f5062c91625204246eebd405af471ad0521a714fdc1a176`
- **Impact:** Password reset token forgery
- **Action Required:**
  ```python
  # Generate new recovery secret
  import secrets
  new_secret = secrets.token_hex(32)
  print(new_secret)
  ```
- **Update in:** `backend/.env.prod`

## Immediate Steps Taken

✅ 1. `.env.prod` files removed from git tracking  
✅ 2. `.gitignore` already configured to prevent future commits  
✅ 3. Template files created (`.env.prod.example`) with placeholders  

## Required Actions (IN ORDER)

### Step 1: Rotate All Credentials (URGENT)
Follow the rotation instructions above for each service. Do this IMMEDIATELY, even if:
- The repository is now private
- The files have been removed from current version
- The credentials have been removed from git history

### Step 2: Update Environment Files
After rotating credentials, update the production `.env.prod` files:
```bash
# DO NOT commit these files!
# Update manually on production servers or via secure deployment process
backend/.env.prod
notifications/.env.prod
chat-room/.env.prod
```

### Step 3: Restart All Services
After updating credentials:
```bash
# Restart all services to pick up new credentials
docker-compose down
docker-compose up -d
```

### Step 4: Monitor for Suspicious Activity
- Check database access logs for unauthorized queries
- Review RabbitMQ message queue for unexpected messages
- Monitor payment gateway for unauthorized transactions
- Check email service for unusual sending patterns
- Review application logs for authentication anomalies

### Step 5: (Optional) Clean Git History
⚠️ **WARNING:** This is a destructive operation and will require force-pushing

If you want to remove credentials from git history:
```bash
# Use BFG Repo-Cleaner (recommended)
git clone --mirror https://github.com/kivaschenko/graintrade-info.git
bfg --replace-text passwords.txt graintrade-info.git
cd graintrade-info.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force

# OR use git-filter-repo
pip install git-filter-repo
git filter-repo --path backend/.env.prod --invert-paths
git filter-repo --path notifications/.env.prod --invert-paths
git filter-repo --path chat-room/.env.prod --invert-paths
```

**Important:** Coordinate with all team members before doing this, as it will require everyone to re-clone the repository.

Reference: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

## Future Prevention

### 1. Use Environment Variable Management
Consider using:
- **HashiCorp Vault** for secret management
- **AWS Secrets Manager** or **Azure Key Vault** for cloud deployments
- **Docker Secrets** for containerized applications
- **GitHub Secrets** for CI/CD pipelines

### 2. Pre-commit Hooks
Install git-secrets or similar tools:
```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
sudo apt-get install git-secrets  # Linux

# Setup for repository
cd /home/kostiantyn/projects/graintrade-info
git secrets --install
git secrets --register-aws
```

### 3. Regular Security Audits
- Rotate credentials every 90 days
- Use unique credentials for each environment (dev/staging/prod)
- Implement credential complexity requirements
- Enable 2FA/MFA on all service accounts

### 4. Access Control
- Limit production credential access to essential personnel
- Use separate credentials for different team members
- Implement audit logging for credential access

## Checklist

- [ ] PostgreSQL password rotated
- [ ] RabbitMQ credentials rotated
- [ ] Redis password rotated
- [ ] JWT secret regenerated
- [ ] FONDY API keys rotated
- [ ] LiqPay keys rotated
- [ ] NOWPayments keys rotated
- [ ] Mailtrap passwords regenerated
- [ ] Telegram bot token regenerated
- [ ] Recovery secret regenerated
- [ ] All `.env.prod` files updated on production servers
- [ ] All services restarted
- [ ] Suspicious activity monitoring enabled
- [ ] Team notified about required actions
- [ ] Incident documented

## Support Resources

- **GitHub Security:** https://docs.github.com/en/code-security
- **How To Rotate:** https://howtorotate.com/
- **OWASP Secrets Management:** https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

## Contact

For questions or assistance with this security incident, contact your security team or DevOps lead.

---
**Last Updated:** November 15, 2025  
**Document Status:** Active Incident Response
