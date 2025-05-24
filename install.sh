#!/bin/bash

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print with color
print_status() {
    echo -e "${2}$1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python package
install_python_package() {
    local package=$1
    if command_exists pacman; then
        sudo pacman -S --noconfirm "python-$package"
    elif command_exists apt; then
        sudo apt install -y "python3-$package"
    elif command_exists dnf; then
        sudo dnf install -y "python3-$package"
    elif command_exists brew; then
        pip3 install "$package"
    else
        pip3 install "$package"
    fi
}

# Welcome message
print_status "🚀 Installing Laravel VHost Manager dependencies..." "$YELLOW"
echo

# Check for Python 3
if ! command_exists python3; then
    print_status "❌ Python 3 is not installed. Installing..." "$RED"
    if command_exists pacman; then
        sudo pacman -S --noconfirm python
    elif command_exists apt; then
        sudo apt install -y python3
    elif command_exists dnf; then
        sudo dnf install -y python3
    elif command_exists brew; then
        brew install python
    else
        print_status "❌ Could not install Python 3. Please install it manually." "$RED"
        exit 1
    fi
fi

# Check for pip
if ! command_exists pip3; then
    print_status "❌ pip3 is not installed. Installing..." "$RED"
    if command_exists pacman; then
        sudo pacman -S --noconfirm python-pip
    elif command_exists apt; then
        sudo apt install -y python3-pip
    elif command_exists dnf; then
        sudo dnf install -y python3-pip
    elif command_exists brew; then
        brew install python # pip comes with Python from brew
    else
        print_status "❌ Could not install pip3. Please install it manually." "$RED"
        exit 1
    fi
fi

# Install mkcert
if ! command_exists mkcert; then
    print_status "📦 Installing mkcert..." "$YELLOW"
    if command_exists pacman; then
        sudo pacman -S --noconfirm mkcert nss
    elif command_exists apt; then
        sudo apt install -y libnss3-tools
        # Download and install mkcert for Ubuntu/Debian
        curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
        chmod +x mkcert-v*-linux-amd64
        sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
    elif command_exists dnf; then
        sudo dnf install -y nss-tools
        # Download and install mkcert for Fedora
        curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
        chmod +x mkcert-v*-linux-amd64
        sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
    elif command_exists brew; then
        brew install mkcert nss
    else
        print_status "❌ Could not install mkcert. Please install it manually." "$RED"
        exit 1
    fi
fi

# Check for Apache
if ! command_exists httpd && ! command_exists apachectl; then
    print_status "\n⚠️  WARNING: Apache is not installed!" "$YELLOW"
    print_status "This script requires Apache to function properly. Please install Apache manually:" "$YELLOW"
    echo
    if command_exists pacman; then
        print_status "Run: sudo pacman -S apache" "$GREEN"
    elif command_exists apt; then
        print_status "Run: sudo apt install apache2" "$GREEN"
    elif command_exists dnf; then
        print_status "Run: sudo dnf install httpd" "$GREEN"
    elif command_exists brew; then
        print_status "Run: brew install httpd" "$GREEN"
    else
        print_status "Please install Apache using your system's package manager" "$GREEN"
    fi
    echo
    print_status "After installing Apache, run this script again" "$YELLOW"
    echo
fi

# Install InquirerPy
print_status "📦 Installing InquirerPy..." "$YELLOW"
install_python_package "inquirerpy"

# Setup mkcert
print_status "🔒 Setting up mkcert..." "$YELLOW"
mkcert -install

# Final check
print_status "\n✅ Dependencies installation completed!" "$GREEN"
print_status "You can now run the Laravel VHost Manager with:" "$YELLOW"
print_status "sudo python3 laravel_vhoster_tui.py" "$GREEN"

# Make certificate directory
mkdir -p ~/.localhost-ssl
print_status "✅ Created SSL certificates directory at ~/.localhost-ssl" "$GREEN"
