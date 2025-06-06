#!/bin/bash
# Script to set up the database for The Grey Tutor

# Exit on error
set -e

echo "Setting up The Grey Tutor database..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is required but not installed."
    exit 1
fi

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p database/migrations/versions

# Initialize the database
echo "Initializing the database..."
python -c "from database.init import init_database; init_database()"

# Import data
echo "Importing data..."
python -c "from database.init import import_all; import_all()"

echo "Database setup complete."
echo "You can now use the database admin tool to manage the database:"
echo "  python -m database.admin list-users"
echo "  python -m database.admin get-user --username test_user"
echo "  python -m database.admin create-user --username new_user --name 'New User' --email 'new.user@example.com'"
echo "  python -m database.admin list-conversations --username test_user"
echo "  python -m database.admin get-conversation --id <conversation_id> --messages"
