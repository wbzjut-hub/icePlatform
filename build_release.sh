#!/bin/bash

# Exit on error
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Starting IcePlatform Release Build ===${NC}"

# 1. Build Backend
echo -e "\n${GREEN}[1/2] Building Python Backend...${NC}"
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: backend/venv not found!"
    exit 1
fi

# Ensure PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Build executable
pyinstaller icePlatform.spec --clean --noconfirm

# Deactivate venv
deactivate
cd ..

# 2. Build Frontend & Electron
echo -e "\n${GREEN}[2/2] Building Electron App (DMG)...${NC}"
cd my-vue-app

# Install dependencies if needed (optional, safer to assume they exist or run npm install)
# npm install 

# Run build script defined in package.json
# "electron:build": "vue-tsc && vite build && electron-builder"
npm run electron:build

cd ..

echo -e "\n${GREEN}=== Build Complete! ===${NC}"
echo -e "DMG should be in: ${BLUE}my-vue-app/dist_electron/${NC}"
