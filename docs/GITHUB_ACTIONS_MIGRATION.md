# GitHub Actions Migration Package

This guide moves production deploys from Gitea/Jenkins to GitHub Actions with Docker Hub.

## What was added
- Workflow: .github/workflows/deploy.yml
- Production compose updated: docker-compose.prod.yaml

The workflow now:
1. Triggers on push to main (and manual dispatch).
2. Builds and pushes all microservice images every run with one shared tag: commit SHA.
3. Generates frontend/.env.production from a GitHub secret before frontend build.
4. Deploys over SSH to production and runs docker compose pull/up with matching TAG.

## Required GitHub repository secrets
Create these in GitHub repo settings -> Secrets and variables -> Actions:

1. DOCKERHUB_USERNAME
2. DOCKERHUB_TOKEN
3. FRONTEND_ENV_PRODUCTION
4. DEPLOY_SSH_KEY
5. DEPLOY_HOST
6. DEPLOY_PORT
7. DEPLOY_USER

## Production host prerequisites
1. docker and docker compose installed.
2. Production project available in /home/kivaschenko/production.
3. Runtime env files present:
   - /home/kivaschenko/production/envs/backend.env
   - /home/kivaschenko/production/envs/chat-room.env
   - /home/kivaschenko/production/envs/notifications.env
   - /home/kivaschenko/production/envs/data-pipeline.env
4. SSH user can run docker compose in /home/kivaschenko/production.

## Compose image source model
The production compose file now supports overrides:
- IMAGE_REGISTRY (default docker.io)
- IMAGE_NAMESPACE (default kivaschenko)
- TAG (default latest)

Example deploy command on server:

IMAGE_REGISTRY=docker.io IMAGE_NAMESPACE=<dockerhub_user> TAG=<commit_sha> docker compose -f docker-compose.prod.yaml pull
IMAGE_REGISTRY=docker.io IMAGE_NAMESPACE=<dockerhub_user> TAG=<commit_sha> docker compose -f docker-compose.prod.yaml up -d

## Cutover checklist
1. Push current branch to GitHub.
2. Add all required secrets in GitHub.
3. Disable old deploy automations:
   - Gitea Actions workflow in .gitea/workflows/deploy.yaml
   - Jenkins job webhook trigger
4. Run GitHub workflow manually once from Actions tab.
5. Verify production containers are running the new tag.
6. Enable push-based deploys on main.

## Rollback strategy
If a deploy fails, redeploy previous known good tag:

IMAGE_REGISTRY=docker.io IMAGE_NAMESPACE=<dockerhub_user> TAG=<previous_sha> docker compose -f docker-compose.prod.yaml pull
IMAGE_REGISTRY=docker.io IMAGE_NAMESPACE=<dockerhub_user> TAG=<previous_sha> docker compose -f docker-compose.prod.yaml up -d

## Notes
- Frontend runtime env file in compose was removed intentionally; Vue environment values are build-time and come from FRONTEND_ENV_PRODUCTION during build.
- If you want to add tests or scan gates before deploy, add a test job and make deploy depend on it.
