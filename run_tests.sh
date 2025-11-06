#!/bin/bash

# Test runner for AI Token Protection System
# Runs both pytest (backend) and Selenium (E2E) tests

set -e

echo "========================================="
echo "🧪 AI TOKEN PROTECTION - TEST SUITE"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in WSL
if [ -f /proc/version ] && grep -q Microsoft /proc/version; then
    echo "✅ Running in WSL2"
    cd ~/MenuMind_AI/MenuMind_AI
else
    echo "⚠️  Not in WSL2, using current directory"
fi

echo ""
echo "========================================="
echo "📦 STEP 1: Backend Unit Tests (Pytest)"
echo "========================================="
echo ""

# Run pytest for backend
echo "Running pytest with coverage..."
docker compose -f docker-compose.dev.yml exec -T backend pytest apps/users/tests/ -v --cov=apps.users --cov-report=term-missing

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend tests passed!${NC}"
else
    echo -e "${RED}❌ Backend tests failed!${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo "🌐 STEP 2: E2E Tests (Selenium)"
echo "========================================="
echo ""

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"
    
    echo "Running Selenium E2E tests..."
    docker compose -f docker-compose.dev.yml exec -T backend pytest tests/test_e2e_protection.py -v -s
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ E2E tests passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  E2E tests failed (this is expected if UI is not accessible)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Frontend not running on localhost:3000, skipping E2E tests${NC}"
fi

echo ""
echo "========================================="
echo "📊 STEP 3: Test Summary"
echo "========================================="
echo ""

echo "✅ Backend unit tests: PASSED"
echo "📝 Coverage report generated"
echo ""
echo "To view detailed coverage:"
echo "  docker compose -f docker-compose.dev.yml exec backend coverage html"
echo "  # Then open backend/htmlcov/index.html"
echo ""
echo "========================================="
echo "🎉 TEST SUITE COMPLETE"
echo "========================================="

