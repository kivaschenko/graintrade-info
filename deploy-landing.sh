#!/bin/bash

# Landing Service Deployment Script
# This script deploys the landing pages microservice

set -e

echo "🚀 Starting GrainTrade Landing Service deployment..."

# Configuration
SERVICE_NAME="landing-service"
DOCKER_COMPOSE_FILE="docker-compose.yaml"
APACHE_CONF_SOURCE="apache_files/sites-available/home.graintrade.info.conf"
APACHE_CONF_TARGET="/etc/apache2/sites-available/home.graintrade.info.conf"
STATIC_FILES_TARGET="/var/www/html/landing"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for Apache configuration
check_permissions() {
    if [[ $EUID -ne 0 ]] && [[ "$1" == "apache" ]]; then
        log_error "Apache configuration requires root privileges. Run with sudo."
        exit 1
    fi
}

# Build and start the Docker service
deploy_docker_service() {
    log_info "Building and starting $SERVICE_NAME..."
    
    # Build the Docker image
    docker-compose -f $DOCKER_COMPOSE_FILE build $SERVICE_NAME
    
    # Start the service
    docker-compose -f $DOCKER_COMPOSE_FILE up -d $SERVICE_NAME
    
    # Wait for service to be healthy
    log_info "Waiting for service to be healthy..."
    timeout=60
    counter=0
    
    while [ $counter -lt $timeout ]; do
        if docker-compose -f $DOCKER_COMPOSE_FILE exec $SERVICE_NAME curl -f http://localhost:8003/health > /dev/null 2>&1; then
            log_info "Service is healthy!"
            break
        fi
        
        counter=$((counter + 1))
        sleep 1
    done
    
    if [ $counter -eq $timeout ]; then
        log_error "Service failed to become healthy within $timeout seconds"
        exit 1
    fi
}

# Configure Apache
configure_apache() {
    log_info "Configuring Apache..."
    
    # Copy Apache configuration
    cp "$APACHE_CONF_SOURCE" "$APACHE_CONF_TARGET"
    
    # Create static files directory
    mkdir -p "$STATIC_FILES_TARGET"
    
    # Copy static files
    docker cp $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q $SERVICE_NAME):/app/static "$STATIC_FILES_TARGET/"
    docker cp $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q $SERVICE_NAME):/app/robots.txt "$STATIC_FILES_TARGET/"
    docker cp $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q $SERVICE_NAME):/app/sitemap.xml "$STATIC_FILES_TARGET/"
    
    # Set proper permissions
    chown -R www-data:www-data "$STATIC_FILES_TARGET"
    chmod -R 755 "$STATIC_FILES_TARGET"
    
    # Enable required Apache modules
    a2enmod ssl
    a2enmod rewrite
    a2enmod headers
    a2enmod proxy
    a2enmod proxy_http
    a2enmod expires
    a2enmod deflate
    
    # Enable the site
    a2ensite home.graintrade.info.conf
    
    # Test Apache configuration
    apache2ctl configtest
    
    # Reload Apache
    systemctl reload apache2
    
    log_info "Apache configuration completed"
}

# Create backup
create_backup() {
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    log_info "Creating backup in $BACKUP_DIR..."
    
    # Backup current Docker images
    docker save graintrade_landing-service:latest | gzip > "$BACKUP_DIR/landing-service.tar.gz" 2>/dev/null || log_warn "No existing image to backup"
    
    # Backup Apache config
    if [ -f "$APACHE_CONF_TARGET" ]; then
        cp "$APACHE_CONF_TARGET" "$BACKUP_DIR/"
    fi
    
    # Backup static files
    if [ -d "$STATIC_FILES_TARGET" ]; then
        tar -czf "$BACKUP_DIR/static_files.tar.gz" -C "$(dirname $STATIC_FILES_TARGET)" "$(basename $STATIC_FILES_TARGET)"
    fi
    
    log_info "Backup created successfully"
}

# Rollback function
rollback() {
    log_warn "Rolling back deployment..."
    
    # Stop current service
    docker-compose -f $DOCKER_COMPOSE_FILE stop $SERVICE_NAME
    
    # Restore from latest backup
    LATEST_BACKUP=$(ls -1t backups/ 2>/dev/null | head -n1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        log_info "Restoring from backup: $LATEST_BACKUP"
        
        # Restore Docker image
        if [ -f "backups/$LATEST_BACKUP/landing-service.tar.gz" ]; then
            gunzip -c "backups/$LATEST_BACKUP/landing-service.tar.gz" | docker load
        fi
        
        # Restore Apache config
        if [ -f "backups/$LATEST_BACKUP/home.graintrade.info.conf" ]; then
            cp "backups/$LATEST_BACKUP/home.graintrade.info.conf" "$APACHE_CONF_TARGET"
            systemctl reload apache2
        fi
        
        # Start service
        docker-compose -f $DOCKER_COMPOSE_FILE start $SERVICE_NAME
        
        log_info "Rollback completed"
    else
        log_error "No backup found for rollback"
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check Docker service
    if ! docker-compose -f $DOCKER_COMPOSE_FILE exec $SERVICE_NAME curl -f http://localhost:8003/health > /dev/null 2>&1; then
        log_error "Docker service health check failed"
        return 1
    fi
    
    # Check external access (if Apache is configured)
    if command -v curl > /dev/null 2>&1; then
        if curl -f https://home.graintrade.info/health > /dev/null 2>&1; then
            log_info "External health check passed"
        else
            log_warn "External health check failed (this is normal if Apache is not configured yet)"
        fi
    fi
    
    log_info "Health check completed successfully"
}

# Update function
update_service() {
    log_info "Updating $SERVICE_NAME..."
    
    create_backup
    
    # Pull latest changes
    git pull origin develop
    
    # Rebuild and restart
    docker-compose -f $DOCKER_COMPOSE_FILE build $SERVICE_NAME
    docker-compose -f $DOCKER_COMPOSE_FILE up -d $SERVICE_NAME
    
    # Update static files if Apache is configured
    if [ -d "$STATIC_FILES_TARGET" ]; then
        log_info "Updating static files..."
        docker cp $(docker-compose -f $DOCKER_COMPOSE_FILE ps -q $SERVICE_NAME):/app/static "$STATIC_FILES_TARGET/"
        chown -R www-data:www-data "$STATIC_FILES_TARGET"
    fi
    
    health_check
    
    log_info "Update completed successfully"
}

# Main deployment logic
main() {
    case "${1:-deploy}" in
        "deploy")
            create_backup
            deploy_docker_service
            health_check
            log_info "Deployment completed successfully!"
            echo ""
            log_info "Next steps:"
            echo "1. Run './deploy-landing.sh apache' as root to configure Apache"
            echo "2. Verify the service at https://home.graintrade.info"
            ;;
        "apache")
            check_permissions "apache"
            configure_apache
            health_check
            log_info "Apache configuration completed successfully!"
            ;;
        "update")
            update_service
            ;;
        "rollback")
            rollback
            ;;
        "health")
            health_check
            ;;
        "stop")
            log_info "Stopping $SERVICE_NAME..."
            docker-compose -f $DOCKER_COMPOSE_FILE stop $SERVICE_NAME
            ;;
        "start")
            log_info "Starting $SERVICE_NAME..."
            docker-compose -f $DOCKER_COMPOSE_FILE start $SERVICE_NAME
            health_check
            ;;
        "restart")
            log_info "Restarting $SERVICE_NAME..."
            docker-compose -f $DOCKER_COMPOSE_FILE restart $SERVICE_NAME
            health_check
            ;;
        "logs")
            docker-compose -f $DOCKER_COMPOSE_FILE logs -f $SERVICE_NAME
            ;;
        *)
            echo "Usage: $0 {deploy|apache|update|rollback|health|stop|start|restart|logs}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Deploy the Docker service (default)"
            echo "  apache   - Configure Apache (requires sudo)"
            echo "  update   - Update the service with latest changes"
            echo "  rollback - Rollback to previous version"
            echo "  health   - Check service health"
            echo "  stop     - Stop the service"
            echo "  start    - Start the service"
            echo "  restart  - Restart the service"
            echo "  logs     - Show service logs"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"