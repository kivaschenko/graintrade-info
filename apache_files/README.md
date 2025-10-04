# Apache Security Configuration for Graintrade

This directory contains Apache security configurations to protect your Graintrade application from common web attacks and malicious crawlers.

## 🔐 Security Features Implemented

### 1. **Malicious Request Blocking**
- Blocks access to sensitive files (`.env`, `.git`, etc.)
- Prevents WordPress vulnerability scans
- Blocks router/CGI exploitation attempts
- Prevents Microsoft Exchange/OWA attacks
- Blocks advertising file requests (`ads.txt`, `sellers.json`)

### 2. **User Agent Filtering**
Blocks requests from:
- Empty user agents
- Common attack tools (curl, wget, python scripts)
- Security scanners (nikto, sqlmap, nmap)
- Suspicious libraries (libwww, urllib, requests)

### 3. **Rate Limiting**
- Basic rate limiting using mod_rewrite
- Advanced rate limiting with mod_evasive (recommended)
- Configurable thresholds for requests per minute

### 4. **Security Headers**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` for HTTPS

### 5. **IP-based Blocking**
- Manual IP blocking for persistent attackers
- Whitelist for internal networks

## 📁 Files Structure

```
apache_files/sites-available/
├── api.graintrade.info.conf     # API server configuration with security
├── graintrade.info-le-ssl.conf  # Main site configuration with security
├── security.conf                # Shared security configurations
├── chat.graintrade.info.conf    # Chat server configuration
├── home.graintrade.info.conf    # Home server configuration
└── pgadmin.graintrade.info.conf # PgAdmin configuration
```

## 🚀 Deployment Instructions

### 1. **Quick Deployment**
```bash
sudo ./deploy-security.sh
```

### 2. **Manual Deployment**

1. Install required Apache modules:
```bash
sudo apt-get update
sudo apt-get install libapache2-mod-evasive libapache2-mod-security2
sudo a2enmod evasive security2 headers rewrite
```

2. Copy configuration files:
```bash
sudo cp apache_files/sites-available/*.conf /etc/apache2/sites-available/
```

3. Test configuration:
```bash
sudo apache2ctl configtest
```

4. Reload Apache:
```bash
sudo systemctl reload apache2
```

## 📊 Monitoring

### Security Monitoring Script
Use the provided monitoring script to track security events:

```bash
# View summary of all security events
./security-monitor.sh

# View recent blocked requests
./security-monitor.sh blocked

# View top attacking IPs
./security-monitor.sh attackers

# View common attack patterns
./security-monitor.sh patterns

# View mod_evasive blocks
./security-monitor.sh evasive

# Real-time monitoring
./security-monitor.sh realtime
```

### Log Locations
- Apache access log: `/var/log/apache2/access.log`
- Apache error log: `/var/log/apache2/error.log`
- mod_evasive blocks: `/var/log/apache2/evasive/`

## 🔧 Configuration Customization

### Adding More Blocked IPs
Edit `/etc/apache2/sites-available/security.conf`:
```apache
<RequireAll>
    Require all granted
    Require not ip 147.185.132.183
    Require not ip NEW_SUSPICIOUS_IP
</RequireAll>
```

### Adjusting Rate Limits
Edit mod_evasive settings in `security.conf`:
```apache
DOSPageCount        2     # Requests per page
DOSPageInterval     1     # Time interval (seconds)
DOSSiteCount        50    # Total site requests
DOSSiteInterval     1     # Site interval (seconds)
DOSBlockingPeriod   600   # Block duration (seconds)
```

### Whitelist Legitimate Bots
To allow specific user agents, add exceptions before the blocking rules:
```apache
# Allow legitimate bots
RewriteCond %{HTTP_USER_AGENT} (Googlebot|Bingbot) [NC]
RewriteRule ^.*$ - [L]

# Then add the blocking rules...
```

## 🎯 Attack Types Blocked

Based on your logs, these configurations block:

1. **Environment File Access**: `/.env`
2. **WordPress Scans**: 
   - `/wp-includes/wlwmanifest.xml`
   - `/xmlrpc.php`
   - `/wp-admin/`, `/wp-content/`, etc.
3. **Git Repository Access**: `/.git/HEAD`
4. **Router Exploits**: `/cgi-bin/luci/`
5. **Exchange Server Attacks**: `/owa/auth/logon.aspx`
6. **SEO File Scans**: `/ads.txt`, `/sellers.json`
7. **Random Path Probing**: `/aaa9`, `/aab9`

## 📈 Expected Results

After deployment, you should see:
- Significantly reduced backend 404 errors
- Faster response times (fewer requests reaching backend)
- Detailed logs of blocked attacks
- Better server performance

## ⚠️ Important Notes

1. **Test First**: Always test configurations on staging before production
2. **Monitor Logs**: Watch for false positives blocking legitimate traffic
3. **Regular Updates**: Update IP blacklists and patterns regularly
4. **Backup Configs**: Keep backups of working configurations

## 🆘 Troubleshooting

### If Legitimate Traffic is Blocked
1. Check Apache error logs for specific blocking rules
2. Add whitelist entries for legitimate IPs/user agents
3. Adjust rate limiting thresholds

### If Configuration Test Fails
1. Check syntax in Apache config files
2. Ensure all required modules are enabled
3. Verify file paths in Include directives

### Performance Issues
1. Monitor server resources with new rules
2. Adjust rate limiting settings if needed
3. Consider hardware upgrades for high-traffic sites

## 📞 Support

For issues or questions:
1. Check Apache error logs: `sudo tail -f /var/log/apache2/error.log`
2. Test configuration: `sudo apache2ctl configtest`
3. Monitor security events: `./security-monitor.sh`

---

**Last Updated**: October 2025  
**Version**: 1.0  
**Tested On**: Ubuntu 20.04/22.04 with Apache 2.4