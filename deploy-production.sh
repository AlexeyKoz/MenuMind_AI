#!/bin/bash
# Quick Start Script for Production Deployment

set -e

echo "================================================================================"
echo "MenuMine AI - Production Deployment"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  backend/.env not found. Please create it from backend/.env.example${NC}"
    echo "   Required variables:"
    echo "   - SECRET_KEY (generate a new one)"
    echo "   - DB_PASSWORD (choose a secure password)"
    echo "   - OPENAI_API_KEY (your OpenAI API key)"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build images
echo "================================================================================"
echo "Step 1: Building Docker images..."
echo "================================================================================"
docker-compose -f docker-compose.prod.yml build

echo ""
echo -e "${GREEN}✅ Images built successfully${NC}"
echo ""

# Start services
echo "================================================================================"
echo "Step 2: Starting services..."
echo "================================================================================"
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Wait for database to be ready
echo "================================================================================"
echo "Step 3: Waiting for database to be ready..."
echo "================================================================================"
sleep 5

# Run migrations
echo "================================================================================"
echo "Step 4: Running database migrations..."
echo "================================================================================"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

echo ""
echo -e "${GREEN}✅ Migrations completed${NC}"
echo ""

# Collect static files
echo "================================================================================"
echo "Step 5: Collecting static files..."
echo "================================================================================"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

echo ""
echo -e "${GREEN}✅ Static files collected${NC}"
echo ""

# Check service health
echo "================================================================================"
echo "Step 6: Checking service health..."
echo "================================================================================"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "================================================================================"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "================================================================================"
echo ""
echo "Your MenuMine AI application is now running!"
echo ""
echo "Access points:"
echo "  - Frontend:    http://localhost"
echo "  - Backend API: http://localhost:8000"
echo "  - Admin:       http://localhost:8000/admin/"
echo ""
echo "Pre-loaded content:"
echo "  - 83 canonical recipes"
echo "  - 652 ingredients"
echo "  - 892 preparation steps"
echo ""
echo "Next steps:"
echo "  1. Create a superuser:"
echo "     docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
echo ""
echo "  2. Import IML data (optional):"
echo "     docker-compose -f docker-compose.prod.yml exec backend python manage.py import_iml"
echo ""
echo "  3. Import CookLingo data (optional):"
echo "     docker-compose -f docker-compose.prod.yml exec backend python manage.py import_cooklingo"
echo ""
echo "View logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
echo "================================================================================"

