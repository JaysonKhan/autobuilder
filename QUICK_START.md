# Quick Start Guide

AutoBuilder Bot'ni tezda ishga tushirish uchun qo'llanma.

## 🚀 Tezkor o'rnatish

### 1. Loyihani yuklab olish

```bash
cd /opt
git clone <your-repo-url> autobuilder-source
cd autobuilder-source/autobuilder
```

### 2. O'rnatish

```bash
sudo bash install.sh
```

Interaktiv menu sizga quyidagi variantlarni taklif qiladi:
- **1. Full installation** - to'liq o'rnatish (tavsiya etiladi)
- **2. Install dependencies only** - faqat dependencies
- **3. Setup service only** - faqat service
- **4. Fix/Repair installation** - o'rnatishni tuzatish
- **5. Uninstall** - o'chirish

Bu script:
- ✅ Barcha kerakli paketlarni o'rnatadi
- ✅ `autobuilder` foydalanuvchisini yaratadi
- ✅ Virtual environment yaratadi
- ✅ Python paketlarini o'rnatadi
- ✅ Systemd service'ni sozlaydi

### 3. Konfiguratsiyani sozlash

```bash
sudo nano /etc/autobuilder/config.toml
```

**Majburiy sozlamalar:**

```toml
[telegram]
bot_token = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # @BotFather dan oling
chat_id = "123456789"  # @userinfobot dan oling

[github]
ssh_key_path = "/root/.ssh/autobuilder_github"  # SSH kalit yo'li
repo_url = "git@github.com:username/repo.git"  # Repository URL
```

### 4. GitHub SSH kalitini sozlash (ixtiyoriy)

Agar kod push qilish kerak bo'lsa:

```bash
# SSH kalit yaratish
ssh-keygen -t ed25519 -f /root/.ssh/autobuilder_github -N ""

# Public kalitni GitHub'ga qo'shish
cat /root/.ssh/autobuilder_github.pub
# Bu kalitni GitHub Settings > SSH Keys ga qo'shing
```

### 5. Service'ni ishga tushirish

```bash
# Service'ni boshlash
sudo systemctl start autobuilder

# Avtomatik ishga tushishini yoqish
sudo systemctl enable autobuilder

# Holatini tekshirish
sudo systemctl status autobuilder
```

### 6. Loglarni ko'rish

```bash
# Real-time loglar
sudo journalctl -u autobuilder -f

# Oxirgi 50 ta log
sudo journalctl -u autobuilder -n 50
```

## 🧪 Birinchi test

Telegram'da botga quyidagi buyruqni yuboring:

```
/start
```

Agar bot javob bersa, o'rnatish muvaffaqiyatli! 🎉

## 📋 Keyingi qadamlar

1. **Server holatini tekshirish:**
   ```
   /status
   ```

2. **Saytni xavfsizlik tekshiruvi:**
   ```
   /audit_site
   ```

3. **Job ro'yxatini ko'rish:**
   ```
   /jobs
   ```

## 🔧 Development rejimida ishga tushirish

Agar production'ga o'rnatishdan oldin test qilmoqchi bo'lsangiz:

```bash
cd autobuilder
bash scripts/run_dev.sh
```

Bu:
- Virtual environment yaratadi (agar yo'q bo'lsa)
- Paketlarni o'rnatadi
- Bot'ni development rejimida ishga tushiradi

## ⚠️ Muammolarni hal qilish

### Bot javob bermayapti

1. Service ishlayaptimi?
   ```bash
   sudo systemctl status autobuilder
   ```

2. Bot token to'g'rimi?
   ```bash
   sudo grep bot_token /etc/autobuilder/config.toml
   ```

3. Loglarni tekshiring:
   ```bash
   sudo journalctl -u autobuilder -n 50
   ```

### Permission xatolari

```bash
sudo chown -R autobuilder:autobuilder /opt/autobuilder
sudo chown -R autobuilder:autobuilder /var/log/autobuilder
```

### Database xatolari

```bash
# SQLite database permissions
sudo chown autobuilder:autobuilder /opt/autobuilder/storage/jobs.db
sudo chmod 644 /opt/autobuilder/storage/jobs.db
```

## 📚 Qo'shimcha ma'lumot

- Batafsil test qo'llanmasi: [SMOKE_TEST.md](SMOKE_TEST.md)
- To'liq hujjat: [README.md](README.md)

