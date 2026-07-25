# GitHub Actions + Docker Hub + Hetzner (Fedora 44) Deployment Roadmap

This document is the operational roadmap for production deployment of GrainTrade using:

- GitHub Actions for CI/CD
- Docker Hub as image registry
- Hetzner server with Fedora 44
- Apache HTTP Server (Apache 2.4, package/service name is usually `httpd` on Fedora)

Workflow file: `.github/workflows/deploy.yml`

## 1. Brief Audit of Current CI/CD Logic

Current pipeline logic is correct at a high level:

1. Build service images on GitHub Actions.
2. Push images to Docker Hub with tag = commit SHA.
3. SSH to server.
4. `docker login` + `docker compose pull && up -d` on server.

Most likely reasons it worked on old server but fails on new Fedora 44 server:

1. **Rootless Docker session mismatch over SSH**.
   - Non-interactive SSH sessions often miss runtime variables needed by rootless Docker.
   - Result: login can pass but `docker compose pull` cannot reach daemon/socket.
2. **Remote deployment directory assumptions**.
   - Workflow expects `/home/kivaschenko/production/docker-compose.prod.yaml` and `envs/*.env` to exist.
   - If missing, deployment fails after successful login.
3. **Compose plugin or daemon state differences**.
   - Fedora may have Docker CLI installed without compose plugin enabled/available.
4. **User service lifecycle**.
   - Rootless daemon may require linger/user-service setup to survive non-interactive sessions.

### What was improved in workflow

The deploy workflow now includes stricter preflight checks and better rootless handling:

- Verifies Docker CLI and `docker compose` plugin exist.
- Exports `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`, and `DOCKER_HOST` for SSH session.
- Waits for rootless socket and falls back to `/var/run/docker.sock` if available.
- Fails early with clear messages when compose file or required env files are missing.
- Validates compose config before pull/up.

## 2. GitHub Secrets Checklist

Configure in repository settings -> Secrets and variables -> Actions:

| Secret | Required | Example |
| --- | --- | --- |
| `DOCKERHUB_USERNAME` | yes | `kivaschenko` |
| `DOCKERHUB_TOKEN` | yes | Docker Hub access token |
| `DEPLOY_HOST` | yes | server IP or DNS |
| `DEPLOY_PORT` | yes (or default 22) | `22` |
| `DEPLOY_USER` | yes | `kivaschenko` |
| `DEPLOY_SSH_KEY` | yes | private key matching server authorized key |
| `FRONTEND_ENV_PRODUCTION` | yes | full `.env.production` content |

Recommendation:

- Keep these secrets at environment level (`production_env`) because workflow uses `environment: production_env`.

## 3. Hetzner Server Provisioning (Fedora 44)

### 3.1 Base OS prep

```bash
sudo dnf -y update
sudo timedatectl set-timezone Europe/Kyiv
```

### 3.2 Install Docker Engine + Compose plugin

Use Docker official repo instructions for Fedora (recommended), then verify:

```bash
docker --version
docker compose version
```

### 3.3 Configure user `kivaschenko` for rootless mode

Run as `kivaschenko` (not root):

```bash
loginctl enable-linger kivaschenko
systemctl --user enable --now docker
systemctl --user status docker --no-pager
```

Verify socket exists:

```bash
ls -l /run/user/$(id -u)/docker.sock
```

If you choose rootful Docker instead, ensure `kivaschenko` is in docker group and `/var/run/docker.sock` is accessible.

### 3.4 Prepare deployment directory

```bash
mkdir -p /home/kivaschenko/production/envs
```

Copy these files from repository to `/home/kivaschenko/production`:

- `docker-compose.prod.yaml`
- `envs/backend.env`
- `envs/chat-room.env`
- `envs/notifications.env`
- `envs/data-pipeline.env`

Then verify:

```bash
cd /home/kivaschenko/production
ls -la
ls -la envs
```

## 4. One-Time Manual Deploy Validation on Server

Run once manually to prove server setup before relying on CI/CD:

```bash
cd /home/kivaschenko/production
export IMAGE_REGISTRY=docker.io
export IMAGE_NAMESPACE=<dockerhub_username>
export TAG=<existing_image_tag_or_sha>

docker login docker.io -u "$IMAGE_NAMESPACE"
docker compose -f docker-compose.prod.yaml config -q
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d
docker compose -f docker-compose.prod.yaml ps
```

If manual run fails, fix server-side issue first (do not debug GitHub Actions yet).

## 5. Apache Setup Plan (Fedora)

Note: on Fedora, service/package names are typically:

- package: `httpd`
- service: `httpd`
- config root: `/etc/httpd`

### 5.1 Install and enable Apache

```bash
sudo dnf -y install httpd mod_ssl
sudo systemctl enable --now httpd
sudo systemctl status httpd --no-pager
```

### 5.2 Deploy your prepared vhost configs

Source directory in repo:

- `apache_files/sites-available/`

Target directory on Fedora:

- `/etc/httpd/conf.d/`

Suggested approach:

1. Copy only needed files first (`graintrade.info-le-ssl.conf`, `api.graintrade.info.conf`, `chat.graintrade.info.conf`, `data-pipeline.graintrade.info.conf`, `home.graintrade.info.conf`, plus shared security includes).
2. Ensure included paths in each file match Fedora layout.
3. Test and reload:

```bash
sudo httpd -t
sudo systemctl reload httpd
```

### 5.3 SELinux and firewall

Fedora defaults are stricter than Ubuntu:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Allow Apache reverse proxy network connections if needed
sudo setsebool -P httpd_can_network_connect 1
```

## 6. DNS and TLS

1. Point domains/subdomains to Hetzner public IP.
2. Confirm A/AAAA propagation.
3. Issue certificates (Certbot or existing ACME strategy).
4. Reload Apache and verify HTTPS endpoints.

## 7. GitHub Actions Deployment Runbook

After server passes manual validation:

1. Push to `main` or run workflow manually.
2. In Actions logs:
   - verify all image builds and pushes complete.
   - verify deploy step reaches `docker compose ... config -q` and `pull`/`up -d`.
3. On server, validate:

```bash
docker compose -f /home/kivaschenko/production/docker-compose.prod.yaml ps
curl -f http://localhost:8000/health
curl -f http://localhost:8001/health
curl -f http://localhost:8002/health
curl -f http://localhost:8003/health
curl -f http://localhost:8004/health
```

## 8. Recommended Operations Policy

1. Keep compose and `envs/*.env` under controlled change process.
2. Store only image tag/version changes in CI deploy path.
3. For rollback, redeploy previous `TAG` (previous commit SHA).
4. Add a lightweight post-deploy smoke-check job in GitHub Actions (health endpoints).

## 9. Fast Troubleshooting Matrix

### Symptom: `docker login` succeeds, `docker compose pull` fails

Check:

```bash
echo "$DOCKER_HOST"
docker info
docker compose version
```

Likely cause: socket/session mismatch (rootless daemon not available in SSH session).

### Symptom: `docker compose` says file/env missing

Check:

```bash
ls -la /home/kivaschenko/production
ls -la /home/kivaschenko/production/envs
```

Likely cause: production directory not prepared on new server.

### Symptom: containers run but public domains fail

Check:

```bash
sudo httpd -t
sudo systemctl status httpd --no-pager
sudo ss -tulpen | grep -E ':80|:443|:8000|:8001|:8002|:8003|:8004|:8080'
```

Likely cause: Apache vhost mismatch, firewall, SELinux, or DNS/TLS issue.

## 10. Appendix: Minimal CI/CD Flow

```text
push main -> GitHub Actions build -> push images to Docker Hub
-> SSH to Hetzner -> docker login -> compose pull -> compose up -d
-> Apache reverse-proxy serves public domains
```
