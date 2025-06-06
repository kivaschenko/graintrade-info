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
