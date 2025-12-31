#!/bin/bash
# Script to run the database admin tool

# Check if Python is installed
if command -v python &> /dev/null; then
    PYTHON=python
elif command -v python3 &> /dev/null; then
    PYTHON=python3
else
    echo "Error: Python is required but not installed."
    exit 1
fi

# Run the admin tool with the provided arguments
$PYTHON -m database.admin "$@"

# If no arguments were provided, show help
if [ $# -eq 0 ]; then
    echo ""
    echo "Common commands:"
    echo "  ./run_admin.sh list-users                                  # List all users"
    echo "  ./run_admin.sh get-user --username test_user               # Get a user by username"
    echo "  ./run_admin.sh create-user --username new_user --name \"New User\" --email \"new.user@example.com\"  # Create a new user"
    echo "  ./run_admin.sh update-user --username test_user --name \"Updated Name\"  # Update a user"
    echo "  ./run_admin.sh delete-user --username test_user            # Delete a user"
    echo "  ./run_admin.sh list-conversations --username test_user     # List conversations for a user"
    echo "  ./run_admin.sh get-conversation --id <conversation_id> --messages  # Get a conversation with messages"
    echo "  ./run_admin.sh delete-conversation --id <conversation_id>  # Delete a conversation"
    echo "  ./run_admin.sh init-db --import-all                        # Initialize the database and import all data"
    echo "  ./run_admin.sh reset-db                                    # Reset the database (warning: this will delete all data)"
fi
