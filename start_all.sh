#!/bin/bash
# Script to start Neo4j, database, backend FastAPI quiz API, and Expo frontend for The Grey Tutor

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "Loaded environment variables from .env"
fi

# Check if database is initialized
if [ ! -f thegreytutor.db ]; then
  echo "Database not found. Running setup_database.sh..."
  ./setup_database.sh
fi

# 1. Start Neo4j (docker-compose)
echo "Starting Neo4j via docker-compose..."
docker-compose up -d

# 2. Start backend FastAPI app (from project root, as Python module)
echo "Starting backend FastAPI app..."
uvicorn thegreytutor.backend.src.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 3. Start Expo frontend (from thegreytutor/frontend directory)
echo "Starting Expo frontend..."
pushd thegreytutor/frontend > /dev/null
npx expo start &
FRONTEND_PID=$!
popd > /dev/null

# 4. Wait for user to stop
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit 0" SIGINT
wait $BACKEND_PID $FRONTEND_PID
