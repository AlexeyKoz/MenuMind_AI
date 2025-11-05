#!/bin/bash
# MenuMind AI - Docker Production Helper Script
# Quick commands for working with Docker in production mode

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

COMPOSE_FILE="docker-compose.prod.yml"

print_header() {
    echo ""
    echo "===================================="
    echo " MenuMind AI - Production Manager"
    echo "===================================="
    echo ""
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[*]${NC} $1"
}

start_production() {
    print_info "Starting production stack..."
    echo ""
    
    if docker compose -f "$COMPOSE_FILE" up -d; then
        echo ""
        print_success "Production stack started!"
        echo ""
        echo "Services:"
        docker compose -f "$COMPOSE_FILE" ps
        echo ""
    else
        print_error "Failed to start production stack!"
        exit 1
    fi
}

stop_production() {
    echo ""
    echo -e "${YELLOW}[WARNING]${NC} This will stop all production services!"
    echo ""
    read -p "Are you sure? (y/n): " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    
    print_info "Stopping production stack..."
    echo ""
    
    if docker compose -f "$COMPOSE_FILE" down; then
        echo ""
        print_success "Production stack stopped!"
        echo ""
    else
        print_error "Failed to stop production stack!"
        exit 1
    fi
}

restart_services() {
    print_info "Restarting production services..."
    echo ""
    
    if docker compose -f "$COMPOSE_FILE" restart; then
        echo ""
        print_success "Services restarted!"
        echo ""
    else
        print_error "Failed to restart services!"
        exit 1
    fi
}

view_logs() {
    print_info "Production logs (Ctrl+C to exit)..."
    echo ""
    docker compose -f "$COMPOSE_FILE" logs -f --tail=100
}

rebuild_containers() {
    print_info "Rebuilding production containers..."
    echo ""
    
    if docker compose -f "$COMPOSE_FILE" build --no-cache; then
        echo ""
        print_success "Production containers rebuilt!"
        echo ""
        echo "To deploy: ./docker-prod.sh start"
        echo ""
    else
        print_error "Failed to rebuild!"
        exit 1
    fi
}

check_status() {
    print_info "Production service status..."
    echo ""
    
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "Docker resources:"
    docker stats --no-stream
    echo ""
}

backup_database() {
    print_info "Backing up database..."
    echo ""
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backupfile="backup_${timestamp}.sql"
    
    echo "Backup file: $backupfile"
    echo ""
    
    if docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U postgres menumine_ai > "$backupfile"; then
        echo ""
        print_success "Database backed up to: $backupfile"
        echo ""
        
        # Compress backup
        gzip "$backupfile"
        print_info "Compressed to: ${backupfile}.gz"
        echo ""
    else
        print_error "Backup failed!"
        exit 1
    fi
}

check_health() {
    print_info "Checking service health..."
    echo ""
    
    for service in backend celery celery-beat daphne frontend; do
        echo "Checking $service..."
        container="menumine_${service}_prod"
        
        if docker inspect "$container" &>/dev/null; then
            status=$(docker inspect "$container" --format='{{.State.Status}}')
            health=$(docker inspect "$container" --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no healthcheck{{end}}')
            echo "Status: $status | Health: $health"
        else
            echo "$container: NOT RUNNING"
        fi
        echo ""
    done
}

deploy_production() {
    print_info "Deploying production stack..."
    echo ""
    
    # Pull latest code
    print_info "Pulling latest code from Git..."
    git pull origin main
    
    # Rebuild containers
    print_info "Rebuilding containers..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    
    # Stop old containers
    print_info "Stopping old containers..."
    docker compose -f "$COMPOSE_FILE" down
    
    # Start new containers
    print_info "Starting new containers..."
    docker compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check status
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    print_success "Production deployment complete!"
    echo ""
}

show_help() {
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start production stack"
    echo "  stop      - Stop production stack"
    echo "  restart   - Restart services"
    echo "  logs      - View logs"
    echo "  build     - Rebuild containers"
    echo "  status    - Check service status"
    echo "  backup    - Backup database"
    echo "  health    - Check service health"
    echo "  deploy    - Full deployment (git pull + rebuild + restart)"
    echo "  help      - Show this help"
    echo ""
    echo "No command runs interactive menu."
    echo ""
}

show_menu() {
    print_header
    echo "Choose an option:"
    echo ""
    echo "[1] Start production stack"
    echo "[2] Stop production stack"
    echo "[3] Restart services"
    echo "[4] View logs"
    echo "[5] Rebuild containers"
    echo "[6] Check status"
    echo "[7] Backup database"
    echo "[8] View service health"
    echo "[9] Full deployment"
    echo "[0] Exit"
    echo ""
    read -p "Enter your choice: " choice
    
    case $choice in
        1) start_production ;;
        2) stop_production ;;
        3) restart_services ;;
        4) view_logs ;;
        5) rebuild_containers ;;
        6) check_status ;;
        7) backup_database ;;
        8) check_health ;;
        9) deploy_production ;;
        0) exit 0 ;;
        *) echo "Invalid choice"; show_menu ;;
    esac
}

# Main script logic
case "${1:-}" in
    start) start_production ;;
    stop) stop_production ;;
    restart) restart_services ;;
    logs) view_logs ;;
    build) rebuild_containers ;;
    status) check_status ;;
    backup) backup_database ;;
    health) check_health ;;
    deploy) deploy_production ;;
    help) show_help ;;
    "") show_menu ;;
    *) 
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac


