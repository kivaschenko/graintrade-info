Old version of README file for `backend` microservice...
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


# Production

## Deployment on MS Azure
To deploy in Azure container app service:
```
az login && az acr login --name {azure_container_registry_name} && docker tag {local_image_name}:{tag} {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag} && docker push {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag} && az webapp create --resource-group {resource_group_name} --plan {app_service_plan} --name {webapp_name} --deployment-container-image-name {azure_container_registry_name}.azurecr.io/{remote_image_name}:{tag}
```

## Postgres
### Create a new DB:
```
# Variables
RESOURCE_GROUP="<your-resource-group>"
SERVER_NAME="<your-server-name>"
LOCATION="<your-location>"
ADMIN_USER="<your-admin-username>"
ADMIN_PASSWORD="<your-admin-password>"
DATABASE_NAME="<your-database-name>"
IP_ADDRESS="<your-ip-address>"

# Create PostgreSQL server
az postgres server create \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --location $LOCATION \
    --admin-user $ADMIN_USER \
    --admin-password $ADMIN_PASSWORD \
    --sku-name B_Gen5_1

# Create PostgreSQL database
az postgres db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $SERVER_NAME \
    --name $DATABASE_NAME

# Configure firewall rules
az postgres server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server-name $SERVER_NAME \
    --name AllowMyIP \
    --start-ip-address $IP_ADDRESS \
    --end-ip-address $IP_ADDRESS

# Connect to the PostgreSQL database and enable PostGIS extension
psql "host=$SERVER_NAME.postgres.database.azure.com port=5432 dbname=$DATABASE_NAME user=$ADMIN_USER@$SERVER_NAME password=$ADMIN_PASSWORD sslmode=require" <<EOF
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
EOF
```

Set POSTGIS extensions
```
# Variables
RESOURCE_GROUP="<your-resource-group>"
SERVER_NAME="<your-server-name>"

# Enable PostGIS extension
az postgres flexible-server parameter set \
    --resource-group $RESOURCE_GROUP \
    --server-name $SERVER_NAME \
    --name azure.extensions \
    --value postgis

# Connect to the PostgreSQL database and enable PostGIS extension
psql -h graintrade-info-postgres-db.postgres.database.azure.com -p 5432 -U grain_admin_db postgres <<EOF
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
EOF
```
## Deploy to Azure

### Create resource group and registry

#### Step 1. Create a resource group with the `az group create` command.
```
az group create --location westeurope --resource-group ecomm-rg
```
<location> is one of the Azure location Name values from the output of the command `az account list-locations -o table`.

#### Step 2. Create a container registry with the `az acr create` command.
```
az acr create \
> --resource-group ecomm-rg \
> --name ecommregistry \
> --sku Basic \
> --admin-enabled
```
`<registry-name>` must be unique within Azure, and contain 5-50 alphanumeric characters.

* You can view the credentials created for admin with:
```
az acr credential show \
--name <registry-name> \
--resource-group pythoncontainer-rg
```

#### Step 3. Sign in to the registry using the `az acr login` command.
```
az acr login --name ecommregistry
```

The command adds "azurecr.io" to the name to create the fully qualified registry name. If successful, you'll see the message "Login Succeeded". If you're accessing the registry from a subscription different from the one in which the registry was created, use the `--suffix` switch.

#### Step 4. Build the image with the `az acr build` command.
```
az acr build \
--registry ecommregistry \
--resource-group ecomm-rg \
--image ecomm-api:latest .
```
<b> Note that:</b>

* The dot (".") at the end of the command indicates the location of the source code to build. If you aren't running this command in the sample app root directory, specify the path to the code.

* If you are running the command in Azure Cloud Shell, use git clone to first pull the repo into the Cloud Shell environment first and change directory into the root of the project so that dot (".") is interpreted correctly.

* If you leave out the `-t` (same as `--image`) option, the command queues a local context build without pushing it to the registry. Building without pushing can be useful to check that the image builds.

#### Step 5. Confirm the container image was created with the `az acr repository list` command.
```
az acr repository list --name <registry-name>
```
### Create a database on the server
#### Step 6. Step 1 Use the `az postgres flexible-server db create` command to create a database. 
```
az postgres flexible-server db create --resource-group pythoncontainer-rg --server-name <postgres-server-name> --database-name restaurants_reviews
```
Where:

"pythoncontainer-rg" → The resource group name used in this tutorial. If you used a different name, change this value.
`<postgres-server-name>` → The name of the PostgreSQL server.

You could also use the az postgres flexible-server connect command to connect to the database and then work with psql commands. When working with psql, it's often easier to use the Azure Cloud Shell because all the dependencies are included for you in the shell.

### Deploy the web app to Container Apps

#### Step 1. Sign in to Azure and authenticate, if needed.
```
az login
```
#### Step 2. Install or upgrade the extension for Azure Container Apps withe `az extension add` command.
```
az extension add --name containerapp --upgrade
```

#### Step 3. Create a Container Apps environment with the `az containerapp env create` command.
```
az containerapp env create \
--name ecomm-api-container-env \
--resource-group ecomm-rg \
--location westeurope
```
`<location>` is one of the Azure location Name values from the output of the command `az account list-locations -o table`.

#### Step 4. Get the sign-in credentials for the Azure Container Registry.
```
az acr credential show -n ecommregistry
```
Use the username and one of the passwords returned from the output of the command.

#### Step 5. Create a container app in the environment with the `az containerapp create` command.
```
az containerapp create \
--name python-container-app \
--resource-group pythoncontainer-rg \
--image <registry-name>.azurecr.io/pythoncontainer:latest \
--environment python-container-env \
--ingress external \
--target-port 8000 \
--registry-server <registry-name>.azurecr.io \
--registry-username <registry-username> \
--registry-password <registry-password> \
--env-vars <env-variable-string>
--query properties.configuration.ingress.fqdn
```
`<env-variable-string>` is a string composed of space-separated values in the key="value" format with the following values.

    AZURE_POSTGRESQL_HOST=<postgres-server-name>.postgres.database.azure.com
    AZURE_POSTGRESQL_DATABASE=restaurants_reviews
    AZURE_POSTGRESQL_USERNAME=demoadmin
    AZURE_POSTGRESQL_PASSWORD=<db-password>
    RUNNING_IN_PRODUCTION=1
    AZURE_SECRET_KEY=<YOUR-SECRET-KEY>

Generate AZURE_SECRET_KEY value using output of `python -c 'import secrets; print(secrets.token_hex())'`.

Here's an example: 
```
--env-vars AZURE_POSTGRESQL_HOST="my-postgres-server.postgres.database.azure.com" AZURE_POSTGRESQL_DATABASE="restaurants_reviews" AZURE_POSTGRESQL_USERNAME="demoadmin" AZURE_POSTGRESQL_PASSWORD="somepassword" RUNNING_IN_PRODUCTION="1" AZURE_SECRET_KEY=asdfasdfasdf
```
# Additions

SQL Functions
```
-- Increment item count
SELECT increment_items_count(user_id);

-- Increment map views
SELECT increment_map_views(user_id);

-- Check usage
SELECT * FROM get_subscription_usage(user_id);
```