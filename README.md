# AutoBuilder Bot

Production-ready Telegram bot service for automated tasks, audits, and builds on Ubuntu 24.04.

## 🏗️ Architecture

- **OS**: Ubuntu 24.04
- **Web Server**: Nginx + PHP-FPM 8.3
- **Database**: MariaDB 10.11.x (or SQLite for development)
- **Language**: Python 3.12
- **Bot Framework**: python-telegram-bot

## 📁 Directory Structure

```
autobuilder/
├── config/          # Configuration files
├── src/            # Source code
│   ├── telegram/   # Telegram bot handlers
│   ├── jobs/       # Job queue management
│   ├── tasks/      # Task implementations
│   └── utils/      # Utilities (shell, redact, markdown)
├── storage/        # Database files
├── scripts/        # Setup and run scripts
├── systemd/        # Systemd service files
├── reports/        # Generated reports (auto-cleaned)
└── workspaces/     # Per-job build workspaces (auto-cleaned)
```

## 🚀 Quick Start

### 1. Installation

```bash
cd autobuilder
sudo bash scripts/install.sh
```

### 2. Configuration

Copy and edit the config file:

```bash
sudo cp config/config.example.toml /etc/autobuilder/config.toml
sudo nano /etc/autobuilder/config.toml
```

Required settings:
- `telegram.bot_token`: Your Telegram bot token
- `telegram.chat_id`: Your Telegram chat ID
- `github.ssh_key_path`: Path to SSH deploy key
- `github.repo_url`: Repository URL
- `database.type`: `sqlite` or `mariadb`
- `database.connection_string`: Connection string

### 3. Start Service

```bash
sudo systemctl start autobuilder
sudo systemctl enable autobuilder
sudo systemctl status autobuilder
```

### 4. Check Logs

```bash
sudo journalctl -u autobuilder -f
```

## 📋 Available Commands

- `/start` - Show welcome message and available commands
- `/help` - Show help and safety rules
- `/status` - Get server status (nginx, php-fpm, mariadb, disk, ram)
- `/audit_site` - Audit public endpoints of jaysonkhan.com
- `/build_weather_apk` - Build a weather app APK
- `/jobs` - List last 10 jobs
- `/job <id>` - Show job status
- `/cancel <id>` - Cancel a running job

## 🔒 Security

- All secrets stored in `/etc/autobuilder/config.toml` with `chmod 600`
- Sensitive data redacted from logs and reports
- Shell commands run with timeouts and resource limits
- Workspaces isolated per job
- Auto-cleanup of old jobs and artifacts

## 🛠️ Development

Run in development mode:

```bash
bash scripts/run_dev.sh
```

## 📝 Notes

- Reports are auto-cleaned after 7 days
- Workspaces are cleaned after job completion
- Old jobs (>30 days) are auto-archived
- Maximum build time: 30 minutes per job
- Maximum disk usage: 5GB per job

## 🐛 Troubleshooting

### Bot not responding
- Check bot token in config
- Verify service is running: `sudo systemctl status autobuilder`
- Check logs: `sudo journalctl -u autobuilder -n 50`

### Permission errors
- Ensure config file has correct permissions: `sudo chmod 600 /etc/autobuilder/config.toml`
- Check workspace permissions: `sudo chown -R autobuilder:autobuilder /opt/autobuilder/workspaces`

### Database connection issues
- Verify MariaDB is running: `sudo systemctl status mariadb`
- Check connection string in config
- Test connection: `mysql -u autobuilder -p`

