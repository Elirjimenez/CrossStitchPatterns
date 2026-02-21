#!/bin/sh
set -e

# Default if not provided
: "${STORAGE_DIR:=/app/storage}"

# Ensure storage exists
mkdir -p "${STORAGE_DIR}/projects"

# Fix ownership at runtime (needed if STORAGE_DIR is a mounted volume)
chown -R appuser:appuser "${STORAGE_DIR}"

# Drop privileges and run the passed command (preserve args)
exec su -s /bin/sh appuser -c "$@"