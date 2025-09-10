# Database Documentation

## Overview
This PostgreSQL database is designed for a grain trade information system. It handles user management, subscriptions, payments, and agricultural product listings with geospatial capabilities.

## Core Features

### Extensions
- `postgis` - Enables spatial and geographic objects
- `uuid-ossp` - Provides UUID generation functionality
- `pg_cron` - Handles scheduled tasks

### Tables Structure

#### Categories System
- `parent_categories` - Main category groups
- `categories` - Specific product categories with parent relationships
- `categories_hierarchy` - View showing category hierarchical structure

#### Product Listings
- `items` - Main product listings table with geospatial data
- `items_users` - Relationship between items and users

#### User Management
- `users` - User accounts and authentication
- `subscriptions` - User subscription management
- `tarifs` - Available subscription plans
- `payments` - Payment transaction records

### Subscription System

#### Tarif Plans
- Free
- Basic
- Premium
- Pro

Each plan includes limits for:
- Items creation
- Map views
- Geo searches
- Navigation usage

#### Subscription Logic
1. **Auto-Renewal System**
   - Checks daily for expired subscriptions
   - Automatically converts expired paid plans to free plans
   - Renews expired free plans automatically

2. **Usage Tracking**
   - `increment_items_count()` - Tracks item creation
   - `increment_map_views()` - Tracks map usage
   - `increment_navigation_count()` - Tracks navigation usage
   - `increment_geo_search_count()` - Tracks geo searches

3. **Status Management**
   - Active subscriptions
   - Expired subscriptions
   - Auto-renewal process

### Geospatial Features
- Automatic geometry calculation from latitude/longitude
- Spatial indexing for efficient location-based queries
- PostGIS integration for geographic operations

### Automated Tasks
- Daily subscription status updates at midnight
- Automatic geometry updates on item creation/modification

## Database Functions

### Subscription Management
```sql
update_expired_subscriptions()
check_subscription_status()
get_subscription_usage()
```

### Usage Tracking
```sql
increment_items_count()
increment_map_views()
increment_navigation_count()
increment_geo_search_count()
```

### Geometry Management
```sql
update_geometry_from_lat_lon()
```

## Indexing Strategy
- Geospatial index on items (GIST)
- B-tree indexes on frequently queried fields
- Composite indexes for complex queries
- JSON indexing for payment additional info

## Data Integrity
- Foreign key constraints
- Unique constraints
- Check constraints for positive values
- Automatic timestamp management
- Cascading updates/deletes where appropriate

## Security Features
- Password hashing
- Role-based access control
- Subscription-based feature limitations

## Maintenance
- Daily automated subscription updates
- Scheduled database maintenance tasks
- Built-in monitoring capabilities

## Best Practices
1. Always use prepared statements
2. Implement proper error handling
3. Use transactions for data consistency
4. Monitor database performance
5. Regular backup schedule
6. Keep indexes updated

## Development Guidelines
1. Use migrations for schema changes
2. Document all functions and triggers
3. Test performance impact of changes
4. Maintain referential integrity
5. Follow naming conventions

# Server config

## Install Postgres
```
sudo apt install postgresql postgresql-contrib
sudo apt install postgis postgresql-14-postgis-3
sudo -u postgres psql
```
## Create database
```
CREATE DATABASE graintrade;
CREATE USER grain WITH ENCRYPTED PASSWORD 'teomeo2358';
GRANT ALL PRIVILEGES ON DATABASE graintrade TO grain;
```

```
# PostgreSQL Production Configuration Template
# Location: /etc/postgresql/14/main/postgresql.conf (or similar)

# ✅ Memory and Performance (based on 64 GB RAM on Hetzner AX41)
shared_buffers = 16GB              # ~25% of 64GB RAM
work_mem = 128MB                  # for complex joins, tuned for fewer connections
effective_cache_size = 48GB       # ~75% of RAM, helps planner
maintenance_work_mem = 2GB        # for vacuum/analyze and index creation

# ✅ Write-Ahead Logging (WAL)
wal_level = replica
max_wal_size = 4GB
min_wal_size = 512MB
checkpoint_completion_target = 0.9

# ✅ Connections
max_connections = 100

# ✅ Locale and Timezone
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
timezone = 'UTC'

# ✅ Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql.log'
log_min_duration_statement = 250  # good default for dev & prod performance tuning
log_statement = 'none'

# ✅ Port
port = 5433  # custom dev port to avoid default 5432
```

Restart database
`sudo systemctl restart postgresql`.

# Seed data
```
cp ~/graintrade-info/postgres-init/init.sql /tmp/init.sql
sudo -u postgres psql -d graintrade -f /tmp/init.sql
```

# Backup
The easiest way on Ubuntu is to create a small **bash script** that calls `pg_dump` and run it daily with **cron**.

Here’s a working example:

---

### 1. Create backup script

`/usr/local/bin/pg_backup.sh`:

```bash
#!/bin/bash

# Database connection settings
DB_NAME="devdb"
DB_USER="devuser"
DB_PASS="devpassword"

# Backup directory
BACKUP_DIR="/var/backups/postgres"
DATE=$(date +\%Y-\%m-\%d_\%H-\%M)

# Ensure directory exists
mkdir -p "$BACKUP_DIR"

# Export password so pg_dump won't ask
export PGPASSWORD="$DB_PASS"

# Run pg_dump
pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -b -v -f "$BACKUP_DIR/${DB_NAME}_${DATE}.dump"

# Optional: remove backups older than 7 days
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +7 -delete
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/pg_backup.sh
```

---

### 2. Test script manually

```bash
/usr/local/bin/pg_backup.sh
```

It should create a file like:

```
/var/backups/postgres/devdb_2025-09-08_18-32.dump
```

---

### 3. Add to cron (daily at 02:00)

Edit cron:

```bash
crontab -e
```

Add line:

```cron
0 2 * * * /usr/local/bin/pg_backup.sh >> /var/log/pg_backup.log 2>&1
```

---

### 4. Restore from backup (when needed)

```bash
pg_restore -U devuser -d devdb /var/backups/postgres/devdb_2025-09-08_18-32.dump
```

---

Ага, зрозумів 👍
Помилка така:

```
pg_dump: connection to server on socket "/var/run/postgresql/.s.PGSQL.5433" failed: 
FATAL:  Peer authentication failed for user "grain"
```

### Чому так:

1. **pg\_dump не отримав пароль** → PostgreSQL спробував автентифікувати через `peer` (локальна авторизація по Linux-користувачу), і відхилив.
2. Ти явно під `root`, а користувач бази інший (`grain` або `devuser`).
3. PostgreSQL слухає на **5433** (не 5432). Це може бути:

   * встановлений не один PostgreSQL,
   * або ти вручну змінив порт у `postgresql.conf`.

---

### 🔧 Рішення:

#### Варіант 1. Вказати порт і хост в скрипті

У скрипті `/usr/local/bin/pg_backup.sh` заміни рядок `pg_dump` на:

```bash
pg_dump -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" -F c -b -v -f "$BACKUP_DIR/${DB_NAME}_${DATE}.dump"
```

---

#### Варіант 2. Додати `.pgpass`

Щоб уникнути проблем із паролем, створюєш файл `/root/.pgpass`:

```bash
nano /root/.pgpass
```

Вставляєш:

```
127.0.0.1:5433:devdb:devuser:devpassword
```

Права доступу:

```bash
chmod 600 /root/.pgpass
```

Тепер можна робити просто:

```bash
pg_dump -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_DIR/${DB_NAME}_${DATE}.dump"
```

і пароль підхопиться автоматично.

---

#### Варіант 3. Перевести `pg_hba.conf` на `md5`

Відкрити:

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Заміни рядок для `local` на:

```
local   all             all                                     md5
```

Потім:

```bash
sudo systemctl restart postgresql
```

---

👉 Запитання: у тебе PostgreSQL справді на порту **5433** (а не 5432)?
Можеш перевірити:

```bash
ss -ltnp | grep postgres
```

Тоді я підкажу фінальну версію скрипта під твій порт.

