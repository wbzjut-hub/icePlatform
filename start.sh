#!/bin/bash

# IcePlatform Development Startup Script

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting IcePlatform (Dev Mode) ===${NC}"

# Function to handle script exit
cleanup() {
    echo -e "\n${RED}Stopping services...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        echo "Killing Backend (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ -n "$VITE_PID" ]; then
        echo "Killing Vite (PID: $VITE_PID)"
        kill $VITE_PID 2>/dev/null
    fi
    echo -e "${GREEN}All services stopped.${NC}"
    exit
}

# Trap SIGINT (Ctrl+C) and EXIT
trap cleanup SIGINT EXIT

# 1. Start Backend
echo -e "${GREEN}[1/3] Starting Backend...${NC}"
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
else
    echo -e "${RED}Error: backend/venv not found. Please run setup first.${NC}"
    exit 1
fi

cd backend
# Run python unbuffered to see output immediately
python -u main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend running (PID: $BACKEND_PID). Logs: backend.log"
cd ..

# 2. Start Vite (Frontend)
echo -e "${GREEN}[2/3] Starting Vite Dev Server...${NC}"
cd my-vue-app
npm run dev > ../frontend.log 2>&1 &
VITE_PID=$!
echo "Vite running (PID: $VITE_PID). Logs: frontend.log"

# 3. Start Electron
echo -e "${GREEN}[3/3] Launching Electron...${NC}"
# Electron will wait for Backend port (checked in main.js)
# and load Vite URL.
npx electron .

# Script will hang here until Electron is closed
echo -e "${BLUE}Electron closed.${NC}"
