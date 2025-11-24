#!/bin/bash

# Backup script for Aeron data
# Usage: ./backup-nightly.sh

BACKUP_ROOT="/mnt/external_ssd/backups/aeron"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup SQLite DB
if [ -f "/data/aeron.db" ]; then
    echo "Backing up database..."
    cp /data/aeron.db "$BACKUP_DIR/"
fi

# Backup Audio files
if [ -d "/data/audio" ]; then
    echo "Backing up audio files..."
    rsync -av /data/audio "$BACKUP_DIR/"
fi

# Prune old backups (keep last 30 days)
find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +

echo "Backup complete: $BACKUP_DIR"

