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

##   Docker compose using
- Devlopment:
```
docker compose -f docker-compose.dev.yml up -d
```
- Production:
```
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
I'll help you create separate Docker Compose files for production and development environments. I notice some security concerns in the current file and will suggest improvements.

1. First, let's create a base Docker Compose file that will contain common configurations:

````yaml
# Base configuration
name: graintraide
services:
  db:
    image: postgis/postgis:latest
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  pgadmin4:
    image: elestio/pgadmin:latest
    restart: always
    ports:
      - "5050:8080"
    volumes:
      - postgis:/var/lib/pgadmin4/servers.json
    depends_on:
      db:
        condition: service_healthy

  rabbitmq:
    image: rabbitmq:3-management
    restart: always
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - rabbitmq_config:/etc/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmqctl", "status"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7.4-alpine
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

volumes:
  postgres_data:
  postgis:
  rabbitmq_data:
  rabbitmq_config:
  redis_data:
````

2. Create a development-specific compose file:

````yaml
name: graintraide-dev
services:
  db:
    extends:
      file: docker-compose.yml
      service: db
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: dev_password
    ports:
      - '5432:5432'

  pgadmin4:
    extends:
      file: docker-compose.yml
      service: pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: dev@example.com
      PGADMIN_DEFAULT_PASSWORD: dev_password
      PGADMIN_LISTEN_PORT: 8080

  rabbitmq:
    extends:
      file: docker-compose.yml
      service: rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: dev_user
      RABBITMQ_DEFAULT_PASS: dev_password

  redis:
    extends:
      file: docker-compose.yml
      service: redis
    ports:
      - "6379:6379"

  backend:
    build: 
      context: ./backend
      target: development
    volumes:
      - ./backend:/backend
      - /backend/node_modules
    environment:
      NODE_ENV: development
      DEBUG: 'true'
    ports:
      - "8000:8000"
    command: npm run dev

  notifications:
    build:
      context: ./notifications
      target: development
    volumes:
      - ./notifications:/notifications
      - /notifications/node_modules
    environment:
      NODE_ENV: development
      DEBUG: 'true'
    ports:
      - "8001:8000"
    command: npm run dev

  frontend:
    build:
      context: ./frontend
      target: development
    volumes:
      - ./frontend:/frontend
      - /frontend/node_modules
    environment:
      NODE_ENV: development
    ports:
      - "3000:3000"
    command: npm run dev
````

3. Create a production-specific compose file:

````yaml
name: graintraide-prod
services:
  db:
    extends:
      file: docker-compose.yml
      service: db
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - '5432:5432'

  pgadmin4:
    extends:
      file: docker-compose.yml
      service: pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_LISTEN_PORT: 8080

  rabbitmq:
    extends:
      file: docker-compose.yml
      service: rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}

  redis:
    extends:
      file: docker-compose.yml
      service: redis
    ports:
      - "6379:6379"

  backend:
    build: 
      context: ./backend
      target: production
    restart: always
    environment:
      NODE_ENV: production
    ports:
      - "8000:8000"

  notifications:
    build:
      context: ./notifications
      target: production
    restart: always
    environment:
      NODE_ENV: production
    ports:
      - "8001:8000"

  frontend:
    build:
      context: ./frontend
      target: production
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./frontend/dist:/var/www/frontend/dist:ro
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - backend
      - frontend
````

4. Create an .env file for production secrets:

````plaintext
POSTGRES_DB=postgres
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password_here
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=secure_password_here
RABBITMQ_USER=rabbit_user
RABBITMQ_PASSWORD=secure_password_here
````

To use these files:

- Development:
```bash
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d
```

- Production:
```bash
docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d
```

Key improvements:
- Separated development and production configurations
- Removed hardcoded credentials
- Added environment variables for sensitive data
- Added development-specific volumes for hot reloading
- Improved security for production setup
- Added proper targeting for build stages
- Added SSL support in production nginx

Remember to:
1. Add .env to .gitignore
2. Create proper .env file for production
3. Set up SSL certificates for production
4. Use secrets management in production
5. Configure proper logging in production
6. Set up monitoring for production services

Create `.env` file for production secrets:
```
POSTGRES_DB=postgres
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password_here
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=secure_password_here
RABBITMQ_USER=rabbit_user
RABBITMQ_PASSWORD=secure_password_here
```

Runthe following command to obtain the initial SSL certificates usig Certbot:
```
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d yourdomain.com -d www.yourdomain.com
```
After obtaining the certificates , restart `ngnx` serice toapply the SSL configuration:
```
docker-compose up -d nginx
```

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
git clone https://github.com/youruser/agrimarket.git
cd agrimarket
```
or from local machine:
```
rsync -avz --exclude '__pycache__' --exclude '*.pyc' ./graintrade-info/ kivaschenko@65.108.68.57:/home/kivaschenko/graintrade-info
```

### 5. Create `.env` file (example):

```env
BACKEND_TAG=latest
FRONTEND_TAG=latest
NOTIFY_TAG=latest
```

### 6. Start services:

```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

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