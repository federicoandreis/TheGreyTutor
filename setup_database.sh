#!/bin/bash

# Setup script for The Grey Tutor database

# Exit on error
set -e

echo "Setting up The Grey Tutor database..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start PostgreSQL if not already running
echo "Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Initialize the database
echo "Initializing the database..."
python -m database.cli init

# Create admin user if it doesn't exist
echo "Creating admin user..."
python -m database.cli create-user admin --role admin --email admin@thegreytutor.com

# Import data if directories exist
if [ -d "conversation_history" ]; then
    echo "Importing conversation history..."
    python -m database.cli import --conversations conversation_history
fi

if [ -d "assessment_conversations" ]; then
    echo "Importing assessment conversations..."
    python -m database.cli import --assessments assessment_conversations
fi

if [ -d "kg_quizzing/scripts/assessment_conversations" ]; then
    echo "Importing KG quizzing assessment conversations..."
    python -m database.cli import --assessments kg_quizzing/scripts/assessment_conversations
fi

echo "Database setup complete!"
echo "You can now use the database CLI with 'python -m database.cli'"
echo "For help, run 'python -m database.cli --help'"
