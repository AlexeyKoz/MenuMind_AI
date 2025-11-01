# Quick Start Script for Production Deployment (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "MenuMine AI - Production Deployment" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker and Docker Compose are installed" -ForegroundColor Green
Write-Host ""

# Check if .env file exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "⚠️  backend\.env not found. Please create it from backend\.env.example" -ForegroundColor Yellow
    Write-Host "   Required variables:"
    Write-Host "   - SECRET_KEY (generate a new one)"
    Write-Host "   - DB_PASSWORD (choose a secure password)"
    Write-Host "   - OPENAI_API_KEY (your OpenAI API key)"
    Write-Host ""
    $reply = Read-Host "Do you want to continue anyway? (y/N)"
    if ($reply -notmatch "^[Yy]$") {
        exit 1
    }
}

# Build images
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Step 1: Building Docker images..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml build

Write-Host ""
Write-Host "✅ Images built successfully" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Step 2: Starting services..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml up -d

Write-Host ""
Write-Host "✅ Services started" -ForegroundColor Green
Write-Host ""

# Wait for database to be ready
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Step 3: Waiting for database to be ready..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Run migrations
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Step 4: Running database migrations..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

Write-Host ""
Write-Host "✅ Migrations completed" -ForegroundColor Green
Write-Host ""

# Collect static files
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Step 5: Collecting static files..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

Write-Host ""
Write-Host "✅ Static files collected" -ForegroundColor Green
Write-Host ""

# Check service health
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Step 6: Checking service health..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your MenuMine AI application is now running!" -ForegroundColor Green
Write-Host ""
Write-Host "Access points:"
Write-Host "  - Frontend:    http://localhost"
Write-Host "  - Backend API: http://localhost:8000"
Write-Host "  - Admin:       http://localhost:8000/admin/"
Write-Host ""
Write-Host "Pre-loaded content:"
Write-Host "  - 83 canonical recipes"
Write-Host "  - 652 ingredients"
Write-Host "  - 892 preparation steps"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Create a superuser:"
Write-Host "     docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
Write-Host ""
Write-Host "  2. Import IML data (optional):"
Write-Host "     docker-compose -f docker-compose.prod.yml exec backend python manage.py import_iml"
Write-Host ""
Write-Host "  3. Import CookLingo data (optional):"
Write-Host "     docker-compose -f docker-compose.prod.yml exec backend python manage.py import_cooklingo"
Write-Host ""
Write-Host "View logs:"
Write-Host "  docker-compose -f docker-compose.prod.yml logs -f"
Write-Host ""
Write-Host "Stop services:"
Write-Host "  docker-compose -f docker-compose.prod.yml down"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan

