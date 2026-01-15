#!/bin/bash

# Video Studio Deployment Script
# Usage: ./deploy.sh [command]

set -e

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="video-studio"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env exists
check_env() {
    if [ ! -f ".env" ]; then
        log_warn ".env file not found. Creating from template..."
        cp .env.example .env
        log_info "Please edit .env with your configuration before deploying."
        exit 1
    fi
}

# Build images
build() {
    log_info "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    log_info "Build complete!"
}

# Start services
start() {
    check_env
    log_info "Starting Video Studio services..."
    docker-compose -f $COMPOSE_FILE up -d
    log_info "Services started!"
    log_info "Frontend: Check your PUBLIC_BASE_URL"
    log_info "API Docs: \${PUBLIC_BASE_URL}/api/docs"
}

# Stop services
stop() {
    log_info "Stopping Video Studio services..."
    docker-compose -f $COMPOSE_FILE down
    log_info "Services stopped!"
}

# Restart services
restart() {
    stop
    start
}

# View logs
logs() {
    docker-compose -f $COMPOSE_FILE logs -f "${@:2}"
}

# Check status
status() {
    docker-compose -f $COMPOSE_FILE ps
}

# Run database migrations
migrate() {
    log_info "Running database migrations..."
    docker-compose -f $COMPOSE_FILE exec video-studio-api alembic upgrade head
    log_info "Migrations complete!"
}

# Backup database
backup() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "Creating database backup: $BACKUP_FILE"
    docker-compose -f $COMPOSE_FILE exec -T video-studio-db \
        pg_dump -U video_studio video_studio > "$BACKUP_FILE"
    log_info "Backup saved to $BACKUP_FILE"
}

# Restore database
restore() {
    if [ -z "$2" ]; then
        log_error "Please provide backup file: ./deploy.sh restore backup.sql"
        exit 1
    fi
    log_warn "This will overwrite the current database. Continue? (y/N)"
    read -r confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        log_info "Restoring database from $2..."
        docker-compose -f $COMPOSE_FILE exec -T video-studio-db \
            psql -U video_studio video_studio < "$2"
        log_info "Restore complete!"
    fi
}

# Shell into container
shell() {
    SERVICE="${2:-video-studio-api}"
    log_info "Opening shell in $SERVICE..."
    docker-compose -f $COMPOSE_FILE exec "$SERVICE" /bin/sh
}

# Clean up
clean() {
    log_warn "This will remove all containers, volumes, and images. Continue? (y/N)"
    read -r confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        log_info "Cleaning up..."
        docker-compose -f $COMPOSE_FILE down -v --rmi all
        log_info "Cleanup complete!"
    fi
}

# Update (pull & restart)
update() {
    log_info "Updating Video Studio..."
    git pull
    build
    restart
    log_info "Update complete!"
}

# Help
help() {
    echo "Video Studio Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build     Build Docker images"
    echo "  start     Start all services"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  logs      View logs (optionally specify service)"
    echo "  status    Check service status"
    echo "  migrate   Run database migrations"
    echo "  backup    Backup database"
    echo "  restore   Restore database from file"
    echo "  shell     Open shell in container"
    echo "  clean     Remove all containers and volumes"
    echo "  update    Pull latest and restart"
    echo "  help      Show this help"
}

# Main
case "${1:-help}" in
    build)   build ;;
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    logs)    logs "$@" ;;
    status)  status ;;
    migrate) migrate ;;
    backup)  backup ;;
    restore) restore "$@" ;;
    shell)   shell "$@" ;;
    clean)   clean ;;
    update)  update ;;
    help)    help ;;
    *)
        log_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
