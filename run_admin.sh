#!/bin/bash

# Script to run the database admin interface

# Exit on error
set -e

echo "Running The Grey Tutor Database Admin Interface..."

# Run the admin interface
python -m database.admin "$@"
