#!/bin/bash

# Apache deployment script for Graintrade production routing and security.
# It installs/enables required Apache components, deploys vhost configs,
# enables core production sites, validates Apache config, and reloads service.

set -euo pipefail

echo "🔐 Deploying Apache production routing/security for Graintrade..."

if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
APACHE_SITES_SRC="$SCRIPT_DIR/apache_files/sites-available"
APACHE_SITES_DST="/etc/apache2/sites-available"
APACHE_CONF_DST="/etc/apache2/conf-available"

REQUIRED_SITE_FILES=(
    "graintrade.info-le-ssl.conf"
    "api.graintrade.info.conf"
    "chat.graintrade.info.conf"
    "data-pipeline.graintrade.info.conf"
    "home.graintrade.info.conf"
)

REQUIRED_CERT_FILES=(
    "/etc/letsencrypt/live/graintrade.info/fullchain.pem"
    "/etc/letsencrypt/live/graintrade.info/privkey.pem"
    "/etc/letsencrypt/live/api.graintrade.info/fullchain.pem"
    "/etc/letsencrypt/live/api.graintrade.info/privkey.pem"
    "/etc/letsencrypt/live/chat.graintrade.info/fullchain.pem"
    "/etc/letsencrypt/live/chat.graintrade.info/privkey.pem"
    "/etc/letsencrypt/live/data-pipeline.graintrade.info/fullchain.pem"
    "/etc/letsencrypt/live/data-pipeline.graintrade.info/privkey.pem"
    "/etc/letsencrypt/live/home.graintrade.info/fullchain.pem"
    "/etc/letsencrypt/live/home.graintrade.info/privkey.pem"
)

ALL_COPY_FILES=(
    "api.graintrade.info.conf"
    "api.graintrade.info-simple.conf"
    "chat.graintrade.info.conf"
    "data-pipeline.graintrade.info.conf"
    "graintrade.info-le-ssl.conf"
    "home.graintrade.info.conf"
    "pgadmin.graintrade.info.conf"
    "airflow.graintrade.info.conf"
    "minio.graintrade.info.conf"
    "security.conf"
)

echo "📁 Working directory: $SCRIPT_DIR"
echo "📁 Apache site source directory: $APACHE_SITES_SRC"

for file in "${REQUIRED_SITE_FILES[@]}"; do
    if [[ ! -f "$APACHE_SITES_SRC/$file" ]]; then
        echo "❌ Required site file missing: $APACHE_SITES_SRC/$file"
        exit 1
    fi
done

missing_certs=0
for cert_file in "${REQUIRED_CERT_FILES[@]}"; do
    if [[ ! -f "$cert_file" ]]; then
        missing_certs=1
        break
    fi
done

echo "📦 Installing Apache dependencies..."
apt-get update
apt-get install -y apache2 certbot python3-certbot-apache libapache2-mod-evasive

echo "🔧 Enabling Apache modules..."
MODULES=(ssl rewrite headers proxy proxy_http proxy_wstunnel expires deflate evasive)
for mod in "${MODULES[@]}"; do
    a2enmod "$mod" >/dev/null
done

echo "📁 Preparing mod_evasive and rate-limit files..."
mkdir -p /var/log/apache2/evasive
chown www-data:www-data /var/log/apache2/evasive
touch /etc/apache2/rate_limit.txt
chown www-data:www-data /etc/apache2/rate_limit.txt

echo "📋 Copying Apache site files..."
for config_file in "${ALL_COPY_FILES[@]}"; do
    if [[ -f "$APACHE_SITES_SRC/$config_file" ]]; then
        cp "$APACHE_SITES_SRC/$config_file" "$APACHE_SITES_DST/$config_file"
    fi
done

if [[ -f "$APACHE_SITES_SRC/global-security.conf" ]]; then
    echo "🛡️  Installing global security conf..."
    cp "$APACHE_SITES_SRC/global-security.conf" "$APACHE_CONF_DST/global-security.conf"
    a2enconf global-security >/dev/null
fi

if [[ "$missing_certs" -eq 1 ]]; then
    BOOTSTRAP_SITE="$APACHE_SITES_DST/graintrade-bootstrap-http.conf"
    echo "⚠️  SSL certificates are missing. Entering bootstrap HTTP mode."
    cat > "$BOOTSTRAP_SITE" <<'EOF'
<VirtualHost *:80>
    ServerName graintrade.info
    ServerAlias www.graintrade.info api.graintrade.info chat.graintrade.info data-pipeline.graintrade.info home.graintrade.info faq.graintrade.info
    DocumentRoot /var/www/html
    <Directory /var/www/html>
        Require all granted
    </Directory>
</VirtualHost>
EOF

    a2ensite graintrade-bootstrap-http.conf >/dev/null
    for site_file in "${REQUIRED_SITE_FILES[@]}"; do
        a2dissite "$site_file" >/dev/null || true
    done
else
    echo "🌐 Enabling core production vhosts..."
    for site_file in "${REQUIRED_SITE_FILES[@]}"; do
        a2ensite "$site_file" >/dev/null
    done
    a2dissite graintrade-bootstrap-http.conf >/dev/null || true
    rm -f "$APACHE_SITES_DST/graintrade-bootstrap-http.conf"
fi

echo "🧹 Disabling default Apache site (if enabled)..."
a2dissite 000-default.conf >/dev/null || true

echo "🧪 Validating Apache configuration..."
if ! apache2ctl configtest; then
    echo ""
    echo "❌ Apache config validation failed."
    echo "Hint: SSL certificate file paths in enabled vhosts must exist."
    echo "Run certbot for missing domains, then re-run this script."
    exit 1
fi

echo "🔄 Reloading Apache..."
systemctl reload apache2
systemctl --no-pager --full status apache2 | sed -n '1,20p'

if [[ "$missing_certs" -eq 1 ]]; then
    echo ""
    echo "✅ Apache HTTP bootstrap is active on port 80."
    echo "Now issue certificates, then re-run this script:"
    echo "  certbot --apache -d graintrade.info -d www.graintrade.info"
    echo "  certbot --apache -d api.graintrade.info"
    echo "  certbot --apache -d chat.graintrade.info"
    echo "  certbot --apache -d data-pipeline.graintrade.info"
    echo "  certbot --apache -d home.graintrade.info -d faq.graintrade.info"
    exit 0
fi

echo ""
echo "✅ Apache deployment completed."
echo ""
echo "Enabled core routes:"
echo "  - graintrade.info        -> frontend:8080"
echo "  - api.graintrade.info    -> backend:8000"
echo "  - chat.graintrade.info   -> chat-room:8001"
echo "  - data-pipeline.graintrade.info -> data-pipeline:8004"
echo "  - home.graintrade.info   -> landing-service:8003"
echo ""
echo "Notes:"
echo "  - notifications service remains internal on host port 8002."
echo "  - If SSL certs are not issued yet, run certbot and re-run this script."