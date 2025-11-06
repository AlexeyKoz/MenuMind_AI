#!/bin/bash
# Production Deployment Script for MenuMind AI (BishulMe)
# Usage: ./deploy-to-production.sh

set -e  # Exit on error

echo "🚀 MenuMind AI (BishulMe) - Production Deployment"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on server
if [[ ! -f "/opt/menumine/docker-compose.prod.yml" ]]; then
    echo -e "${RED}❌ Error: This script must be run on the production server${NC}"
    echo "Files should be in /opt/menumine/"
    exit 1
fi

cd /opt/menumine

# Check if .env exists
if [[ ! -f "backend/.env" ]]; then
    echo -e "${RED}❌ Error: backend/.env not found${NC}"
    echo "Please create backend/.env with production settings"
    exit 1
fi

echo "✅ Pre-deployment checks passed"
echo ""

# Step 1: Pull base images
echo "📦 Step 1/7: Pulling base Docker images..."
docker compose -f docker-compose.prod.yml pull

# Step 2: Build custom images
echo ""
echo "🔨 Step 2/7: Building application images..."
docker compose -f docker-compose.prod.yml build --no-cache

# Step 3: Stop old containers
echo ""
echo "🛑 Step 3/7: Stopping old containers..."
docker compose -f docker-compose.prod.yml down

# Step 4: Start new containers
echo ""
echo "▶️  Step 4/7: Starting new containers..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Step 5: Run migrations
echo ""
echo "🗄️  Step 5/7: Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

# Step 6: Collect static files
echo ""
echo "📁 Step 6/7: Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

# Step 7: Load initial data (only if database is empty)
echo ""
echo "📚 Step 7/7: Loading initial data..."

# Check if data already exists
LEGAL_COUNT=$(docker compose -f docker-compose.prod.yml exec -T backend python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()
from legal.models import LegalDocument
print(LegalDocument.objects.count())
" 2>/dev/null | tr -d '\r')

if [[ "$LEGAL_COUNT" -eq "0" ]]; then
    echo "📄 Loading legal documents..."
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py load_bishulsheli_docs
    
    echo "📝 Loading About Us pages..."
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py load_about_pages
    
    echo "🥕 Importing IML ingredients..."
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py import_iml_json
    
    echo "👨‍🍳 Importing CookLingo terms..."
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py import_cooklingo_json
else
    echo "✅ Initial data already loaded (skipping)"
fi

# Check deployment status
echo ""
echo "🔍 Checking deployment status..."
echo ""

docker compose -f docker-compose.prod.yml ps

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo "=================================================="
echo ""
echo "📊 Next Steps:"
echo "  1. Check logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  2. Test frontend: http://your-server-ip/"
echo "  3. Test API: http://your-server-ip:8000/api/"
echo "  4. Access admin: http://your-server-ip:8000/admin/"
echo ""
echo "⚠️  Don't forget to:"
echo "  - Create superuser: docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
echo "  - Upload logos in admin panel"
echo "  - Configure SSL/HTTPS"
echo "  - Update Google OAuth URLs"
echo ""

