#!/bin/bash

# MenuMind AI Deployment Script

set -e

echo "🚀 Starting MenuMind AI Deployment..."

# Check if production environment file exists
if [ ! -f .env.production ]; then
    echo "❌ .env.production file not found!"
    exit 1
fi

# Load environment variables
export $(cat .env.production | xargs)

echo "📦 Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "🔄 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

echo "🗄️ Starting database..."
docker-compose -f docker-compose.prod.yml up -d db redis
sleep 10

echo "🔨 Running migrations..."
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py migrate

echo "📁 Collecting static files..."
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py collectstatic --noinput

echo "🌱 Seeding initial data..."
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py seed_data

echo "🚀 Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Deployment complete!"
echo "🌐 Application is running at http://localhost"
echo "📊 Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
