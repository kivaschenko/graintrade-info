#!/bin/bash

# Simple Apache Configuration Syntax Checker
# This script checks the syntax of our configuration files without deploying them

echo "🔍 Checking Apache Configuration Syntax..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APACHE_FILES_DIR="$SCRIPT_DIR/apache_files/sites-available"

echo "📁 Checking files in: $APACHE_FILES_DIR"

# Function to check a single config file
check_config_file() {
    local config_file="$1"
    local filename=$(basename "$config_file")
    
    echo "🔍 Checking $filename..."
    
    # Create a temporary Apache config for testing
    cat > /tmp/test_apache.conf << EOF
# Minimal Apache configuration for syntax testing
ServerRoot /etc/apache2
PidFile /var/run/apache2/apache2.pid
Timeout 300
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5

# Load essential modules
LoadModule mpm_prefork_module /usr/lib/apache2/modules/mod_mpm_prefork.so
LoadModule authz_core_module /usr/lib/apache2/modules/mod_authz_core.so
LoadModule dir_module /usr/lib/apache2/modules/mod_dir.so
LoadModule mime_module /usr/lib/apache2/modules/mod_mime.so
LoadModule rewrite_module /usr/lib/apache2/modules/mod_rewrite.so
LoadModule ssl_module /usr/lib/apache2/modules/mod_ssl.so
LoadModule headers_module /usr/lib/apache2/modules/mod_headers.so
LoadModule proxy_module /usr/lib/apache2/modules/mod_proxy.so
LoadModule proxy_http_module /usr/lib/apache2/modules/mod_proxy_http.so
LoadModule alias_module /usr/lib/apache2/modules/mod_alias.so
LoadModule authz_host_module /usr/lib/apache2/modules/mod_authz_host.so

# Define variables
Define APACHE_LOG_DIR /var/log/apache2

# Include our config file
Include $config_file
EOF

    # Test the configuration
    if apache2 -t -f /tmp/test_apache.conf 2>/dev/null; then
        echo "  ✅ $filename syntax is OK"
        return 0
    else
        echo "  ❌ $filename has syntax errors:"
        apache2 -t -f /tmp/test_apache.conf 2>&1 | grep -v "AH00558" | head -5
        return 1
    fi
}

# Check all configuration files
error_count=0

for config_file in "$APACHE_FILES_DIR"/*.conf; do
    if [ -f "$config_file" ]; then
        if ! check_config_file "$config_file"; then
            ((error_count++))
        fi
    fi
done

# Clean up
rm -f /tmp/test_apache.conf

echo ""
if [ $error_count -eq 0 ]; then
    echo "✅ All configuration files passed syntax check!"
    echo "📝 Ready for deployment with: sudo ./deploy-security.sh"
else
    echo "❌ Found $error_count configuration file(s) with syntax errors"
    echo "🔧 Please fix the errors before deployment"
    exit 1
fi