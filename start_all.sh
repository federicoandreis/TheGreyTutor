#!/bin/bash
# Script to start Neo4j, backend FastAPI quiz API, and Expo frontend for The Grey Tutor

# 1. Start Neo4j (docker-compose)
echo "Starting Neo4j via docker-compose..."
docker-compose up -d

# 2. Start backend FastAPI quiz API (from project root, as Python module)
echo "Starting backend FastAPI quiz API..."
uvicorn kg_quizzing.scripts.quiz_api:app --reload --host 0.0.0.0 --port 8000 &
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