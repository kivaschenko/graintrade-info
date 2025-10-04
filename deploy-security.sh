#!/bin/bash

# Security Enhancement Deployment Script for Graintrade API
# This script helps deploy the security configurations

echo "🔐 Deploying Apache Security Enhancements for Graintrade API..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)" 
   exit 1
fi

# 1. Install required Apache modules
echo "📦 Installing required Apache modules..."
apt-get update
apt-get install -y libapache2-mod-evasive libapache2-mod-security2

# Enable modules
a2enmod evasive
a2enmod security2
a2enmod headers
a2enmod rewrite

# 2. Create rate limiting directory for mod_evasive
echo "📁 Creating mod_evasive log directory..."
mkdir -p /var/log/apache2/evasive
chown www-data:www-data /var/log/apache2/evasive

# 3. Create rate limit file for basic rewrite rules
echo "📝 Creating rate limit tracking file..."
touch /etc/apache2/rate_limit.txt
chown www-data:www-data /etc/apache2/rate_limit.txt

# 4. Copy configuration files
echo "📋 Copying configuration files..."
cp /home/kostiantyn/projects/graintrade-info/apache_files/sites-available/api.graintrade.info.conf /etc/apache2/sites-available/
cp /home/kostiantyn/projects/graintrade-info/apache_files/sites-available/security.conf /etc/apache2/sites-available/

# 5. Test Apache configuration
echo "🧪 Testing Apache configuration..."
apache2ctl configtest

if [ $? -eq 0 ]; then
    echo "✅ Apache configuration test passed!"
    
    # 6. Reload Apache
    echo "🔄 Reloading Apache..."
    systemctl reload apache2
    
    echo "✅ Security enhancements deployed successfully!"
    echo ""
    echo "📊 Security features enabled:"
    echo "  ✓ Block malicious file requests (.env, .git, wp-admin, etc.)"
    echo "  ✓ Block WordPress vulnerability scans"
    echo "  ✓ Block router/CGI exploitation attempts"
    echo "  ✓ Block Microsoft Exchange attacks"
    echo "  ✓ Block advertising file requests"
    echo "  ✓ Block suspicious user agents"
    echo "  ✓ Rate limiting with mod_evasive"
    echo "  ✓ Security headers"
    echo "  ✓ Custom error pages"
    echo ""
    echo "📝 Monitor logs at:"
    echo "  - Apache access log: /var/log/apache2/access.log"
    echo "  - Apache error log: /var/log/apache2/error.log"
    echo "  - mod_evasive log: /var/log/apache2/evasive/"
    echo ""
    echo "🔧 To add more blocked IPs, edit:"
    echo "  /etc/apache2/sites-available/security.conf"
    
else
    echo "❌ Apache configuration test failed!"
    echo "Please check the configuration and fix any errors before reloading."
    exit 1
fi