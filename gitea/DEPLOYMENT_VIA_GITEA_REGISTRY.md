This document summarizes the complete process of transitioning from `rsync` to a versioned Docker registry workflow using your own Gitea instance on the Hetzner AX41-NVMe.

# Guide: Gitea Container Registry & Docker Production Workflow

This guide covers the infrastructure tuning, Gitea setup, and Jenkins integration required to deploy versioned images.

---

## 1. Infrastructure Tuning (Hetzner/Ubuntu)

Because Docker pushes involve rapid-fire requests, you must whitelist your server IP in your Apache security modules to prevent `403 Forbidden` errors.

### A. Apache mod_evasive Configuration
Edit `/etc/apache2/mods-enabled/evasive.conf`:
```apache
<IfModule mod_evasive20.c>
    DOSHashTableSize    3097
    DOSPageCount        5
    DOSSiteCount        50
    DOSPageInterval     1
    DOSSiteInterval     1
    DOSBlockingPeriod   10

    # Whitelist your server and local loopback
    DOSWhitelist        127.0.0.1
    DOSWhitelist        65.108.142.153  # Your Hetzner IP
</IfModule>
```

### B. Apache Virtual Host for Gitea
Ensure your SSL VirtualHost (`/etc/apache2/sites-available/gitea.conf`) handles encoded slashes and protocol headers correctly:
```apache
AllowEncodedSlashes NoDecode

<VirtualHost *:443>
    ServerName gitea.graintrade.info

    RequestHeader set X-Forwarded-Proto "https"
    ProxyPreserveHost On
    ProxyPass / http://localhost:3000/ nocanon
    ProxyPassReverse / http://localhost:3000/

    # SSL Certs (Managed by Certbot)
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/gitea.graintrade.info/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/gitea.graintrade.info/privkey.pem
</VirtualHost>
```
*Restart services: `sudo systemctl restart apache2`*

---

## 2. Gitea Server Configuration

Edit your Gitea `app.ini` (usually in `/data/gitea/conf/app.ini`) to enable the registry and fix domain mismatches.

```ini
[server]
DOMAIN = gitea.graintrade.info
ROOT_URL = https://gitea.graintrade.info/

[packages]
ENABLED = true

[repository]
ENABLE_PUSH_CREATE_USER = true
```
*Restart Gitea: `docker restart gitea`*

---

## 3. Production Deployment Files

### A. Refactored `docker-compose.yaml`
Remove `build:` and `volumes:` (source code mounts). Use versioned images.

```yaml
services:
  backend:
    image: gitea.graintrade.info/kivaschenko/grain-backend:${TAG:-latest}
    restart: always
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    networks:
      - grain-network

  chat-room:
    image: gitea.graintrade.info/kivaschenko/grain-chat-room:${TAG:-latest}
    restart: always
    env_file:
      - ./chat-room/.env
    ports:
      - "8001:8001"
    networks:
      - grain-network
```

---

## 4. CI/CD Workflow (Jenkins)

### A. Authentication
1. Generate an **App Token** in Gitea (**Settings > Applications**) with `package:write` scope.
2. In Jenkins, add a credential of type **Username with Password**:
   - **ID**: `gitea-token-creds`
   - **Username**: `kivaschenko`
   - **Password**: Your Gitea App Token.

### B. Jenkinsfile Logic
```groovy
pipeline {
    agent any
    environment {
        REGISTRY = 'gitea.graintrade.info'
        OWNER = 'kivaschenko'
        TAG = "${env.GIT_COMMIT.take(7)}"
        PROD_DIR = "/home/admin/graintrade" 
    }
    stages {
        stage('Build & Push') {
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", 'gitea-token-creds') {
                        def backend = docker.build("${REGISTRY}/${OWNER}/grain-backend:${TAG}", "./backend")
                        backend.push()
                        
                        def chat = docker.build("${REGISTRY}/${OWNER}/grain-chat-room:${TAG}", "./chat-room")
                        chat.push()
                    }
                }
            }
        }
        stage('Deploy') {
            steps {
                sh "cd ${PROD_DIR} && TAG=${TAG} docker compose pull && TAG=${TAG} docker compose up -d --remove-orphans"
            }
        }
    }
}
```

---

## 5. Critical Constraints & Rules

1.  **Image Naming**: Gitea registry only supports two levels: `domain/owner/image-name`. **Do not** use sub-folders like `owner/project/image`.
2.  **Immutability**: Always use the Git SHA (`TAG`) for production. Avoid relying on `latest` to ensure you can roll back instantly.
3.  **Cleanup**: Images consume NVMe space. Run `docker image prune -f` in your Jenkins `post` block to remove old build layers.