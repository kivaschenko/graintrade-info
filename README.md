
# About project
This is a favorite project for learning more about asynchronous API with the FastAPI package. The main concept of the business is to help cope with a large number of offers from small and large participants of the agricultural market, tied to geographical points. You also need different filters to search for information.
It should be completely anonymous and transparent, storing sensitive data as cryptographically hashed.

# Development

## Environment
To install all dependencies use `poetry`. Move to `graintrade-info/needeing-service-dir/` and run:
```
poetry install
```
Make sure you have completed at least one `env` file.

To run locally you can use 2 ways:

1. Casually running of FastAPI and previously checked database params in `.env` file and have a workinf PostgreSQL database:
```
fastapi dev
```
Note, check what `env` file is using in `config.py` `Settings` previuosly as well.

2. Or using docker compose. To run this use command:
```
docker compose up --build
```

3. Create tables
```
cd shared-libs/
poetry shell
python create_tables.py
```

### Kafka and infrastructure
#### Create images for Kafka

```
docker pull ubuntu/kafka
docker pull ubuntu/zookeeper
docker pull provectuslabs/kafka-ui
```
#### Make a network
```
docker network create -d bridge kafka-network
```
Launch the zookeeper image locally
```
docker run --detach  --name zookeeper-container --network kafka-network ubuntu/zookeeper:3.8-22.04_edge
```
[more about  zookeeper dockerized here](https://hub.docker.com/r/ubuntu/zookeeper)

Launch Kafka in container

```
docker run --detach --name kafka-container --network kafka-network -p 9092:9092 ubuntu/kafka:latest
```
[more about kafka dockerized here](https://hub.docker.com/r/ubuntu/kafka)



# Production
## Deployment
To deploy in Azure container app service:
```
az login && az acr login --name {azure_container_registry_name} && docker tag {local_image_name}:{tag} {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag} && docker push {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag} && az webapp create --resource-group {resource_group_name} --plan {app_service_plan} --name {webapp_name} --deployment-container-image-name {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag}
```
