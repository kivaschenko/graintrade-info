# About project
This is a favorite project for learning more about asynchronous API with the FastAPI package. The main concept of the business is to help cope with a large number of offers from small and large participants of the agricultural market, tied to geographical points. You also need different filters to search for information.
It should be completely anonymous and transparent, storing sensitive data as cryptographically hashed.

## Azure stage host
Redoc API: <https://web-app-graintrade.mangosky-9dd5102f.westus2.azurecontainerapps.io/redoc>

Docs API: <https://web-app-graintrade.mangosky-9dd5102f.westus2.azurecontainerapps.io/docs>

# Development
## Environment
To install all dependencies use `poetry`. Move to `graintrade-info/` and run:
```
poetry install
```
Make sure you have completed at least one `env` file.

To run locally you can use 2 ways:

1. Casually running of FastAPI and previously checked database params in `.env` or `env.dev` file and have a workinf PostgreSQL database:
```
fastapi dev
```
Note, check what `env` file is using in `config.py` `Settings` previuosly as well.

2. Or using docker compose. To run this use command:
```
docker compose up --build
```

# Production
## Deployment
To deploy in Azure container app service:
```
az login && az acr login --name {azure_container_registry_name} && docker tag {local_image_name}:{tag} {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag} && docker push {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag} && az webapp create --resource-group {resource_group_name} --plan {app_service_plan} --name {webapp_name} --deployment-container-image-name {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag}
```
