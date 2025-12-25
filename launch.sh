#!/bin/bash

# VideoConverter Launch Script
# This script checks for required dependencies, sets up a virtual environment, and launches the application

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  VideoConverter Launch Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python 3
echo -e "${YELLOW}[1/4] Checking Python installation...${NC}"
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo -e "${YELLOW}Please install Python 3 using: sudo apt install python3 python3-venv python3-pip${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"
echo ""

# Check for system dependencies (ffmpeg)
echo -e "${YELLOW}[2/4] Checking system dependencies...${NC}"
MISSING_SYSTEM_DEPS=false

if ! command_exists ffmpeg; then
    echo -e "${RED}✗ ffmpeg not found${NC}"
    MISSING_SYSTEM_DEPS=true
else
    echo -e "${GREEN}✓ ffmpeg found${NC}"
fi

if [ "$MISSING_SYSTEM_DEPS" = true ]; then
    echo ""
    echo -e "${YELLOW}Installing missing system dependencies...${NC}"
    echo -e "${YELLOW}This requires sudo privileges.${NC}"
    sudo apt update
    sudo apt install -y ffmpeg
    
    if ! command_exists ffmpeg; then
        echo -e "${RED}Error: Failed to install ffmpeg${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ System dependencies installed successfully${NC}"
fi
echo ""

# Virtual Environment Setup
echo -e "${YELLOW}[3/4] Checking Virtual Environment...${NC}"
VENV_DIR="venv"

# Check if venv exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment in $VENV_DIR...${NC}"
    # Try to create venv, if it fails, user might need python3-venv
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        echo -e "${YELLOW}You might need to install the venv package:${NC}"
        echo -e "${YELLOW}sudo apt install python3-venv${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment found${NC}"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip inside venv to avoid warnings
pip install --upgrade pip > /dev/null 2>&1

# Check and install Python dependencies inside venv
echo -e "${YELLOW}[4/4] Checking Python dependencies (inside venv)...${NC}"

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

# We use pip sync or install to ensure dependencies are met
# Using install directly is faster if requirements are already met
echo -e "${YELLOW}Ensuring requirements are installed...${NC}"
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install Python dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All Python dependencies satisfied${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}System Ready!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Launching VideoConverter...${NC}"
echo ""

# Launch the application using the python from the venv
python app.py

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}Application exited with error code: $EXIT_CODE${NC}"
    # Keep terminal open if there was an error so user can read it
    read -p "Press Enter to close..."
    exit $EXIT_CODE
fi
