#!/bin/bash

# BishulMe Development Startup Script for WSL2
# This script starts the development environment with hot reload

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}???????????????????????????????????????????????????????????????${NC}"
echo -e "${GREEN}  ?? BishulMe Development Environment (WSL2)${NC}"
echo -e "${GREEN}???????????????????????????????????????????????????????????????${NC}"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}? Docker is not running!${NC}"
    echo -e "${YELLOW}Please start Docker Desktop in Windows${NC}"
    exit 1
fi

echo -e "${CYAN}? Docker is running${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}??  .env file not found!${NC}"
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cat > .env << 'EOF'
# Database
DB_NAME=menumindai
DB_USER=postgres
DB_PASSWORD=MenuMind2025!SecureDB

# Redis
REDIS_URL=redis://redis:6379/0

# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,backend
CORS_ALLOWED_ORIGINS=http://localhost,http://localhost:3000,http://localhost:80

# Mailjet
MAILJET_API_KEY=7fddcffd9c674043d468c076f6b3f399
MAILJET_SECRET_KEY=63cad8b87cd6be051280f3fa1e5c3c41
MAILJET_SENDER_EMAIL=bishulme@gmail.com
MAILJET_SENDER_NAME=BishulSheli
MAILJET_TEMPLATE_VERIFY_EN=7459709
MAILJET_TEMPLATE_VERIFY_RU=7459713
MAILJET_TEMPLATE_VERIFY_HE=7459704

# Google OAuth
REACT_APP_GOOGLE_CLIENT_ID=819829561375-19d74oa53gsn83r0qaaavb0659hsegqo.apps.googleusercontent.com
EOF
    echo -e "${GREEN}? .env file created${NC}"
fi

# Check if containers are already running
if docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo ""
    echo -e "${YELLOW}??  Containers are already running${NC}"
    read -p "Do you want to restart them? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Restarting containers...${NC}"
        docker compose -f docker-compose.dev.yml restart
    fi
else
    echo ""
    echo -e "${CYAN}Starting development environment...${NC}"
    echo -e "${YELLOW}(First time may take 2-3 minutes to build images)${NC}"
    echo ""
    
    docker compose -f docker-compose.dev.yml up -d
    
    echo ""
    echo -e "${CYAN}Waiting for services to be healthy...${NC}"
    sleep 10
fi

# Wait for database to be fully ready
echo ""
echo -e "${CYAN}Waiting for database to be ready...${NC}"
sleep 5

# Run migrations
echo ""
echo -e "${CYAN}Running database migrations...${NC}"
docker compose -f docker-compose.dev.yml exec -T backend python manage.py migrate --noinput
echo -e "${GREEN}✅ Migrations applied${NC}"

# Check service status
echo ""
echo -e "${CYAN}📊 Service Status:${NC}"
docker compose -f docker-compose.dev.yml ps

echo ""
echo -e "${GREEN}???????????????????????????????????????????????????????????????${NC}"
echo -e "${GREEN}  ? Development Environment is Running!${NC}"
echo -e "${GREEN}???????????????????????????????????????????????????????????????${NC}"
echo ""
echo -e "${CYAN}?? Access Points:${NC}"
echo -e "   Frontend:   ${YELLOW}http://localhost:3000${NC}"
echo -e "   Backend:    ${YELLOW}http://localhost:8000${NC}"
echo -e "   Admin:      ${YELLOW}http://localhost:8000/admin/${NC}"
echo -e "   WebSocket:  ${YELLOW}ws://localhost:8001${NC}"
echo ""
echo -e "${CYAN}?? Hot Reload Enabled:${NC}"
echo -e "   ? Edit ${YELLOW}backend/${NC} files ? Django auto-reloads"
echo -e "   ? Edit ${YELLOW}frontend/${NC} files ? React auto-reloads"
echo -e "   ? ${GREEN}No rebuild needed!${NC}"
echo ""
echo -e "${CYAN}?? Useful Commands:${NC}"
echo -e "   View logs:        ${YELLOW}docker compose -f docker-compose.dev.yml logs -f${NC}"
echo -e "   Django shell:     ${YELLOW}docker compose -f docker-compose.dev.yml exec backend python manage.py shell${NC}"
echo -e "   Stop services:    ${YELLOW}docker compose -f docker-compose.dev.yml down${NC}"
echo -e "   Restart service:  ${YELLOW}docker compose -f docker-compose.dev.yml restart <service>${NC}"
echo ""
echo -e "${CYAN}?? VSCode:${NC}"
echo -e "   Open in WSL:      ${YELLOW}code .${NC}"
echo ""
echo -e "${GREEN}Happy coding! ??${NC}"
echo ""


