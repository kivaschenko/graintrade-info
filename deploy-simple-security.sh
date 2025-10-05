#!/bin/bash

# Simple Security Deployment Script for Graintrade API
# This script deploys a simplified but effective security configuration

echo "🔐 Deploying Simple Apache Security for Graintrade API..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)" 
   exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APACHE_FILES_DIR="$SCRIPT_DIR/apache_files/sites-available"

echo "📁 Working from: $SCRIPT_DIR"

# Check if source file exists
if [ ! -f "$APACHE_FILES_DIR/api.graintrade.info-simple.conf" ]; then
    echo "❌ Source file not found: $APACHE_FILES_DIR/api.graintrade.info-simple.conf"
    exit 1
fi

# 1. Enable required Apache modules
echo "🔧 Enabling Apache modules..."
a2enmod ssl || echo "⚠️  mod_ssl already enabled"
a2enmod headers || echo "⚠️  mod_headers already enabled"
a2enmod rewrite || echo "⚠️  mod_rewrite already enabled"
a2enmod proxy || echo "⚠️  mod_proxy already enabled"
a2enmod proxy_http || echo "⚠️  mod_proxy_http already enabled"

# 2. Install mod_evasive if available
echo "📦 Installing mod_evasive (optional)..."
apt-get update
if apt-get install -y libapache2-mod-evasive; then
    a2enmod evasive || echo "⚠️  mod_evasive failed to enable"
    
    # Create evasive log directory
    mkdir -p /var/log/apache2/evasive
    chown www-data:www-data /var/log/apache2/evasive
    
    echo "✅ mod_evasive installed and configured"
else
    echo "⚠️  mod_evasive not available, continuing without it"
fi

# 3. Backup existing configuration if it exists
if [ -f "/etc/apache2/sites-available/api.graintrade.info.conf" ]; then
    echo "💾 Backing up existing configuration..."
    cp "/etc/apache2/sites-available/api.graintrade.info.conf" "/etc/apache2/sites-available/api.graintrade.info.conf.backup.$(date +%Y%m%d-%H%M%S)"
fi

# 4. Copy new configuration
echo "📋 Installing new security configuration..."
cp "$APACHE_FILES_DIR/api.graintrade.info-simple.conf" "/etc/apache2/sites-available/api.graintrade.info.conf"

# 5. Test Apache configuration
echo "🧪 Testing Apache configuration..."
if apache2ctl configtest; then
    echo "✅ Apache configuration test passed!"
    
    # 6. Enable the site and reload Apache
    echo "🔄 Enabling site and reloading Apache..."
    a2ensite api.graintrade.info.conf
    systemctl reload apache2
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Security deployment completed successfully!"
        echo ""
        echo "🛡️  Security features now active:"
        echo "  ✓ Block .env and .git access"
        echo "  ✓ Block WordPress vulnerability scans"
        echo "  ✓ Block CGI/admin/phpmyadmin access"
        echo "  ✓ Block Exchange/OWA attacks"
        echo "  ✓ Block advertising file requests"
        echo "  ✓ Block suspicious file extensions"
        echo "  ✓ Block random path probing"
        echo "  ✓ Block empty user agents"
        echo "  ✓ Block common attack tools"
        echo "  ✓ Security headers enabled"
        echo "  ✓ Server information hidden"
        echo ""
        echo "📊 Monitor the results:"
        echo "  tail -f /var/log/apache2/access.log | grep 403"
        echo "  ./security-monitor.sh"
        echo ""
        echo "🔧 To add real SSL certificates later:"
        echo "  Edit /etc/apache2/sites-available/api.graintrade.info.conf"
        echo "  Uncomment the real SSL lines and comment out the snakeoil lines"
        
    else
        echo "❌ Failed to reload Apache!"
        exit 1
    fi
    
else
    echo "❌ Apache configuration test failed!"
    echo ""
    echo "📋 Error details:"
    apache2ctl configtest
    echo ""
    echo "Please check the configuration and try again."
    exit 1
fi