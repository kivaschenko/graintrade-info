# Gitea + Jenkins CI/CD Roadmap

This directory holds everything that is needed to run the self-hosted developer platform (Gitea + Jenkins) on the Hetzner AX-41 production node. It operationalizes the approach described in [Jenkins_and_Gitea_on_Hetzner_server_suggestment.md](Jenkins_and_Gitea_on_Hetzner_server_suggestment.md) and replaces the older "Jenkins on laptop + Docker Hub" flow described in [docs/CI_CD.md](../docs/CI_CD.md).

## 1. What lives here
- `docker-compose.yaml` &rarr; container stack for Gitea + Postgres.
- `Jenkinsfile` &rarr; production pipeline that builds and pushes all microservice images on every run, using one shared immutable tag.
- This README &rarr; end-to-end setup + operations checklist for the AX-41 host.

## 2. Target architecture
```
┌──────────────────────────────────────────┐
│ Hetzner AX-41 (Ubuntu 22.04 / Docker)    │
│                                          │
│  Gitea (git remote, web UI)              │
│  Jenkins (Pipeline + Docker socket)      │
│  docker compose stack for microservices  │
│                                          │
│ git push → Gitea webhook → Jenkins build │
│ → build/push all images with same TAG    │
│ → docker compose pull/up in production   │
└──────────────────────────────────────────┘
```
- Registry-based deploy: Jenkins pushes images to `gitea.graintrade.info/kivaschenko/*`.
- One pipeline run = one TAG (Git commit SHA) for all services.
- Runtime secrets stay on the production host in `./envs/*.env` next to `docker-compose.prod.yaml`.

## 3. Prerequisites
1. **Server**: Hetzner AX-41 (or similar) running Ubuntu 22.04 LTS, public DNS entry for `gitea.graintrade.info`.
2. **Packages**:
   ```bash
   sudo apt update && sudo apt install -y ca-certificates curl gnupg ufw
   ```
3. **Docker + Compose plugin**:
   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER
   sudo apt install -y docker-compose-plugin
   docker --version && docker compose version
   ```
4. **Firewall** (open HTTPS + Jenkins UI):
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 8888/tcp   # restricted to admin IPs if possible
   sudo ufw enable
   ```
5. **TLS / reverse proxy**: terminate TLS with your preferred reverse proxy (Apache, Nginx, Traefik, Caddy, etc.). The sample compose file exposes Gitea only on 127.0.0.1:6543 so that the proxy handles public traffic. If you use Apache, reuse the vhost definition in `apache_files/sites-available/gitea.graintrade.info.conf`, which already proxies HTTPS traffic on port 443 to `http://localhost:6543/` and redirects HTTP to HTTPS.

## 4. Bring up Gitea
1. Copy `gitea/docker-compose.yaml` to `/opt/gitea/docker-compose.yaml` (or keep it inside this repo clone).
2. Update the file:
   - Replace every `temp12345` with a strong secret.
   - Set `GITEA__server__DOMAIN` and `ROOT_URL` to match your DNS name.
   - (Optional) Mount `/etc/letsencrypt` into a reverse proxy container if you keep SSL termination inside the compose stack.
3. Start the stack:
   ```bash
   cd /path/to/graintrade-info/gitea
   docker compose up -d
   docker compose ps
   ```
4. Point your reverse proxy at `http://127.0.0.1:6543` and complete the browser-based Gitea installer (Postgres host is `db:5432`).
5. Create:
   - Admin user.
   - Organization/repository `graintrade-info`.
   - Deploy keys or a PAT (Settings → Applications) for Jenkins.

## 5. Install Jenkins on the same host
Run Jenkins as a container so it shares the host Docker/Compose binaries:
```bash
docker network create cicd || true
docker volume create jenkins_home

docker run -d -p 8888:8080 --name jenkins -v jenkins_home:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock jenkins/jenkins:lts
```
Then:
1. Unlock Jenkins using the password from `docker logs jenkins`.
2. Install plugins: **Git**, **Gitea**, **Pipeline**, **Docker**, **SSH Agent**.
3. Add credentials required by the pipeline:
   - `gitea-registry-creds` (Username/Password): registry user and token/password for `gitea.graintrade.info`.
   - `frontend-env-production` (Secret text): full content for `frontend/.env.production`.
   - `prod-ssh-key` (SSH Username with private key): deployment SSH key.
   - `prod-host` (Secret text): production host or IP.
   - `prod-port` (Secret text): SSH port (usually `22`).

## 6. Prepare the working copy + secrets
1. Create Jenkins credentials used by `gitea/Jenkinsfile`:
   - `gitea-registry-creds` (Username/Password) for Gitea registry login.
   - `frontend-env-production` (Secret text) containing the full content of `frontend/.env.production`.
   - `prod-ssh-key` (SSH Username with private key) for production SSH.
   - `prod-host` (Secret text) for the production hostname/IP.
   - `prod-port` (Secret text) for SSH port (usually `22`).
2. Keep runtime service env files on the production host, not in git:
   - `production/envs/backend.env`
   - `production/envs/chat-room.env`
   - `production/envs/notifications.env`
   - `production/envs/data-pipeline.env`
3. Restrict permissions on production env files:
   - directory: `chmod 700 production/envs`
   - files: `chmod 600 production/envs/*.env`

## 7. Configure the Jenkins job
Use one of these two supported setups depending on your Jenkins UI.

1. Recommended: Multibranch Pipeline
   - Create a new item of type Multibranch Pipeline named graintrade-prod.
   - In Branch Sources, add your Gitea repository URL and credentials.
   - In Build Configuration, set mode to by Jenkinsfile.
   - Set Script Path to gitea/Jenkinsfile.
   - Enable webhook trigger from Gitea and optionally keep periodic scan as fallback.

2. Alternative: Single Pipeline Job
   - Create a new item of type Pipeline named graintrade-prod.
   - In the job configuration, open the Pipeline section near the bottom.
   - In Definition, choose Pipeline script from SCM.
   - Set SCM to Git, configure repo URL/credentials, branch main, and Script Path gitea/Jenkinsfile.

3. If Pipeline script from SCM is missing in your Pipeline job
   - Install or enable these plugins: Pipeline, Pipeline: Groovy, Pipeline: Job, Git.
   - Restart Jenkins after plugin install and reopen the job config.

4. Concurrency and deploy behavior
   - The Jenkinsfile already has disableConcurrentBuilds() and full deploy logic with one shared tag.

## 8. Wire Gitea → Jenkins webhooks
1. In Gitea repo settings, add a Jenkins webhook.
2. URL: https://jenkins.example.com/gitea-webhook/post
3. Content type: application/json
4. Trigger: push events
5. For Multibranch, ensure repository indexing or webhook trigger is enabled.
6. For single Pipeline job, ensure the Gitea webhook trigger is enabled in the job.

## 9. Pipeline behavior (gitea/Jenkinsfile)
- **Checkout**: pulls the commit received from Gitea.
- **Generate deploy tag**: computes one immutable `DEPLOY_TAG` from `git rev-parse HEAD`.
- **Prepare frontend build env**: writes `frontend/.env.production` from Jenkins secret `frontend-env-production`.
- **Build and push all services**: always builds/pushes backend, frontend, chat-room, notifications, data-pipeline, and landing-service using the same tag.
- **Deploy on production host**: over SSH, runs:
   ```bash
   TAG=<DEPLOY_TAG> docker compose -f docker-compose.prod.yaml pull
   TAG=<DEPLOY_TAG> docker compose -f docker-compose.prod.yaml up -d
   ```
- **Result**: all running services are aligned to the same image tag from the same commit.

## 10. Operations checklist
- **Manual full redeploy on server**:
   - `cd /home/kivaschenko/production`
   - `TAG=<commit_sha> docker compose -f docker-compose.prod.yaml pull`
   - `TAG=<commit_sha> docker compose -f docker-compose.prod.yaml up -d`
- **Status**:
   - `docker compose -f docker-compose.prod.yaml ps`
   - `docker logs --tail 100 <container>`
- **Backups**:
  - Gitea data volume: `docker run --rm -v gitea-data:/data -v $(pwd):/backup alpine tar czf /backup/gitea-data.tgz /data`.
  - Jenkins home: `docker run --rm -v jenkins_home:/var/jenkins_home -v $(pwd):/backup alpine tar czf /backup/jenkins-home.tgz /var/jenkins_home`.
- **Updates**:
  - `docker compose pull && docker compose up -d gitea db` for the SCM stack.
  - `docker pull jenkins/jenkins:lts-jdk17 && docker restart jenkins`.
- **Monitoring**: reuse the existing Prometheus/Grafana stack (`docker-compose.yaml` already exposes exporters).

## 11. Security hardening tips
- Immediately change every default password in `gitea/docker-compose.yaml` before the first boot.
- Restrict Jenkins (port 8888) to VPN/admin IPs.
- Store PATs/SSH keys inside Jenkins Credentials, not in plaintext files.
- Enable 2FA for Gitea admin accounts.
- Schedule automatic backups of both Docker volumes.

## 12. Troubleshooting quick wins
| Symptom | Checks |
| ------- | ------ |
| Jenkins cannot talk to Docker | `docker info` inside the Jenkins container, ensure `/var/run/docker.sock` is mounted and permissions allow uid 1000 to use it. |
| Pipeline fails on frontend env stage | Verify Jenkins credential `frontend-env-production` exists and contains valid `.env.production` content. |
| Deploy uses old images | Confirm production command uses `TAG=<commit_sha>` and that the same tag exists in registry for all services. |
| SSH deploy fails | Check `prod-ssh-key`, `prod-host`, `prod-port` credentials and firewall rules for SSH access. |
| Webhook not firing | Check Gitea webhook delivery log and Jenkins system log (Manage Jenkins → System Log → All). |

With this setup you now have a self-hosted CI/CD loop: push to Gitea, Jenkins builds/pushes all microservice images with one shared tag, and production is redeployed to that exact tag set.
