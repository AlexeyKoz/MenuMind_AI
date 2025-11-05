#!/bin/bash
# MenuMind AI - Docker Development Helper Script
# Quick commands for working with Docker in development mode

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "===================================="
    echo "  MenuMind AI - Docker Manager"
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

start_services() {
    print_info "Starting all services in development mode..."
    echo ""
    
    if docker compose up -d; then
        echo ""
        print_success "All services started!"
        echo ""
        echo "Services available at:"
        echo "- Frontend:  http://localhost:3000"
        echo "- Backend:   http://localhost:8000"
        echo "- Admin:     http://localhost:8000/admin"
        echo "- Database:  localhost:5432"
        echo "- Redis:     localhost:6379"
        echo ""
        echo "Run: docker compose logs -f"
        echo "To view real-time logs"
        echo ""
    else
        print_error "Failed to start services!"
        exit 1
    fi
}

stop_services() {
    print_info "Stopping all services..."
    echo ""
    
    if docker compose down; then
        echo ""
        print_success "All services stopped!"
        echo ""
    else
        print_error "Failed to stop services!"
        exit 1
    fi
}

restart_services() {
    print_info "Restarting all services..."
    echo ""
    
    if docker compose restart; then
        echo ""
        print_success "All services restarted!"
        echo ""
    else
        print_error "Failed to restart services!"
        exit 1
    fi
}

view_logs() {
    print_info "Showing logs (Ctrl+C to exit)..."
    echo ""
    docker compose logs -f --tail=100
}

rebuild_containers() {
    print_info "Rebuilding all containers..."
    echo ""
    
    docker compose down
    
    if docker compose build --no-cache && docker compose up -d; then
        echo ""
        print_success "All containers rebuilt and started!"
        echo ""
    else
        print_error "Failed to rebuild!"
        exit 1
    fi
}

check_status() {
    print_info "Checking service status..."
    echo ""
    
    docker compose ps
    
    echo ""
    echo "Docker resources:"
    docker stats --no-stream
    echo ""
}

access_shell() {
    print_info "Accessing backend shell..."
    print_info "Type 'exit' to return"
    echo ""
    docker compose exec backend bash
}

access_db() {
    print_info "Accessing PostgreSQL database..."
    print_info "Type '\\q' to exit"
    echo ""
    docker compose exec db psql -U postgres -d menumine_ai
}

clean_docker() {
    echo ""
    echo -e "${YELLOW}[WARNING]${NC} This will remove all stopped containers, unused networks, and dangling images!"
    echo ""
    read -p "Are you sure? (y/n): " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    
    print_info "Cleaning up Docker..."
    echo ""
    
    docker system prune -f
    
    echo ""
    print_success "Docker cleanup complete!"
    echo ""
}

show_help() {
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  logs      - View logs"
    echo "  build     - Rebuild containers"
    echo "  status    - Check service status"
    echo "  shell     - Access backend shell"
    echo "  db        - Access database"
    echo "  clean     - Clean up Docker"
    echo "  help      - Show this help"
    echo ""
    echo "No command runs interactive menu."
    echo ""
}

show_menu() {
    print_header
    echo "Choose an option:"
    echo ""
    echo "[1] Start all services (dev mode)"
    echo "[2] Stop all services"
    echo "[3] Restart all services"
    echo "[4] View logs"
    echo "[5] Rebuild containers"
    echo "[6] Check status"
    echo "[7] Access backend shell"
    echo "[8] Access database"
    echo "[9] Clean up Docker"
    echo "[0] Exit"
    echo ""
    read -p "Enter your choice: " choice
    
    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) view_logs ;;
        5) rebuild_containers ;;
        6) check_status ;;
        7) access_shell ;;
        8) access_db ;;
        9) clean_docker ;;
        0) exit 0 ;;
        *) echo "Invalid choice"; show_menu ;;
    esac
}

# Main script logic
case "${1:-}" in
    start) start_services ;;
    stop) stop_services ;;
    restart) restart_services ;;
    logs) view_logs ;;
    build) rebuild_containers ;;
    status) check_status ;;
    shell) access_shell ;;
    db) access_db ;;
    clean) clean_docker ;;
    help) show_help ;;
    "") show_menu ;;
    *) 
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac


