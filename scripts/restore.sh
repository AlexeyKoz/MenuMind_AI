#!/bin/bash

# Database Restore Script

if [ $# -eq 0 ]; then
    echo "Usage: ./restore.sh <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  Warning: This will replace the current database!"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Decompress backup
gunzip -c $BACKUP_FILE > /tmp/restore.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER $DB_NAME < /tmp/restore.sql

# Clean up
rm /tmp/restore.sql

echo "✅ Database restored from: $BACKUP_FILE"
