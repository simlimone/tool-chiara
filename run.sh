#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down services...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Activate virtual environment
source venv/bin/activate

# Create necessary directories
mkdir -p backend/temp backend/output

# Start backend server
echo -e "${BLUE}Starting backend server...${NC}"
cd backend
uvicorn main:app --reload &
cd ..

# Wait for backend to start
sleep 2

# Start frontend development server
echo -e "${BLUE}Starting frontend server...${NC}"
cd frontend
npm start &
cd ..

echo -e "${GREEN}Both servers are running!${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend: http://localhost:8000${NC}"
echo -e "${BLUE}Press Ctrl+C to stop both servers${NC}"

# Wait for both processes
wait
