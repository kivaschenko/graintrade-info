# Installation PostgrSQL 18 + PostGIS on Fedora 43
 To install PostgreSQL 18 with PostGIS on Fedora, you should
use the official PostgreSQL yum repository as the Fedora modular stream might have an older version. 

## Step 1: Add the PostgreSQL Yum Repository 
First, you need to add the external PostgreSQL repository to your system to access the specific version 18 packages. (The exact URL for the latest Fedora version, e.g., F-43, will be on the PostgreSQL download page, the following is an example format): 
```bash
sudo dnf install -y https://download.postgresql.org
```
If you encounter a conflict with the stock Fedora PostgreSQL module, you may need to disable the default Fedora module first: 
```bash
sudo dnf -y module disable postgresql
```

## Step 2: Install PostgreSQL 18 and PostGIS 
With the repository in place, you can install the server packages for PostgreSQL 18 and the PostGIS extension: 
```bash
sudo dnf install -y postgresql18-server postgresql18-contrib postgis35_18
```
(Note: The PostGIS package name format may vary slightly, but generally follows postgis[version]_[pgversion]. The above assumes version 3.5 of PostGIS for PostgreSQL 18).

## Step 3: Initialize the Database and Start the Service 
The PostgreSQL server requires initialization of its data directory before it can be started. 
```bash
# Initialize the database
sudo /usr/pgsql-18/bin/postgresql-18-setup initdb

# Enable the PostgreSQL service to start at boot
sudo systemctl enable postgresql-18

# Start the PostgreSQL service
sudo systemctl start postgresql-18
```
## Step 4: Configure and Access the Database
A default postgres user is created during installation. Switch to this user to access the psql shell: 
```bash
sudo -u postgres psql
```
From within the psql prompt, you can perform administrative tasks like creating new users and databases. 
## Step 5: Enable the PostGIS Extension in a Database 
Once you have created a database (e.g., mydb), you can enable the PostGIS extension within that specific database. 
```bash
# Exit the psql shell if you are in it (use \q)
\q

# Connect to your new database as the postgres user
sudo -u postgres psql -d mydb

# Enable the PostGIS extension
CREATE EXTENSION postgis;

# Verify the installation (optional)
SELECT PostGIS_full_version();

# Exit psql
\q
```
Your PostgreSQL 18 installation is now ready with PostGIS support. For further configuration, refer to the Fedora Docs on PostgreSQL or the official PostgreSQL documentation. 

Useful links:
- https://docs.fedoraproject.org/en-US/quick-docs/postgresql/