# 🌾 AgriMarket Startup – Fullstack Deployment Guide

This project is a modern fullstack MVP platform for Ukrainian farmers to buy/sell grain, seeds, fertilizer, diesel, etc.  
It includes:

- FastAPI (Backend)
- Vue.js (Frontend)
- Redis, RabbitMQ, PostgreSQL (Infrastructure)
- CI/CD via Jenkins, Docker Hub, and Docker Compose on remote server

---

## 📦 Tech Stack

- **Backend**: FastAPI + PostgreSQL + Redis + RabbitMQ
- **Frontend**: Vue 3 + Vite + WebSocket
- **Messaging**: RabbitMQ (event-driven architecture)
- **CI/CD**: Jenkins (local) → Docker Hub → Remote Deploy


---

## 🚀 Setup: Remote Server

### 1. Provision server (Hetzner recommended: [AX41-NVMe](https://www.hetzner.com/dedicated-rootserver/ax41-nvme))

### 2. Install essentials:

```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose ufw fail2ban git curl
systemctl enable docker
```

### 3. Secure the server:

```bash
ufw allow OpenSSH
ufw allow 80,443,5432,5672,15672/tcp
ufw enable
```

Enable Fail2Ban:

```bash
systemctl enable fail2ban
systemctl start fail2ban
```

### 4. Clone project:

```bash
# on server side
git clone https://github.com/kivaschenko/graintrade-info
cd graintrade-info
```
or from local machine:
```bash
# on local side
rsync -avz --exclude '__pycache__/' --exclude '*.pyc' --exclude 'venv/' --exclude 'frontend/node_modules/' --delete-excluded ./graintrade-info kivaschenko@65.108.68.57:/home/kivaschenko

ssh kivaschenko@65.108.68.57
# on server side
cd graintrade-info
```

### 5. Update `.env` files (example):
For each of backend microservices exchange development `.env` with `.env.prod` production file:
```bash
# Go to main backend microservice
cd backend
mv .env .env.local
mv .env.prod .env

# Go to next microservice for chats handling
cd ../chat-rooms
mv .env .env.local
mv .env.prod .env

# Go to notifications microservice
cd ../notifications
mv .env .env.local
mv .env.prod .env

```

### 6. Start backend services:

```bash
# In /graintrade-info directory run the dockers using by default docker-compose.yaml
docker-compose --build --no-cache
docker-compose up -d
# Check dockers if all ran good
docker ps
docker compose logs
```

### 7. Create and run frontend app
Firstly build the production Vue app:
```bash
# Build the production version of Vue app
# In /graintrade-info directory
cd frontend
npm run build
```
Then copy the app to certain web directory:
```bash
sudo cp -r dist/* /var/www/graintrade.info/
```
---
## Let's Encrypt SSL
Here’s the **step-by-step guide to set up Let’s Encrypt SSL from scratch on Apache for your Vue app**:

---

### ✅ 1. **Install Certbot & Apache Plugin**

On Ubuntu:

```bash
sudo apt update
sudo apt install certbot python3-certbot-apache -y
```

---

### ✅ 2. **Check Apache Virtual Hosts**

Make sure you have a proper **Apache site config** for your domain (not the default one). For example:

`/etc/apache2/sites-available/graintrade.info.conf`:

```apache
<VirtualHost *:80>
    ServerName graintrade.info
    ServerAlias www.graintrade.info
    DocumentRoot /var/www/graintrade.info/dist

    <Directory /var/www/graintrade.info/dist>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/graintrade_error.log
    CustomLog ${APACHE_LOG_DIR}/graintrade_access.log combined
</VirtualHost>
```

Enable it and disable defaults:

```bash
sudo a2ensite graintrade.info.conf
sudo a2dissite 000-default.conf
sudo systemctl reload apache2
```

---

### ✅ 3. **Open Ports in Firewall**

Make sure **80 and 443 are open**:

```bash
sudo ufw allow 'Apache Full'
```

---

### ✅ 4. **Obtain SSL Certificate**

Run Certbot to automatically configure SSL:

```bash
sudo certbot --apache -d graintrade.info -d www.graintrade.info
```

This will:
✔ Validate your domain
✔ Install SSL certificates
✔ Update your Apache config
✔ Reload Apache

---

### ✅ 5. **Auto-Renew Certificates**

Certbot installs a cron job by default. You can test renewal manually:

```bash
sudo certbot renew --dry-run
```

---

### ✅ 6. **Verify SSL**

Open:

```
https://graintrade.info
```

or check via:

```bash
openssl s_client -connect graintrade.info:443
```

---

### ✅ 7. **Optional: Redirect HTTP → HTTPS**

Certbot usually adds this, but if not, add to your port 80 VirtualHost:

```apache
<VirtualHost *:80>
    ServerName graintrade.info
    Redirect permanent / https://graintrade.info/
</VirtualHost>
```

---

✅ After this, your site will be **served over HTTPS with Let’s Encrypt SSL**.

---

## Settings of Apache2 server

Right now Apache is using `000-default-le-ssl.conf` because Let's Encrypt likely enabled SSL automatically. To serve your **Vue app** from `/var/www/graintrade.info/` instead of the temporary index.html, you need to:

---

### ✅ 1. Update your `graintrade.info.conf`

Edit `/etc/apache2/sites-available/graintrade.info.conf` to point to your Vue build folder:

```apache
<VirtualHost *:80>
    ServerName graintrade.info
    ServerAlias www.graintrade.info

    DocumentRoot /var/www/graintrade.info/dist
    <Directory /var/www/graintrade.info/dist>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/graintrade_error.log
    CustomLog ${APACHE_LOG_DIR}/graintrade_access.log combined
</VirtualHost>
```

---

### ✅ 2. Add SSL for this site

Edit (or create) `/etc/apache2/sites-available/graintrade.info-le-ssl.conf`:

```apache
<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName graintrade.info
    ServerAlias www.graintrade.info

    DocumentRoot /var/www/graintrade.info/dist
    <Directory /var/www/graintrade.info/dist>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/graintrade.info/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/graintrade.info/privkey.pem

    ErrorLog ${APACHE_LOG_DIR}/graintrade_ssl_error.log
    CustomLog ${APACHE_LOG_DIR}/graintrade_ssl_access.log combined
</VirtualHost>
</IfModule>
```

---

### ✅ 3. Enable the site and disable the old one

Run:

```bash
sudo a2dissite 000-default-le-ssl.conf
sudo a2dissite 000-default.conf
sudo a2ensite graintrade.info.conf
sudo a2ensite graintrade.info-le-ssl.conf
sudo systemctl reload apache2
```

---

### ✅ 4. Ensure Rewrite works for Vue Router (SPA)

If you use Vue Router in **history mode**, add this to the SSL and non-SSL `<VirtualHost>` sections:

```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteRule ^index\.html$ - [L]
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule . /index.html [L]
</IfModule>
```

Make sure `mod_rewrite` is enabled:

```bash
sudo a2enmod rewrite
sudo systemctl reload apache2
```

---

✅ After this, your Vue app will be served from **/var/www/graintrade.info/dist** on both `http://graintrade.info` and `https://graintrade.info`.

---

👉 Do you want me to give you a **full Apache config template for Vue SPA + API proxy (backend on FastAPI)** so that `https://graintrade.info/api/` points to your backend? Or keep API on subdomain (`api.graintrade.info`)?

---

## 💻 CI/CD Setup with Jenkins (Local Dev Machine)

### 1. Run Jenkins in Docker:

```bash
docker run -d --name jenkins \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

### 2. Open Jenkins

Go to [http://localhost:8080](http://localhost:8080)  
Unlock Jenkins (password from `docker logs jenkins`)

Get admin password:
```
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```
Paste password into browser → click Continue

### 3. Install required plugins:

- Docker
- Docker Pipeline
- Git
- Pipeline
- SSH Agent
- Slack Notification (optional)

### 4. Add Credentials

- Docker Hub:
  - Type: Username/Password
  - ID: `dockerhub-credentials`
- SSH Key for remote deploy:
  - Type: SSH Username with private key
  - ID: `your-ssh-key-id`

---

## 🐳 Docker Image Build and Push

Each push builds and pushes tagged Docker images:

- `backend` → `yourdockerhubuser/backend:<git-sha>`
- `frontend` → `yourdockerhubuser/frontend:<git-sha>`
- `notifications` → `yourdockerhubuser/notifications:<git-sha>`

---

## 🔧 Jenkinsfile Example (Pipeline as Code)

```groovy
pipeline {
  agent any
  environment {
    DOCKERHUB_CREDENTIALS = 'dockerhub-credentials'
    DOCKERHUB_NAMESPACE = 'yourdockerhubuser'
    COMMIT_HASH = "${GIT_COMMIT[0..7]}"
  }

  stages {
    stage('Checkout') {
      steps { git branch: 'main', url: 'https://github.com/youruser/agrimarket.git' }
    }

    stage('Build') {
      steps {
        script {
          docker.build('backend', './backend')
          docker.build('frontend', './frontend')
          docker.build('notifications', './notifications')
        }
      }
    }

    stage('Push') {
      steps {
        script {
          docker.withRegistry('https://index.docker.io/v1/', DOCKERHUB_CREDENTIALS) {
            docker.image('backend').push("${COMMIT_HASH}")
            docker.image('frontend').push("${COMMIT_HASH}")
            docker.image('notifications').push("${COMMIT_HASH}")
          }
        }
      }
    }

    stage('Deploy to Remote') {
      steps {
        sshagent(credentials: ['your-ssh-key-id']) {
          sh """
          ssh user@your.remote.server '
            cd /home/youruser/agrimarket &&
            echo "BACKEND_TAG=${COMMIT_HASH}" > .env &&
            echo "FRONTEND_TAG=${COMMIT_HASH}" >> .env &&
            echo "NOTIFY_TAG=${COMMIT_HASH}" >> .env &&
            docker-compose pull &&
            docker-compose up -d
          '
          """
        }
      }
    }

    stage('Notify') {
      steps {
        slackSend(channel: '#deployments', color: 'good', message: "✅ Deploy: ${COMMIT_HASH} complete!")
      }
    }
  }

  post {
    failure {
      slackSend(channel: '#deployments', color: 'danger', message: "❌ Deploy failed")
    }
  }
}
```
---
## Save copy to remote USB drive
To copy files to a USB drive using `rsync`, you can follow these steps. Make sure your USB drive is connected to your computer and properly mounted.

### Step 1: Identify the USB Drive

First, you need to find out where your USB drive is mounted. You can do this by running the following command in the terminal:

```bash
df -h
```

Look for your USB drive in the output. It will typically be listed under `/media/username/` or `/mnt/`.

### Step 2: Use `rsync` to Copy Files

Once you know the mount point of your USB drive, you can use the `rsync` command to copy files. The basic syntax is:

```bash
rsync -av /path/to/source/ /path/to/usb/
```

- `-a`: Archive mode; it preserves permissions, timestamps, symbolic links, etc.
- `-v`: Verbose; it provides detailed output of the transfer process.

### Example Command

If your USB drive is mounted at `/media/username/USB_DRIVE` and you want to copy files from a folder called `Documents`, the command would look like this:

```bash
rsync -av ~/Documents/ /media/username/USB_DRIVE/
```

### Step 3: Eject the USB Drive

After the copying process is complete, make sure to safely eject the USB drive to avoid data corruption:

```bash
umount /media/username/USB_DRIVE
```

### Additional Options

- If you want to exclude certain files or directories, you can use the `--exclude` option:

```bash
rsync -av --exclude='*.tmp' ~/Documents/ /media/username/USB_DRIVE/
```

- To perform a dry run (to see what would be copied without actually copying), add the `-n` option:

```bash
rsync -avn ~/Documents/ /media/username/USB_DRIVE/
```

---

## 🛡 Monitoring & Backup (Optional)

- Use **UptimeRobot** or **HetrixTools** for basic uptime checks.
- Add cronjob:
```bash
0 3 * * * docker exec postgres pg_dump -U user db > /backups/db_$(date +\%F).sql
```
- Store backups in **Hetzner Storage Box**, S3 or Dropbox.

---

## 📈 Scaling later?

- Move Redis/RabbitMQ to separate VPS
- Deploy backend with multiple replicas (Docker Swarm/K8s)
- Use Cloudflare + CDN for frontend
- Add PostgreSQL read replica (pgpool)

---

## 📬 Contact / License

MIT License © 2024  
Project by [yourname or startup]