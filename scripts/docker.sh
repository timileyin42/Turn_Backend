#!/bin/bash

# TURN Docker Management Scripts
# Usage: ./scripts/docker.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Development environment
dev() {
    print_info "Starting development environment..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile development up -d
    print_success "Development environment started!"
    print_info "API: http://localhost:8000"
    print_info "Docs: http://localhost:8000/docs"
    print_info "pgAdmin: http://localhost:5050 (admin@turn.com / admin123)"
    print_info "Redis Commander: http://localhost:8081"
}

# Production environment
prod() {
    print_info "Starting production environment..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
    print_success "Production environment started!"
    print_info "API: http://localhost:80"
}

# Stop all services
stop() {
    print_info "Stopping all services..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml down
    print_success "All services stopped!"
}

# Clean up containers, volumes, and images
clean() {
    print_warning "This will remove all TURN containers, volumes, and images. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Cleaning up Docker resources..."
        
        # Stop and remove containers
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml down -v --remove-orphans
        
        # Remove images
        docker images | grep turn_ | awk '{print $3}' | xargs -r docker rmi -f
        
        # Remove volumes
        docker volume ls | grep turn_ | awk '{print $2}' | xargs -r docker volume rm
        
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled."
    fi
}

# View logs
logs() {
    service=${2:-app}
    print_info "Showing logs for service: $service"
    docker-compose logs -f "$service"
}

# Database operations
db_migrate() {
    print_info "Running database migrations..."
    docker-compose exec app alembic upgrade head
    print_success "Database migrations completed!"
}

db_reset() {
    print_warning "This will reset the database. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Resetting database..."
        docker-compose exec app python init_db.py drop
        docker-compose exec app python init_db.py create
        docker-compose exec app alembic upgrade head
        print_success "Database reset completed!"
    else
        print_info "Database reset cancelled."
    fi
}

# Build and push to registry (for production)
build() {
    print_info "Building TURN application image..."
    docker build -t turn-backend:latest .
    print_success "Build completed!"
}

# Health check
health() {
    print_info "Checking service health..."
    
    services=("app" "db" "redis")
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "${service}.*Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
        fi
    done
}

# Show status
status() {
    print_info "Docker Compose Status:"
    docker-compose ps
    
    print_info "\nDocker Images:"
    docker images | grep -E "(turn_|postgres|redis|nginx)"
    
    print_info "\nDocker Volumes:"
    docker volume ls | grep turn_
}

# Execute command in container
exec_app() {
    shift
    docker-compose exec app "$@"
}

# Show help
show_help() {
    echo "TURN Docker Management Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  dev          Start development environment with hot reload"
    echo "  prod         Start production environment"
    echo "  stop         Stop all services"
    echo "  clean        Remove all containers, volumes, and images"
    echo "  logs [service] Show logs for service (default: app)"
    echo "  db-migrate   Run database migrations"
    echo "  db-reset     Reset database (drop and recreate)"
    echo "  build        Build application image"
    echo "  health       Check service health"
    echo "  status       Show status of all services"
    echo "  exec [cmd]   Execute command in app container"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Start development environment"
    echo "  $0 logs app               # Show app logs"
    echo "  $0 exec python manage.py  # Run command in container"
}

# Main script logic
main() {
    check_docker
    
    case ${1:-help} in
        dev)
            dev
            ;;
        prod)
            prod
            ;;
        stop)
            stop
            ;;
        clean)
            clean
            ;;
        logs)
            logs "$@"
            ;;
        db-migrate)
            db_migrate
            ;;
        db-reset)
            db_reset
            ;;
        build)
            build
            ;;
        health)
            health
            ;;
        status)
            status
            ;;
        exec)
            exec_app "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"