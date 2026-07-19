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

Grant permissions if get  ERROR:  permission denied for table tarifs SQL state: 42501.
This is a classic PostgreSQL permissions issue, not an SELinux problem.

When you run `GRANT ALL PRIVILEGES ON DATABASE graindb TO grainuser`, you are only granting permission to **connect** to the database itself [1.1.1, 1.2.3]. This does not automatically grant rights to the internal objects (schemas, tables, or sequences) contained within that database [1.1.1]. Because PostgreSQL has a strict security model, you must explicitly grant access to those specific objects [1.1.1, 1.3.2].

### The Solution

You need to grant `USAGE` on the schema and then `SELECT`, `INSERT`, etc., on the tables and sequences [1.1.3, 1.2.4]. Run these commands as the `postgres` superuser (or the owner of the tables) while connected to the `graindb` database [1.1.3].

#### 1. Grant Schema Usage

The user needs permission to "enter" the `public` schema [1.1.3].

```sql
GRANT USAGE ON SCHEMA public TO grainuser;

```

#### 2. Grant Table Permissions

To allow the user to read and modify existing data, run:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO grainuser;

```

*(If you want them to have full control, including the ability to alter table structures, you can use `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO grainuser;`)* [1.1.3, 1.2.3].

#### 3. Grant Sequence Permissions

If your tables use `SERIAL` or `IDENTITY` columns, they rely on sequences [1.1.2]. Without these permissions, the user might get errors when trying to insert new records [1.1.3, 1.2.4].

```sql
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO grainuser;

```

---

### Important: Handling Future Tables

The commands above only affect **existing** tables [1.2.3]. If your application creates new tables in the future, `grainuser` will likely face "permission denied" errors again [1.2.3]. To prevent this, set **Default Privileges** so that any new table created by the owner (likely the `postgres` user) automatically grants permissions to `grainuser` [1.1.3, 1.2.3]:

```sql
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO grainuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO grainuser;

```

### Why it isn't SELinux

If SELinux were blocking this, you would typically see connection errors (e.g., "Connection refused" or "Could not connect to server") or log messages related to system sockets/files [1.3.1]. Since your pgAdmin can successfully connect and list the table names/metadata, the network and authentication layers are working perfectly. The `42501` error is strictly an internal PostgreSQL authorization check [1.3.1, 1.3.2].

To answer your question directly: **It depends on how those objects were created and what they do.**

Here is the breakdown for Views and Functions:

### 1. Views

* **Do you need to grant access?** Yes.
* **How it works:** In PostgreSQL, a `VIEW` is treated like a table for permission purposes. If you ran `GRANT SELECT ON ALL TABLES...` as I suggested in the previous step, **it usually includes Views automatically** because they are considered "relations" [1.4.1].
* **The Catch:** Even if you grant `SELECT` on the View, the user **also** needs `USAGE` permission on the schema containing the tables that the View relies on. If the user does not have permission to read the underlying tables, they may still get a permission error when trying to query the View, unless the View is using `SECURITY DEFINER` (which executes with the owner's privileges) [1.1.3, 1.3.2].

### 2. Functions

* **Do you need to grant access?** Often, **no**, because `EXECUTE` permission on functions is granted to `PUBLIC` by default in PostgreSQL [1.1.1, 1.3.2].
* **The Exception:** If you or your security policy revoked `PUBLIC` access to functions (which is a common hardening step), you will need to manually grant access [1.3.2, 1.4.2]:
```sql
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO grainuser;

```


* **Important Note:** If your function performs internal actions (like reading from a table), it must either be owned by a user who has access to those tables, or be marked as `SECURITY DEFINER` [1.3.2]. If the function is a standard `SECURITY INVOKER` (the default), `grainuser` must have permission to access the underlying tables inside the function as well [1.1.3, 1.3.2].

---

### Summary Checklist

If `grainuser` still cannot access your data, run these commands as the `postgres` superuser while connected to `graindb`:

| Object Type | Command |
| --- | --- |
| **Tables & Views** | `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO grainuser;` |
| **Sequences** | `GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO grainuser;` |
| **Functions** | `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO grainuser;` |

**Pro Tip:** If you want to make sure your user has permission for any future objects you create, use the `ALTER DEFAULT PRIVILEGES` command for each type [1.4.2]:

```sql
-- For Tables and Views
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO grainuser;

-- For Functions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO grainuser;

-- For Sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO grainuser;

```

Yes, it makes perfect sense and is actually considered **best practice** in PostgreSQL to create a dedicated user and then make that user the **owner** of the database [1.3.1].

This approach is superior because it inherently grants the user full control over the objects within their own database without needing to be a superuser [1.1.1, 1.1.2]. It keeps your application isolated and secure [1.3.1].

### Why this is better

1. **Automatic Permissions:** As the owner, the user automatically has all privileges on the objects they create [1.2.3]. They won't run into "permission denied" errors when creating tables, indexes, or functions [1.2.3].
2. **Clean Separation:** You avoid mixing your application's database objects with the default `postgres` superuser account [1.3.1].
3. **Security:** Your application connects with a user that only has access to its own database, minimizing the blast radius if your application's credentials are ever compromised [1.3.1].

---

### How to do it (The Recommended Workflow)

Instead of using the `postgres` superuser to create the tables, you set the user as the owner from the very beginning.

#### 1. Create the user and the database

Run these commands as the `postgres` superuser:

```sql
-- Create the user
CREATE USER grainuser WITH PASSWORD 'somepassword';

-- Create the database and assign ownership
CREATE DATABASE graindb OWNER grainuser;

```

#### 2. Seed the `init.sql` as the new user

Now that `grainuser` owns the database, you don't need to use `sudo -u postgres`. You can connect directly as `grainuser` to run your script. Since `grainuser` is the owner, it will have all the necessary permissions to create the tables, schemas, and default values defined in your `init.sql` [1.2.3].

Run this from your terminal:

```bash
psql -d graindb -U grainuser -f /tmp/init.sql

```

*(You will be prompted for `grainuser`'s password.)*

### A Note on the `public` Schema

By default, the `public` schema is owned by the superuser (`postgres`). When you create tables inside it, they will be owned by `grainuser`, but the `public` schema itself remains owned by `postgres` [1.2.3].

This is usually fine. However, if you want `grainuser` to have complete ownership of the entire database structure, including the schema itself, you can perform one extra step as the **`postgres` superuser** after creating the database:

```sql
-- Connect to graindb as postgres, then run:
ALTER SCHEMA public OWNER TO grainuser;

```

With this setup, your application is much more robust, and you will rarely (if ever) need to worry about manual `GRANT` commands again because your application user will inherently own everything it creates.

It looks like you are mixing up two different concepts: **Database Roles** (PostgreSQL users) and **System Users** (Linux/Fedora users).

The error `sudo: unknown user grainuser` happens because there is no OS-level user named `grainuser` on your Fedora system [1.3.1]. You only created a **database role** within PostgreSQL [1.4.3].

Here is how to fix this and successfully run your script.

---

### Step 1: Fix the Database Authentication

The "password authentication failed" error means the password you are typing for `grainuser` in PostgreSQL does not match what the database has on record [1.1.1].

Since you are already logged in as `root`, you can bypass the password prompt entirely by using the `postgres` superuser account to reset it [1.1.1, 1.2.1].

1. **Access PostgreSQL as the superuser:**
```bash
sudo -u postgres psql

```


2. **Reset the `grainuser` password:**
```sql
ALTER USER grainuser WITH PASSWORD 'somepassword';

```


*(Replace `'somepassword'` with the actual password you want to use.)*
3. **Exit psql:**
```sql
\q

```



---

### Step 2: Run your `init.sql` script

Now that you have confirmed the password, you don't need to create a Linux user. You can run your script as the `postgres` user, but tell PostgreSQL to run the commands **as if** you were `grainuser` [1.1.1].

**Run this command as `root`:**

```bash
sudo -u postgres psql -d graindb -U grainuser -h localhost -f /tmp/init.sql

```

**Why this works:**

* `sudo -u postgres`: Uses the system's `postgres` account to bypass OS-level permission issues [1.3.1].
* `-d graindb`: Specifies the target database.
* `-U grainuser`: Tells the database to execute the script with the permissions of `grainuser`.
* `-h localhost`: Forces the connection to go through the network stack, which triggers the password prompt (or authentication check) [1.1.1, 1.1.3].
* **When prompted for a password**, enter the new password you just set in Step 1.

---

### Summary of Differences

* **PostgreSQL Role (`grainuser`)**: This lives inside the database. It is what you use for `SELECT`, `INSERT`, and connection credentials [1.4.3].
* **System User (`grainuser`)**: This would be a user account created with `useradd` on Fedora. You **do not need this** to run your database script.

If you still get an authentication error, double-check your `pg_hba.conf` file (usually in `/var/lib/pgsql/data/`) to ensure that `localhost` connections are allowed to use `md5` or `scram-sha-256` authentication [1.1.1, 1.2.3].