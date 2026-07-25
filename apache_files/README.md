# Apache2 Production Deployment for Graintrade

This guide explains how to deploy all core Graintrade microservices and the landing page on a production server using Docker Compose and Apache2 reverse proxy.

## Scope

This runbook covers:

- Frontend SPA
- Backend API
- Chat service (including WebSocket)
- Notifications service
- Data pipeline API
- Landing pages service

## Service Routing Matrix

| Public Domain | Apache Config | Upstream Service | Host Port |
|---|---|---|---|
| graintrade.info, www.graintrade.info | graintrade.info-le-ssl.conf | frontend | 8080 |
| api.graintrade.info | api.graintrade.info.conf | backend | 8000 |
| chat.graintrade.info | chat.graintrade.info.conf | chat-room | 8001 |
| data-pipeline.graintrade.info | data-pipeline.graintrade.info.conf | data-pipeline | 8004 |
| home.graintrade.info, faq.graintrade.info | home.graintrade.info.conf | landing-service | 8003 |

Notes:

- notifications currently has no dedicated public Apache vhost in this repository.
- notifications runs on host port 8002 and is expected to be consumed by internal services.

Optional admin sites in this folder:

- pgadmin.graintrade.info -> localhost:8081
- airflow.graintrade.info -> localhost:8080
- minio.graintrade.info -> localhost:9001

## Prerequisites

1. Ubuntu 20.04/22.04+ production server with sudo access.
2. DNS A records for all required domains pointing to the server.
3. Docker Engine + Docker Compose plugin installed.
4. Ports open in firewall/security group:
    - 22/tcp
    - 80/tcp
    - 443/tcp
5. Repository checked out on server.

## 1. Start All Microservices

From repository root:

```bash
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d backend chat-room notifications data-pipeline frontend landing-service
docker compose -f docker-compose.prod.yaml ps
```

Quick local health checks:

```bash
curl -f http://127.0.0.1:8000/health
curl -f http://127.0.0.1:8001/health
curl -f http://127.0.0.1:8002/health
curl -f http://127.0.0.1:8003/health
curl -f http://127.0.0.1:8004/health
curl -I http://127.0.0.1:8080
```

## 2. Install Apache2 and Required Modules

```bash
sudo apt-get update
sudo apt-get install -y apache2 certbot python3-certbot-apache libapache2-mod-evasive

sudo a2enmod ssl rewrite headers proxy proxy_http proxy_wstunnel expires deflate
sudo a2enmod evasive
```

If you use shared hardening rules from this directory, install and enable them as Apache conf:

```bash
sudo cp apache_files/sites-available/global-security.conf /etc/apache2/conf-available/global-security.conf
sudo a2enconf global-security
```

## 3. Deploy Apache Virtual Hosts

Copy configs from this repository:

```bash
sudo cp apache_files/sites-available/*.conf /etc/apache2/sites-available/
```

Enable required production sites:

```bash
sudo a2ensite graintrade.info-le-ssl.conf
sudo a2ensite api.graintrade.info.conf
sudo a2ensite chat.graintrade.info.conf
sudo a2ensite data-pipeline.graintrade.info.conf
sudo a2ensite home.graintrade.info.conf
```

Disable default site if still enabled:

```bash
sudo a2dissite 000-default.conf || true
```

## 4. Issue and Attach SSL Certificates

Run Certbot for each public hostname:

```bash
sudo certbot --apache -d graintrade.info -d www.graintrade.info
sudo certbot --apache -d api.graintrade.info
sudo certbot --apache -d chat.graintrade.info
sudo certbot --apache -d data-pipeline.graintrade.info
sudo certbot --apache -d home.graintrade.info -d faq.graintrade.info
```

Validate renewal timer:

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

## 5. Validate Apache Configuration and Reload

```bash
sudo apache2ctl configtest
sudo systemctl reload apache2
sudo systemctl status apache2 --no-pager
```

## 6. End-to-End Smoke Test

```bash
curl -I https://graintrade.info
curl -f https://api.graintrade.info/health
curl -f https://chat.graintrade.info/health
curl -f https://data-pipeline.graintrade.info/health
curl -f https://home.graintrade.info/health
```

Notifications check (internal service):

```bash
curl -f http://127.0.0.1:8002/health
docker compose -f docker-compose.prod.yaml logs --tail=100 notifications
```

For WebSocket validation on chat, connect with your client to:

- wss://chat.graintrade.info/ws/

## Landing Page Notes

The landing Apache vhost serves static files directly (alias /static) and proxies dynamic routes to landing-service on port 8003.

If static files must be exported to host:

```bash
sudo mkdir -p /var/www/html/landing
docker cp $(docker compose -f docker-compose.prod.yaml ps -q landing-service):/app/static /tmp/landing-static
sudo rsync -a /tmp/landing-static/ /var/www/html/landing/static/
sudo chown -R www-data:www-data /var/www/html/landing
```

## Security and Monitoring

Use the bundled monitor script:

```bash
./security-monitor.sh
./security-monitor.sh blocked
./security-monitor.sh attackers
./security-monitor.sh patterns
./security-monitor.sh evasive
./security-monitor.sh realtime
```

Useful logs:

- /var/log/apache2/error.log
- /var/log/apache2/access.log
- /var/log/apache2/chat_error.log
- /var/log/apache2/home.graintrade.info_error.log

## Troubleshooting

1. 502/503 from domain: container not healthy or wrong upstream port in vhost.
2. SSL errors: DNS not propagated or missing certificate files in /etc/letsencrypt/live.
3. WebSocket fails on chat: ensure proxy_wstunnel is enabled and chat service is on port 8001.
4. Landing static 404: verify /var/www/html/landing/static exists and Apache can read it.
5. Notifications errors: verify envs/notifications.env values and backend->notifications connectivity on port 8002.

## One-Command Security Baseline

If you only need to re-apply security-related Apache settings (not full deployment), you can still use:

```bash
sudo ./deploy-security.sh
```

---

Last Updated: 2026-07-25
Version: 2.0
Tested On: Ubuntu 22.04 with Apache 2.4