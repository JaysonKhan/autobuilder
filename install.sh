#!/bin/bash
# AutoBuilder Bot - Interactive Installation Script
# For Ubuntu 24.04

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/autobuilder"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    local answer
    
    if [ "$default" = "y" ]; then
        prompt="${prompt} [Y/n]: "
    else
        prompt="${prompt} [y/N]: "
    fi
    
    read -p "$prompt" answer
    answer="${answer:-$default}"
    
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

ask_input() {
    local prompt="$1"
    local default="$2"
    local answer
    
    if [ -n "$default" ]; then
        prompt="${prompt} [${default}]: "
    else
        prompt="${prompt}: "
    fi
    
    read -p "$prompt" answer
    echo "${answer:-$default}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Welcome
print_header "🚀 AutoBuilder Bot Installation"
echo "This script will install AutoBuilder Bot on your system."
echo ""

# Menu
print_header "Installation Options"
echo "1. Full installation (recommended)"
echo "2. Install dependencies only"
echo "3. Setup service only"
echo "4. Fix/Repair installation"
echo "5. Uninstall"
echo ""

read -p "Select option [1]: " choice
choice="${choice:-1}"

case $choice in
    1)
        MODE="full"
        ;;
    2)
        MODE="deps"
        ;;
    3)
        MODE="service"
        ;;
    4)
        MODE="fix"
        ;;
    5)
        MODE="uninstall"
        ;;
    *)
        print_error "Invalid option"
        exit 1
        ;;
esac

# Uninstall
if [ "$MODE" = "uninstall" ]; then
    print_header "Uninstalling AutoBuilder Bot"
    
    if ask_yes_no "Are you sure you want to uninstall?" "n"; then
        systemctl stop autobuilder 2>/dev/null || true
        systemctl disable autobuilder 2>/dev/null || true
        rm -f /etc/systemd/system/autobuilder.service
        systemctl daemon-reload
        
        if ask_yes_no "Remove all files and data?" "n"; then
            rm -rf "$INSTALL_DIR"
            rm -rf /etc/autobuilder
            rm -rf /var/log/autobuilder
            userdel autobuilder 2>/dev/null || true
            print_success "Uninstalled completely"
        else
            print_success "Service removed, files kept at $INSTALL_DIR"
        fi
        exit 0
    else
        print_info "Uninstall cancelled"
        exit 0
    fi
fi

# Full installation or dependencies
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ]; then
    print_header "📦 Installing System Dependencies"
    
    # Update package list
    print_info "Updating package list..."
    apt-get update -qq || {
        print_warning "Package list update had some errors, continuing anyway..."
    }
    
    # Install dependencies
    print_info "Installing system packages..."
    apt-get install -y \
        python3.12 \
        python3.12-venv \
        python3-pip \
        git \
        curl \
        wget \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev || {
        print_error "Failed to install system dependencies"
        exit 1
    }
    print_success "System dependencies installed"
fi

# Create user
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ]; then
    print_header "👤 Creating User"
    
    if ! id "autobuilder" &>/dev/null; then
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -m autobuilder
        print_success "User 'autobuilder' created"
    else
        print_info "User 'autobuilder' already exists"
    fi
fi

# Create directories
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ] || [ "$MODE" = "fix" ]; then
    print_header "📁 Creating Directories"
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/storage"
    mkdir -p "$INSTALL_DIR/reports"
    mkdir -p "$INSTALL_DIR/workspaces"
    mkdir -p "$INSTALL_DIR/repo"
    mkdir -p /var/log/autobuilder
    mkdir -p /etc/autobuilder
    
    print_success "Directories created"
fi

# Copy files
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ]; then
    print_header "📋 Copying Project Files"
    
    cp -r "$PROJECT_DIR/src" "$INSTALL_DIR/" 2>/dev/null || {
        print_error "Failed to copy src directory"
        exit 1
    }
    cp -r "$PROJECT_DIR/config" "$INSTALL_DIR/" 2>/dev/null || {
        print_error "Failed to copy config directory"
        exit 1
    }
    cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || {
        print_warning "requirements.txt not found, will create"
    }
    
    print_success "Files copied"
fi

# Set permissions
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ] || [ "$MODE" = "fix" ]; then
    print_header "🔐 Setting Permissions"
    
    chown -R autobuilder:autobuilder "$INSTALL_DIR"
    chown -R autobuilder:autobuilder /var/log/autobuilder
    chmod 755 "$INSTALL_DIR"
    chmod 755 /var/log/autobuilder
    
    print_success "Permissions set"
fi

# Create Python venv
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ] || [ "$MODE" = "fix" ]; then
    print_header "🐍 Setting Up Python Environment"
    
    # Remove old venv if exists
    if [ -d "$INSTALL_DIR/venv" ]; then
        if ask_yes_no "Remove existing virtual environment?" "y"; then
            rm -rf "$INSTALL_DIR/venv"
            print_info "Old venv removed"
        fi
    fi
    
    # Create venv
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        print_info "Creating Python virtual environment..."
        sudo -u autobuilder python3.12 -m venv "$INSTALL_DIR/venv" || {
            print_error "Failed to create venv"
            exit 1
        }
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    sudo -u autobuilder "$INSTALL_DIR/venv/bin/pip" install --upgrade pip setuptools wheel || {
        print_error "Failed to upgrade pip"
        exit 1
    }
    
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        sudo -u autobuilder "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" || {
            print_error "Failed to install requirements"
            exit 1
        }
    else
        print_warning "requirements.txt not found, installing basic packages..."
        sudo -u autobuilder "$INSTALL_DIR/venv/bin/pip" install python-telegram-bot requests psutil tomli || {
            print_error "Failed to install basic packages"
            exit 1
        }
    fi
    
    print_success "Python dependencies installed"
fi

# Create requirements.txt if missing
if [ ! -f "$INSTALL_DIR/requirements.txt" ]; then
    cat > "$INSTALL_DIR/requirements.txt" << EOF
python-telegram-bot>=20.0
requests>=2.31.0
psutil>=5.9.0
tomli>=2.0.0
EOF
fi

# Fix main.py
if [ "$MODE" = "full" ] || [ "$MODE" = "deps" ] || [ "$MODE" = "fix" ]; then
    print_header "📝 Configuring Main Script"
    
    # Update shebang
    sed -i "1s|.*|#!/opt/autobuilder/venv/bin/python3|" "$INSTALL_DIR/src/main.py" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/src/main.py"
    chown autobuilder:autobuilder "$INSTALL_DIR/src/main.py"
    
    print_success "Main script configured"
fi

# Setup configuration
if [ "$MODE" = "full" ] || [ "$MODE" = "service" ] || [ "$MODE" = "fix" ]; then
    print_header "⚙️  Configuration"
    
    if [ ! -f "/etc/autobuilder/config.toml" ]; then
        cp "$INSTALL_DIR/config/config.example.toml" /etc/autobuilder/config.toml
        chmod 600 /etc/autobuilder/config.toml
        chown root:root /etc/autobuilder/config.toml
        print_success "Configuration file created"
        
        if ask_yes_no "Do you want to configure bot token and chat ID now?" "y"; then
            BOT_TOKEN=$(ask_input "Enter Telegram bot token" "")
            CHAT_ID=$(ask_input "Enter Telegram chat ID" "")
            
            if [ -n "$BOT_TOKEN" ] && [ -n "$CHAT_ID" ]; then
                sed -i "s|bot_token = \".*\"|bot_token = \"$BOT_TOKEN\"|" /etc/autobuilder/config.toml
                sed -i "s|chat_id = \".*\"|chat_id = \"$CHAT_ID\"|" /etc/autobuilder/config.toml
                print_success "Bot token and chat ID configured"
            else
                print_warning "Configuration skipped, edit manually: sudo nano /etc/autobuilder/config.toml"
            fi
        else
            print_warning "Edit configuration manually: sudo nano /etc/autobuilder/config.toml"
        fi
    else
        print_info "Configuration file already exists"
        if ask_yes_no "Do you want to reconfigure?" "n"; then
            BOT_TOKEN=$(ask_input "Enter Telegram bot token" "")
            CHAT_ID=$(ask_input "Enter Telegram chat ID" "")
            
            if [ -n "$BOT_TOKEN" ] && [ -n "$CHAT_ID" ]; then
                sed -i "s|bot_token = \".*\"|bot_token = \"$BOT_TOKEN\"|" /etc/autobuilder/config.toml
                sed -i "s|chat_id = \".*\"|chat_id = \"$CHAT_ID\"|" /etc/autobuilder/config.toml
                print_success "Configuration updated"
            fi
        fi
    fi
fi

# Install systemd service
if [ "$MODE" = "full" ] || [ "$MODE" = "service" ] || [ "$MODE" = "fix" ]; then
    print_header "🔧 Installing Systemd Service"
    
    # Stop service if running
    systemctl stop autobuilder 2>/dev/null || true
    
    # Create service file
    cat > /etc/systemd/system/autobuilder.service << 'EOFSERVICE'
[Unit]
Description=AutoBuilder Bot - Telegram bot for automated tasks and builds
After=network.target mariadb.service
Wants=mariadb.service

[Service]
Type=simple
User=autobuilder
Group=autobuilder
WorkingDirectory=/opt/autobuilder
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/autobuilder/venv/bin/python3 /opt/autobuilder/src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=autobuilder
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/autobuilder /var/log/autobuilder
LimitNOFILE=65536
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOFSERVICE
    
    systemctl daemon-reload
    print_success "Systemd service installed"
fi

# Setup log rotation
if [ "$MODE" = "full" ] || [ "$MODE" = "service" ]; then
    print_header "📝 Setting Up Log Rotation"
    
    cat > /etc/logrotate.d/autobuilder << 'EOFLROTATE'
/var/log/autobuilder/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 autobuilder autobuilder
    sharedscripts
}
EOFLROTATE
    
    print_success "Log rotation configured"
fi

# Start service
if [ "$MODE" = "full" ] || [ "$MODE" = "service" ] || [ "$MODE" = "fix" ]; then
    print_header "🚀 Starting Service"
    
    if ask_yes_no "Do you want to start the service now?" "y"; then
        systemctl enable autobuilder
        systemctl start autobuilder
        
        sleep 2
        
        if systemctl is-active --quiet autobuilder; then
            print_success "Service started successfully"
        else
            print_error "Service failed to start"
            print_info "Check logs: sudo journalctl -u autobuilder -n 50"
        fi
    else
        print_info "Service not started. Start manually: sudo systemctl start autobuilder"
    fi
fi

# Summary
print_header "✅ Installation Complete"
echo ""
echo "📋 Summary:"
echo "  • Installation directory: $INSTALL_DIR"
echo "  • Configuration: /etc/autobuilder/config.toml"
echo "  • Service: autobuilder.service"
echo ""
echo "📝 Useful Commands:"
echo "  • Check status: sudo systemctl status autobuilder"
echo "  • View logs: sudo journalctl -u autobuilder -f"
echo "  • Restart: sudo systemctl restart autobuilder"
echo "  • Edit config: sudo nano /etc/autobuilder/config.toml"
echo ""
echo "🧪 Test the bot:"
echo "  Send /start command to your Telegram bot"
echo ""

