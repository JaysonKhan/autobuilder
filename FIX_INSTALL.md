# O'rnatish Muammolarini Hal Qilish

Agar o'rnatish paytida muammolar bo'lsa, quyidagi qadamlarni bajaring:

## Muammo 1: apt-get update xatoliklari

Bu Ubuntu mirror muammosi. Script endi bu xatoliklarni ignore qiladi va davom etadi.

Agar hali ham muammo bo'lsa:

```bash
# Qo'lda paketlarni o'rnatish
sudo apt-get install -y python3.12 python3.12-venv python3-pip git curl wget build-essential libssl-dev libffi-dev python3-dev
```

## Muammo 2: Systemd service topilmayapti

Agar service fayli to'g'ri o'rnatilmagan bo'lsa:

```bash
# Service faylini qo'lda yaratish
sudo nano /etc/systemd/system/autobuilder.service
```

Quyidagi kontentni qo'shing:

```ini
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
```

Keyin:

```bash
sudo systemctl daemon-reload
sudo systemctl start autobuilder
sudo systemctl status autobuilder
```

## Muammo 3: Python venv topilmayapti

Agar virtual environment yaratilmagan bo'lsa:

```bash
cd /opt/autobuilder
sudo -u autobuilder python3.12 -m venv venv
sudo -u autobuilder venv/bin/pip install --upgrade pip setuptools wheel
sudo -u autobuilder venv/bin/pip install -r requirements.txt
```

## Muammo 4: Permission xatoliklari

```bash
sudo chown -R autobuilder:autobuilder /opt/autobuilder
sudo chown -R autobuilder:autobuilder /var/log/autobuilder
sudo chmod 755 /opt/autobuilder
sudo chmod 755 /var/log/autobuilder
```

## Muammo 5: Config fayl topilmayapti

```bash
sudo mkdir -p /etc/autobuilder
sudo cp /opt/autobuilder/config/config.example.toml /etc/autobuilder/config.toml
sudo chmod 600 /etc/autobuilder/config.toml
sudo chown root:root /etc/autobuilder/config.toml
sudo nano /etc/autobuilder/config.toml  # Bot token va chat ID ni sozlash
```

## To'liq qayta o'rnatish

Agar hamma narsa noto'g'ri bo'lsa:

```bash
# Service'ni to'xtatish
sudo systemctl stop autobuilder 2>/dev/null || true
sudo systemctl disable autobuilder 2>/dev/null || true

# Eski fayllarni o'chirish
sudo rm -f /etc/systemd/system/autobuilder.service
sudo systemctl daemon-reload

# Qayta o'rnatish
cd /opt/autobuilder
sudo bash scripts/install.sh

# Service'ni ishga tushirish
sudo systemctl start autobuilder
sudo systemctl enable autobuilder
sudo systemctl status autobuilder
```

## Tekshirish

Barcha narsa to'g'ri ishlayotganini tekshirish:

```bash
# Service holati
sudo systemctl status autobuilder

# Loglar
sudo journalctl -u autobuilder -n 50 --no-pager

# Python venv mavjudligi
ls -la /opt/autobuilder/venv/bin/python3

# Config fayl
sudo ls -la /etc/autobuilder/config.toml

# Permissions
ls -la /opt/autobuilder
```

