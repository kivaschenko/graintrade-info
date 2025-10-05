#!/bin/bash

# Security Enhancement Deployment Script for Graintrade API
# This script helps deploy the security configurations

echo "🔐 Deploying Apache Security Enhancements for Graintrade API..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)" 
   exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APACHE_FILES_DIR="$SCRIPT_DIR/apache_files/sites-available"

echo "📁 Working directory: $SCRIPT_DIR"
echo "📁 Apache files directory: $APACHE_FILES_DIR"

# Check if source files exist
if [ ! -f "$APACHE_FILES_DIR/api.graintrade.info.conf" ]; then
    echo "❌ Source file not found: $APACHE_FILES_DIR/api.graintrade.info.conf"
    exit 1
fi

if [ ! -f "$APACHE_FILES_DIR/security.conf" ]; then
    echo "❌ Source file not found: $APACHE_FILES_DIR/security.conf"
    exit 1
fi

# 1. Install required Apache modules
echo "📦 Installing required Apache modules..."
apt-get update
apt-get install -y libapache2-mod-evasive

# Enable modules (don't fail if already enabled)
echo "🔧 Enabling Apache modules..."
a2enmod ssl || echo "⚠️  mod_ssl already enabled or failed to enable"
a2enmod evasive || echo "⚠️  mod_evasive already enabled or failed to enable"
a2enmod headers || echo "⚠️  mod_headers already enabled or failed to enable"
a2enmod rewrite || echo "⚠️  mod_rewrite already enabled or failed to enable"

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
cp "$APACHE_FILES_DIR/api.graintrade.info.conf" /etc/apache2/sites-available/ || {
    echo "❌ Failed to copy api.graintrade.info.conf"
    exit 1
}

cp "$APACHE_FILES_DIR/security.conf" /etc/apache2/sites-available/ || {
    echo "❌ Failed to copy security.conf"
    exit 1
}

# Copy global security configuration
if [ -f "$APACHE_FILES_DIR/global-security.conf" ]; then
    cp "$APACHE_FILES_DIR/global-security.conf" /etc/apache2/conf-available/
    a2enconf global-security
    echo "✅ Global security configuration enabled"
fi

# Copy other site configurations if they exist
for config_file in graintrade.info-le-ssl.conf chat.graintrade.info.conf home.graintrade.info.conf pgadmin.graintrade.info.conf; do
    if [ -f "$APACHE_FILES_DIR/$config_file" ]; then
        echo "📋 Copying $config_file..."
        cp "$APACHE_FILES_DIR/$config_file" /etc/apache2/sites-available/
    fi
done

# 5. Test Apache configuration
echo "🧪 Testing Apache configuration..."
apache2ctl configtest

if [ $? -eq 0 ]; then
    echo "✅ Apache configuration test passed!"
    
    # 6. Reload Apache
    echo "🔄 Reloading Apache..."
    systemctl reload apache2
    
    if [ $? -eq 0 ]; then
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
        echo "❌ Failed to reload Apache!"
        exit 1
    fi
    
else
    echo "❌ Apache configuration test failed!"
    echo "📋 Showing Apache error details:"
    apache2ctl configtest 2>&1
    echo ""
    echo "Please check the configuration and fix any errors before reloading."
    exit 1
fi