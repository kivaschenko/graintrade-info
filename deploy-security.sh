#!/bin/bash

# Security Enhancement Deployment Script for Graintrade API (Fedora 44)
# This script deploys Apache/httpd security configs on Fedora-family systems.

set -euo pipefail

echo "Deploying Apache security enhancements for Graintrade on Fedora..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (use sudo)."
    exit 1
fi

# Fedora-only guard
if [[ ! -f /etc/fedora-release ]]; then
    echo "ERROR: This script is adapted for Fedora. Detected non-Fedora OS."
    exit 1
fi

# Paths and service names for Fedora
APACHE_SERVICE="httpd"
APACHE_CONF_DIR="/etc/httpd"
APACHE_CONFD_DIR="${APACHE_CONF_DIR}/conf.d"
APACHE_CONF_MAIN="${APACHE_CONF_DIR}/conf/httpd.conf"
APACHE_USER="apache"
EVASIVE_LOG_DIR="/var/log/httpd/evasive"
RATE_LIMIT_FILE="${APACHE_CONF_DIR}/rate_limit.txt"
COMPAT_CONF_FILE="${APACHE_CONFD_DIR}/00-graintrade-compat.conf"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
APACHE_FILES_DIR="$SCRIPT_DIR/apache_files/sites-available"

echo "Working directory: $SCRIPT_DIR"
echo "Apache files directory: $APACHE_FILES_DIR"

# Check required source files
if [[ ! -f "$APACHE_FILES_DIR/api.graintrade.info.conf" ]]; then
    echo "ERROR: Source file not found: $APACHE_FILES_DIR/api.graintrade.info.conf"
    exit 1
fi

if [[ ! -f "$APACHE_FILES_DIR/security.conf" ]]; then
    echo "ERROR: Source file not found: $APACHE_FILES_DIR/security.conf"
    exit 1
fi

# 1. Install required packages
echo "Installing Apache packages and modules with dnf..."
dnf -y install httpd mod_ssl mod_evasive

# 2. Ensure service is enabled
echo "Enabling and starting httpd service..."
systemctl enable --now "$APACHE_SERVICE"

# 3. Create mod_evasive log directory and rate-limit file
echo "Preparing mod_evasive log directory and rate-limit file..."
mkdir -p "$EVASIVE_LOG_DIR"
chown "$APACHE_USER":"$APACHE_USER" "$EVASIVE_LOG_DIR"
chmod 750 "$EVASIVE_LOG_DIR"

touch "$RATE_LIMIT_FILE"
chown "$APACHE_USER":"$APACHE_USER" "$RATE_LIMIT_FILE"
chmod 640 "$RATE_LIMIT_FILE"

# 4. Copy configuration files to conf.d
echo "Deploying virtual host and security config files..."
install -m 644 "$APACHE_FILES_DIR/api.graintrade.info.conf" "$APACHE_CONFD_DIR/"
install -m 644 "$APACHE_FILES_DIR/security.conf" "$APACHE_CONFD_DIR/"

if [[ -f "$APACHE_FILES_DIR/global-security.conf" ]]; then
    install -m 644 "$APACHE_FILES_DIR/global-security.conf" "$APACHE_CONFD_DIR/00-global-security.conf"
    echo "Global security configuration deployed to $APACHE_CONFD_DIR/00-global-security.conf"
fi

# Copy other site configurations if they exist
for config_file in \
    graintrade.info-le-ssl.conf \
    chat.graintrade.info.conf \
    home.graintrade.info.conf \
    pgadmin.graintrade.info.conf \
    data-pipeline.graintrade.info.conf \
    airflow.graintrade.info.conf \
    minio.graintrade.info.conf
do
    if [[ -f "$APACHE_FILES_DIR/$config_file" ]]; then
        echo "Deploying $config_file..."
        install -m 644 "$APACHE_FILES_DIR/$config_file" "$APACHE_CONFD_DIR/$config_file"
    fi
done

# 5. Align Debian-style path references inside security.conf to Fedora paths
if [[ -f "$APACHE_CONFD_DIR/security.conf" ]]; then
    sed -i 's#/var/log/apache2/evasive#/var/log/httpd/evasive#g' "$APACHE_CONFD_DIR/security.conf"
fi

# 5b. Compatibility defines for configs authored for Debian-style Apache layout
cat > "$COMPAT_CONF_FILE" <<'EOF'
# Compatibility definitions for cross-distro vhost configs
Define APACHE_LOG_DIR /var/log/httpd
EOF

# 6. SELinux and firewall adjustments for reverse-proxy use case
echo "Applying SELinux and firewall settings..."
if command -v setsebool >/dev/null 2>&1; then
    setsebool -P httpd_can_network_connect 1 || true
fi

if command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-service=http || true
    firewall-cmd --permanent --add-service=https || true
    firewall-cmd --reload || true
fi

# 7. Validate httpd configuration
echo "Testing Apache/httpd configuration..."
if ! httpd -t; then
    echo "ERROR: httpd configuration test failed."
    exit 1
fi

# 8. Reload service
echo "Reloading httpd..."
systemctl reload "$APACHE_SERVICE"

echo "Security enhancements deployed successfully."
echo ""
echo "Enabled/checked:"
echo "  - Apache/httpd service: $APACHE_SERVICE"
echo "  - Main config: $APACHE_CONF_MAIN"
echo "  - Config include dir: $APACHE_CONFD_DIR"
echo "  - mod_evasive log dir: $EVASIVE_LOG_DIR"
echo "  - Rate limit file: $RATE_LIMIT_FILE"
echo ""
echo "Logs:"
echo "  - Access log: /var/log/httpd/access_log"
echo "  - Error log: /var/log/httpd/error_log"
echo "  - mod_evasive: $EVASIVE_LOG_DIR"
echo ""
echo "Next checks:"
echo "  - systemctl status httpd --no-pager"
echo "  - httpd -M | grep -E 'rewrite|headers|ssl|evasive'"