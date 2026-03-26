# Gitea + Jenkins CI/CD Roadmap

This directory holds everything that is needed to run the self-hosted developer platform (Gitea + Jenkins) on the Hetzner AX-41 production node. It operationalizes the approach described in [Jenkins_and_Gitea_on_Hetzner_server_suggestment.md](Jenkins_and_Gitea_on_Hetzner_server_suggestment.md) and replaces the older "Jenkins on laptop + Docker Hub" flow described in [docs/CI_CD.md](../docs/CI_CD.md).

## 1. What lives here
- `docker-compose.yaml` &rarr; container stack for Gitea + Postgres.
- `Jenkinsfile` &rarr; opinionated pipeline that selectively rebuilds Docker services defined in the root `docker-compose.yaml`.
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
│ → docker compose build/up (selective)    │
└──────────────────────────────────────────┘
```
- No external registry: images are built locally and containers are restarted in place.
- Secrets (.env files) stay on the server; only source code is pulled from Gitea.
- Jenkins decides which services to rebuild by diffing the latest commit against its parent.

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
3. Add credentials:
   - `gitea-token`: Gitea PAT with repo:read scope.
   - `hetzner-ssh`: SSH key Jenkins can use to administer the host (optional but handy for future automation).

## 6. Prepare the working copy + secrets
1. Jenkins clones the repo into `/var/lib/jenkins/workspace/<job>/` automatically. After the first successful checkout, place production `.env` files alongside each service:
   ```bash
   sudo -u jenkins cp backend/sample_env /var/lib/jenkins/workspace/grain/docker/backend/.env
   # repeat for chat-room/.env, notifications/.env, frontend/.env.production, landing-service/.env, etc.
   ```
2. Remove write access for other users: `chmod 600 backend/.env`.
3. Keep these files out of git; Jenkins will reuse them every time it runs `docker compose`.

## 7. Configure the Jenkins job
1. Create a new **Pipeline** job named `graintrade-prod`.
2. Under **Pipeline → Definition**, choose "Pipeline script from SCM".
3. SCM settings:
   - Git / SSH URL from Gitea (`git@gitea.graintrade.info:org/graintrade-info.git`).
   - Credentials: `gitea-token` (or an SSH key pair).
   - Branch: `main`.
   - Script Path: `gitea/Jenkinsfile`.
4. Enable triggers:
   - Check "Build when a change is pushed to Gitea".
   - (Optional) Poll SCM every hour as a fallback.
5. Restrict concurrency: the Jenkinsfile already contains `disableConcurrentBuilds()`.

## 8. Wire Gitea → Jenkins webhooks
1. In Gitea repo → Settings → Webhooks → Add Webhook → Jenkins.
2. URL: `https://jenkins.example.com/gitea-webhook/post` (adjust protocol/hostname).
3. Content type: `application/json`.
4. Trigger: "Just the push event".
5. Jenkins job → Configure → Build Triggers → check "Gitea web hook".

## 9. Pipeline behavior (gitea/Jenkinsfile)
- **Checkout**: pulls the commit received from Gitea.
- **Select services**: runs `git diff HEAD^ HEAD` (falls back to `git show` for the first commit) and maps touched files to compose services using `serviceCatalog`.
- **Global triggers**: any change to `docker-compose.yaml`, helper scripts, or other shared infra files rebuilds every service.
- **Compose build & deploy**: for each selected service it executes:
  ```bash
  docker compose -f docker-compose.yaml build --pull <service>
  docker compose -f docker-compose.yaml up -d <service>
  docker compose -f docker-compose.yaml ps <service>
  ```
- **Health checks**: backend, chat-room, notifications, and landing-service are pinged on `http://127.0.0.1:<port>/health`. Failures break the pipeline so you can roll back manually.
- **No-op stage**: if a commit only touches docs/config files unrelated to microservices, Jenkins exits without touching containers.
- **Force redeploy**: manually run the job with "Build with Parameters" (once parameters are added) or push a commit that touches `docker-compose.yaml`.

## 10. Operations checklist
- **Manual redeploy**: `cd /var/lib/jenkins/workspace/graintrade-prod && docker compose up -d backend`.
- **Status**: `docker compose ps`, `docker logs --tail 100 <container>`.
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
| Pipeline skips deploy | Confirm the commit actually touched directories listed in `serviceCatalog`. Use "Replay" in Jenkins to inspect `changedFiles`. |
| Health check fails | `curl -v http://127.0.0.1:<port>/health`, `docker logs grain-<service>-1`. Adjust health URLs in `serviceCatalog` if endpoints moved. |
| Webhook not firing | Check Gitea webhook delivery log and Jenkins system log (Manage Jenkins → System Log → All). |

With this setup you now have a self-hosted CI/CD loop: push to Gitea, get deterministic builds via Jenkins, and restart only the services that changed. The docs above should be enough to reproduce the platform on a fresh Hetzner node end-to-end.
