#!/bin/bash

# Backup script for Ollie data
# Usage: ./backup-nightly.sh

BACKUP_ROOT="/mnt/external_ssd/backups/ollie"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup SQLite DB
if [ -f "/data/ollie.db" ]; then
    echo "Backing up database..."
    cp /data/ollie.db "$BACKUP_DIR/"
fi

# Backup Audio files
if [ -d "/data/audio" ]; then
    echo "Backing up audio files..."
    rsync -av /data/audio "$BACKUP_DIR/"
fi

# Backup ChromaDB
if [ -d "/data/chroma" ]; then
    echo "Backing up ChromaDB..."
    rsync -av /data/chroma "$BACKUP_DIR/"
fi

# Backup LoRA Adapters
if [ -d "/data/models/adapters" ]; then
    echo "Backing up LoRA adapters..."
    rsync -av /data/models/adapters "$BACKUP_DIR/"
fi

# Prune old backups (keep last 30 days)
find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +

echo "Backup complete: $BACKUP_DIR"
