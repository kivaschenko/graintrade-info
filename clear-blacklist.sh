#!/bin/bash

# Clear mod_evasive blacklist and update configuration
# This script helps remove your IP from the blacklist and apply new settings

echo "🔧 Clearing mod_evasive blacklist and updating configuration..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)" 
   exit 1
fi

USER_IP="188.163.31.56"

echo "🧹 Clearing mod_evasive blacklist for IP: $USER_IP"

# Step 1: Clear the mod_evasive blacklist
echo "📝 Clearing mod_evasive temporary files..."
if [ -d "/var/log/apache2/evasive" ]; then
    # Remove any IP-specific blacklist files
    find /var/log/apache2/evasive -name "*$USER_IP*" -delete 2>/dev/null
    find /var/log/apache2/evasive -type f -delete 2>/dev/null
    echo "✅ Cleared evasive blacklist files"
else
    echo "⚠️  Evasive log directory not found"
fi

# Step 2: Check if we have updated configuration files
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SECURITY_CONF="$SCRIPT_DIR/apache_files/sites-available/security.conf"

if [ -f "$SECURITY_CONF" ]; then
    echo "📋 Updating security configuration with new settings..."
    
    # Copy the updated security.conf
    cp "$SECURITY_CONF" /etc/apache2/sites-available/security.conf
    
    # Check if API configuration exists and update it
    if [ -f "$SCRIPT_DIR/apache_files/sites-available/api.graintrade.info-simple.conf" ]; then
        echo "📋 Updating API configuration..."
        cp "$SCRIPT_DIR/apache_files/sites-available/api.graintrade.info-simple.conf" /etc/apache2/sites-available/api.graintrade.info.conf
    fi
    
    echo "✅ Configuration files updated"
else
    echo "❌ Security configuration file not found at $SECURITY_CONF"
    exit 1
fi

# Step 3: Test the configuration
echo "🧪 Testing Apache configuration..."
if apache2ctl configtest; then
    echo "✅ Apache configuration test passed!"
    
    # Step 4: Reload Apache
    echo "🔄 Reloading Apache..."
    systemctl reload apache2
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Successfully updated configuration and cleared blacklist!"
        echo ""
        echo "📊 New mod_evasive settings:"
        echo "  ✓ Page requests: 5 per 2 seconds (was 3 per 1 second)"
        echo "  ✓ Site requests: 100 per 2 seconds (was 50 per 1 second)"
        echo "  ✓ Block duration: 60 seconds (was 300 seconds)"
        echo "  ✓ Your IP ($USER_IP) is whitelisted"
        echo ""
        echo "💡 These settings are more permissive for legitimate users"
        echo "💡 Monitor with: ./security-monitor.sh"
        echo ""
        echo "🔍 Check if you're still being blocked:"
        echo "  tail -f /var/log/apache2/evasive/ (if any files appear)"
        echo "  journalctl -f | grep mod_evasive"
        
    else
        echo "❌ Failed to reload Apache!"
        exit 1
    fi
else
    echo "❌ Apache configuration test failed!"
    apache2ctl configtest
    exit 1
fi