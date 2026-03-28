# 🚀 GitHub Actions CI/CD Pipeline

The project uses **GitHub Actions** for automated CI/CD. All deployment workflows are defined in [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

---

## 📋 GitHub Actions Setup

### Required Secrets

Configure these in GitHub repo settings → **Secrets and variables** → **Actions**:

| Secret | Description |
| --- | --- |
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `DEPLOY_SSH_KEY` | Private SSH key for production server |
| `DEPLOY_HOST` | Production server hostname/IP |
| `DEPLOY_PORT` | SSH port (default: 22) |
| `DEPLOY_USER` | SSH user on production server |
| `FRONTEND_ENV_PRODUCTION` | Vue.js environment variables for production |

### Workflow Overview

The GitHub Actions pipeline:

1. **Triggers** on push to `main` branch or manual dispatch
2. **Builds** all microservice Docker images with commit SHA tag
3. **Pushes** images to Docker Hub
4. **Deploys** to production via SSH:
   - Pulls latest images
   - Runs `docker compose up -d`

---

## 🔄 CI/CD Flow

```
[Git push to main] → 
[GitHub Actions triggers] → 
[Build Docker images with commit SHA] → 
[Push to Docker Hub] → 
[SSH to production server] → 
[docker compose pull & up -d]
```

---

## 🚀 Deployment Commands

Manual deployment on production server:

```bash
# Set environment variables
export IMAGE_REGISTRY=docker.io
export IMAGE_NAMESPACE=<dockerhub_username>
export TAG=<commit_sha>

# Pull and deploy
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d
```

---

## 🔄 Rollback Strategy

To rollback to a previous version:

```bash
# Deploy previous known-good commit SHA
export TAG=<previous_commit_sha>
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d
```

---

## 📝 Production Compose File

The production compose file (`docker-compose.prod.yaml`) supports environment variable overrides:

- `IMAGE_REGISTRY` (default: `docker.io`)
- `IMAGE_NAMESPACE` (default: `kivaschenko`)
- `TAG` (default: `latest`)

Example compose entries:

```yaml
backend:
  image: ${IMAGE_REGISTRY}/${IMAGE_NAMESPACE}/backend:${TAG}
  restart: always
  env_file:
    - ./envs/backend.env
```

---

## ✅ Pre-deployment Checklist

Before enabling automated deployments:

1. ✅ Push code to GitHub main branch
2. ✅ Add all required secrets in GitHub Actions settings
3. ✅ Verify Docker images build successfully locally
4. ✅ Test SSH access to production server
5. ✅ Ensure production server has docker and docker compose installed
6. ✅ Create environment files on production server:
   - `/home/kivaschenko/production/envs/backend.env`
   - `/home/kivaschenko/production/envs/chat-room.env`
   - `/home/kivaschenko/production/envs/notifications.env`
   - `/home/kivaschenko/production/envs/data-pipeline.env`

---

## 🔧 Manual Workflow Dispatch

You can also trigger the workflow manually from GitHub:

1. Go to **Actions** tab
2. Select **Deploy** workflow
3. Click **Run workflow**
4. Select the branch and commit

---

## 📊 Monitoring Deployments

- View workflow status in GitHub **Actions** tab
- Check logs for each job step
- Verify production containers with `docker ps` on production server

---

## 🆘 Troubleshooting

### Images not being pushed to Docker Hub
- Verify `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are set correctly
- Check if token has permission for Docker Hub repositories

### SSH deployment fails
- Verify `DEPLOY_SSH_KEY` is a valid private key
- Test SSH connection manually: `ssh -i key.pem user@host`
- Ensure SSH user can run `docker` and `docker compose` commands

### Production containers not updating
- Check that docker images are actually being pulled: `docker compose pull`
- Verify production compose file uses correct variable names
- Check production server has internet access to pull from Docker Hub

---

## 📚 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Hub Authentication](https://docs.docker.com/docker-hub/access-tokens/)
- [Docker Compose Override Variables](https://docs.docker.com/compose/how-tos/environment-variables/)
