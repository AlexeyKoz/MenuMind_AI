#!/bin/bash

# Database Backup Script

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/menumine_backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE.gz"

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
