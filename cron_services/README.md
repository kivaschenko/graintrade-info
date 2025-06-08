# Subscription Checker Service

This service handles automated subscription management tasks for the GrainTrade application.

## Overview

The service runs as a standalone microservice that periodically checks and updates subscription statuses in the database. It automatically handles expiration of paid subscriptions and manages free plan transitions.

## Project Structure

```
cron_services/
├── app/
│   ├── __init__.py
│   ├── database.py      # Database connection handling
│   └── check_subscriptions.py  # Main subscription checking logic
├── Dockerfile          # Container configuration
├── entrypoint.sh      # Container entry point script
├── requirements.txt    # Python dependencies
└── README.md          # This documentation
```

## Features

- Daily subscription status checks at midnight (UTC)
- Automatic transition from expired paid plans to free plans
- Automatic renewal of free plans
- Comprehensive logging system
- Containerized deployment with Docker
- Environment-based configuration
- Fault-tolerant database operations

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| POSTGRES_DB | Database name | graintrade | Yes |
| POSTGRES_USER | Database user | postgres | Yes |
| POSTGRES_PASSWORD | Database password | postgres | Yes |
| POSTGRES_HOST | Database host | localhost | Yes |
| POSTGRES_PORT | Database port | 5432 | Yes |

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/graintrade-info.git
cd graintrade-info/cron_services
```

2. Build the Docker image:
```bash
docker-compose build subscription-checker
```

3. Start the service:
```bash
docker-compose up -d subscription-checker
```

## Monitoring

### View Service Logs

```bash
# View all logs
docker-compose logs subscription-checker

# Follow log output
docker-compose logs -f subscription-checker

# View last 100 lines
docker-compose logs --tail=100 subscription-checker
```

### Check Service Status

```bash
docker-compose ps subscription-checker
```

## Development

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 14+
- Access to main database

### Local Development Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export POSTGRES_DB=graintrade
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
```

4. Run manually:
```bash
python app/check_subscriptions.py
```

## Database Functions

The service uses the following core database function:

```sql
update_expired_subscriptions()
```

This function performs:
- Status updates for expired paid subscriptions
- Creation of new free subscriptions for users with expired paid plans
- Automatic renewal of expired free subscriptions

## Maintenance Tasks

### Daily
- Monitor error logs
- Verify successful execution
- Check subscription transitions

### Weekly
- Review log storage
- Monitor database connection performance
- Check for failed operations

### Monthly
- Review subscription patterns
- Analyze error trends
- Update documentation if needed

## Troubleshooting

### Common Issues

1. Database Connection Errors
   - Verify database credentials
   - Check network connectivity
   - Ensure database service is running

2. Cron Execution Issues
   - Check cron service status: `service cron status`
   - Verify log file permissions
   - Review crontab configuration: `crontab -l`

3. Container Issues
   - Check container logs
   - Verify container is running: `docker ps`
   - Review Docker logs: `docker logs subscription-checker`

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Follow coding standards:
   - PEP 8 style guide
   - Add appropriate logging
   - Include unit tests
   - Update documentation
4. Commit your changes: `git commit -m 'Add AmazingFeature'`
5. Push to the branch: `git push origin feature/AmazingFeature`
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter)
Project Link: [https://github.com/yourusername/graintrade-info](https://github.com/yourusername/graintrade-info)