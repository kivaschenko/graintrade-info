# Environment Files Security Guide

## ⚠️ IMPORTANT: Never Commit Sensitive Environment Files

This guide explains how to properly manage environment variables and configuration files in this project.

## File Naming Convention

- **`.env.example`** or **`.env.prod.example`** - Template files with placeholder values (SAFE to commit)
- **`.env`**, **`.env.prod`**, **`.env.production`** - Actual files with real credentials (NEVER commit)

## Quick Start

### For Development

1. Copy the example file:
   ```bash
   cp backend/.env.example backend/.env
   # or for production template:
   cp backend/.env.prod.example backend/.env.prod
   ```

2. Fill in the actual values in your local `.env` file

3. Never commit the `.env` file - it's already in `.gitignore`

### For Production Deployment

Production credentials should be managed through:
- Environment variables in your hosting platform
- Secret management services (HashiCorp Vault, AWS Secrets Manager, etc.)
- Secure configuration management tools
- Docker secrets for containerized deployments

## Current Status

The following template files are available:

```
backend/.env.prod.example          # Backend service configuration template
notifications/.env.prod.example    # Notifications service configuration template
chat-room/.env.prod.example        # Chat room service configuration template
parsers/.env.example               # Parser service configuration template
```

## What's Protected

The `.gitignore` file already includes:
```
.env
.env.prod
.env.production
.envprod
.env.local
.env.*.local
```

## Adding New Services

When creating a new service that needs environment configuration:

1. Create a `.env.example` file with placeholder values
2. Add documentation about required variables
3. Commit the `.env.example` file
4. Add the actual `.env` file to `.gitignore` (if not already covered)

Example `.env.example`:
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database

# API Keys
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here

# Feature Flags
ENABLE_FEATURE_X=true
```

## Best Practices

1. **Use Strong, Unique Credentials**
   - Generate random passwords: `openssl rand -base64 32`
   - Generate secrets: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

2. **Separate Environments**
   - Use different credentials for dev, staging, and production
   - Never use production credentials in development

3. **Regular Rotation**
   - Rotate credentials every 90 days
   - Immediately rotate if exposed

4. **Access Control**
   - Limit who has access to production credentials
   - Use role-based access control
   - Enable audit logging

5. **Validation**
   - Validate environment variables on application startup
   - Fail fast if required variables are missing
   - Use type checking for environment variables

## Security Incident Response

If credentials are accidentally committed:

1. **Immediately rotate all exposed credentials**
2. Follow the guide in `SECURITY_INCIDENT_CREDENTIAL_ROTATION.md`
3. Remove the file from git tracking: `git rm --cached path/to/.env`
4. Consider cleaning git history (see security incident guide)
5. Monitor for suspicious activity

## Git Hooks (Optional)

To prevent accidentally committing sensitive files, you can set up pre-commit hooks:

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
sudo apt-get install git-secrets  # Linux

# Setup for this repository
cd /home/kostiantyn/projects/graintrade-info
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add '\.env$'
git secrets --add '\.env\.prod$'
git secrets --add 'password.*=.*'
git secrets --add 'secret.*=.*'
```

## Checklist Before Committing

- [ ] No `.env` files included
- [ ] Only `.env.example` files with placeholders
- [ ] No passwords or secrets in code
- [ ] No API keys in comments
- [ ] No hardcoded credentials
- [ ] All sensitive values use environment variables

## Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub - Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [How To Rotate Credentials](https://howtorotate.com/docs/introduction/getting-started/)

## Support

For questions about environment configuration or security concerns, contact your team lead or security team.

---
**Last Updated:** November 15, 2025
