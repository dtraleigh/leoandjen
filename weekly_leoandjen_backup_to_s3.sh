#!/bin/bash
set -euo pipefail

# CONFIGURATION
DATE=$(date +%F)
PROJECT_NAME="leoandjen"
PROJECT_DIR="/home/cophead567/apps/$PROJECT_NAME"
VENV_DIR="/home/cophead567/apps/$PROJECT_NAME/env"
BACKUP_DIR="/tmp/${PROJECT_NAME}_backup_$DATE"
S3_BUCKET="s3://leoandjen-weekly-backups/$DATE"
DB_NAME="leoandjen"
DB_USER="leoandjen"

# Prepare
rm -rf "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup codebase (excluding venv, logs, and static/media files)
tar -czf "$BACKUP_DIR/codebase.tar.gz" -C "$PROJECT_DIR" . \
  --exclude='env*' \
  --exclude='*.log' \
  --exclude='static' \
  --exclude='media' \
  --exclude='tmp'

# Backup virtualenv
tar -czf "$BACKUP_DIR/venv.tar.gz" -C "$VENV_DIR" .

# Backup PostgreSQL database
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db.sql.gz"

# Upload to S3
aws s3 cp "$BACKUP_DIR" "$S3_BUCKET" --recursive

# Cleanup local
rm -rf "$BACKUP_DIR"

echo "Backup complete: $DATE" >> ~/backup.log

