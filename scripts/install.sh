#!/bin/bash
# AutoBuilder Bot Installation Script
# For Ubuntu 24.04

set -e

echo "🚀 AutoBuilder Bot Installation Script"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Detect installation directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/autobuilder"

echo "📁 Installation directory: $INSTALL_DIR"
echo "📁 Project directory: $PROJECT_DIR"

# Update package list (ignore errors from mirror sync issues)
echo "📦 Updating package list..."
apt-get update -qq || {
    echo "⚠️  Package list update had some errors (mirror sync issues), continuing anyway..."
}

# Install system dependencies
echo "📦 Installing system dependencies..."
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
    python3-dev

# Create autobuilder user
echo "👤 Creating autobuilder user..."
if ! id "autobuilder" &>/dev/null; then
    useradd -r -s /bin/bash -d "$INSTALL_DIR" -m autobuilder
    echo "✅ User 'autobuilder' created"
else
    echo "ℹ️  User 'autobuilder' already exists"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/storage"
mkdir -p "$INSTALL_DIR/reports"
mkdir -p "$INSTALL_DIR/workspaces"
mkdir -p "$INSTALL_DIR/repo"
mkdir -p /var/log/autobuilder
mkdir -p /etc/autobuilder

# Copy project files
echo "📋 Copying project files..."
cp -r "$PROJECT_DIR/src" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/config" "$INSTALL_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || echo "⚠️  requirements.txt not found, will create"

# Set permissions
chown -R autobuilder:autobuilder "$INSTALL_DIR"
chown -R autobuilder:autobuilder /var/log/autobuilder
chmod 755 "$INSTALL_DIR"
chmod 755 /var/log/autobuilder

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3.12 -m venv "$INSTALL_DIR/venv"
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate venv and install Python dependencies
echo "📦 Installing Python dependencies..."
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip setuptools wheel

# Install requirements
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    pip install -r "$INSTALL_DIR/requirements.txt"
else
    # Install basic requirements
    pip install python-telegram-bot requests psutil tomli
    echo "⚠️  Installed basic dependencies. Please create requirements.txt for full dependency list."
fi

deactivate

# Create requirements.txt if it doesn't exist
if [ ! -f "$INSTALL_DIR/requirements.txt" ]; then
    cat > "$INSTALL_DIR/requirements.txt" << EOF
python-telegram-bot>=20.0
requests>=2.31.0
psutil>=5.9.0
tomli>=2.0.0
EOF
fi

# Update main.py shebang to use venv python
sed -i "1s|.*|#!/opt/autobuilder/venv/bin/python3|" "$INSTALL_DIR/src/main.py"
chmod +x "$INSTALL_DIR/src/main.py"

# Setup configuration
echo "⚙️  Setting up configuration..."
if [ ! -f "/etc/autobuilder/config.toml" ]; then
    cp "$INSTALL_DIR/config/config.example.toml" /etc/autobuilder/config.toml
    chmod 600 /etc/autobuilder/config.toml
    chown root:root /etc/autobuilder/config.toml
    echo "✅ Configuration file created at /etc/autobuilder/config.toml"
    echo "⚠️  IMPORTANT: Edit /etc/autobuilder/config.toml and set your bot token and other settings!"
else
    echo "ℹ️  Configuration file already exists"
fi

# Install systemd service
echo "🔧 Installing systemd service..."
if [ -f "$PROJECT_DIR/systemd/autobuilder.service" ]; then
    cp "$PROJECT_DIR/systemd/autobuilder.service" /etc/systemd/system/
    # Update ExecStart to use venv python
    sed -i "s|ExecStart=/usr/bin/python3|ExecStart=$INSTALL_DIR/venv/bin/python3|" /etc/systemd/system/autobuilder.service
    systemctl daemon-reload
    echo "✅ Systemd service installed"
else
    echo "❌ Service file not found at $PROJECT_DIR/systemd/autobuilder.service"
    echo "⚠️  Creating service file manually..."
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

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/autobuilder /var/log/autobuilder

# Resource limits
LimitNOFILE=65536
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOFSERVICE
    systemctl daemon-reload
    echo "✅ Systemd service created and installed"
fi

# Create log rotation
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/autobuilder << EOF
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
EOF

echo "✅ Log rotation configured"

# Summary
echo ""
echo "✅ Installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit configuration: sudo nano /etc/autobuilder/config.toml"
echo "2. Set your Telegram bot token and chat ID"
echo "3. Configure GitHub SSH key path if needed"
echo "4. Start service: sudo systemctl start autobuilder"
echo "5. Enable on boot: sudo systemctl enable autobuilder"
echo "6. Check status: sudo systemctl status autobuilder"
echo "7. View logs: sudo journalctl -u autobuilder -f"
echo ""

