#!/bin/bash
# DigitalOcean Quick Deployment Script
# Run this on your DigitalOcean droplet after cloning the repository

set -e  # Exit on error

echo "========================================"
echo "MenuMine AI - DigitalOcean Deployment"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}Warning: Running as root. Consider creating a non-root user.${NC}"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed!${NC}"
    echo "Please install Docker first:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose first:"
    echo "  apt install docker-compose -y"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env file not found!${NC}"
    echo ""
    echo "Creating backend/.env from template..."
    
    if [ -f "ENV.digitalocean.example" ]; then
        cp ENV.digitalocean.example backend/.env
        echo -e "${GREEN}✓${NC} Created backend/.env"
        echo ""
        echo -e "${YELLOW}IMPORTANT: Edit backend/.env and update the following:${NC}"
        echo "  - DB_PASSWORD"
        echo "  - SECRET_KEY"
        echo "  - ALLOWED_HOSTS"
        echo "  - FRONTEND_API_URL"
        echo "  - FRONTEND_WS_URL"
        echo "  - CORS_ALLOWED_ORIGINS"
        echo "  - GOOGLE_CLIENT_SECRET"
        echo ""
        echo "Run: nano backend/.env"
        echo ""
        read -p "Press Enter after editing backend/.env to continue..."
    else
        echo -e "${RED}Error: ENV.digitalocean.example not found!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Environment file exists"
echo ""

# Get droplet IP
DROPLET_IP=$(curl -s ifconfig.me)
echo "Your Droplet IP: ${DROPLET_IP}"
echo ""

# Ask for confirmation
echo "This script will:"
echo "  1. Build Docker images (takes 5-10 minutes)"
echo "  2. Start all services"
echo "  3. Run database migrations"
echo "  4. Create necessary data directories"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "========================================"
echo "Step 1: Creating data directories"
echo "========================================"
mkdir -p backend/data
mkdir -p backend/media
mkdir -p backups
echo -e "${GREEN}✓${NC} Directories created"
echo ""

echo "========================================"
echo "Step 2: Building Docker images"
echo "========================================"
echo "This may take 5-10 minutes..."
docker-compose -f docker-compose.digitalocean.yml build
echo -e "${GREEN}✓${NC} Images built successfully"
echo ""

echo "========================================"
echo "Step 3: Starting services"
echo "========================================"
docker-compose -f docker-compose.digitalocean.yml up -d
echo -e "${GREEN}✓${NC} Services started"
echo ""

echo "Waiting for database to be ready..."
sleep 10

echo "========================================"
echo "Step 4: Running database migrations"
echo "========================================"
docker exec menumine_backend python manage.py migrate
echo -e "${GREEN}✓${NC} Migrations completed"
echo ""

echo "========================================"
echo "Step 5: Checking service status"
echo "========================================"
docker-compose -f docker-compose.digitalocean.yml ps
echo ""

echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "Your application is now running at:"
echo ""
echo "  Frontend:      http://${DROPLET_IP}"
echo "  Backend API:   http://${DROPLET_IP}:8000/api/"
echo "  Admin Panel:   http://${DROPLET_IP}:8000/admin/"
echo ""
echo "Next steps:"
echo "  1. Create a superuser: docker exec -it menumine_backend python manage.py createsuperuser"
echo "  2. Import data (if you have exports): See DIGITALOCEAN_DEPLOYMENT.md Step 6"
echo "  3. Configure Google OAuth redirect URIs (see deployment guide)"
echo "  4. Test your application in the browser"
echo ""
echo "To view logs: docker-compose -f docker-compose.digitalocean.yml logs -f"
echo "To stop: docker-compose -f docker-compose.digitalocean.yml down"
echo ""
echo -e "${GREEN}Happy cooking! 🍳${NC}"

