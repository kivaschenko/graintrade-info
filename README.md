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

- Production:
```
docker compose -f docker-compose.yml -f docker-compose.yml up -d
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