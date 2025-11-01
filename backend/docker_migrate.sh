#!/bin/bash
# Run Django migrations inside Docker container
# This avoids Windows encoding issues

echo "================================================================================"
echo "[MIGRATE] Running PostgreSQL migrations via Docker"
echo "================================================================================"
echo ""

# Set environment variables
export USE_POSTGRES=True
export DB_NAME=menumine_ai
export DB_USER=postgres
export DB_PASSWORD=password
export DB_HOST=db
export DB_PORT=5432
export DEBUG=True
export SECRET_KEY="8e-33bn)r_2=nsu%mhr7-*x\$6jm#svuc#cwog2@5c@398on\$bq"

# Run migrations
python manage.py migrate

echo ""
echo "================================================================================"
echo "[SUCCESS] Migrations complete!"
echo "================================================================================"

