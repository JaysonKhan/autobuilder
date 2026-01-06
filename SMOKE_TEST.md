# Smoke Test Guide

Bu qo'llanma AutoBuilder Bot'ni tekshirish uchun aniq buyruqlarni o'z ichiga oladi.

## 📋 Oldindan tekshiruvlar

### 1. Konfiguratsiyani tekshirish

```bash
sudo cat /etc/autobuilder/config.toml
```

Quyidagilar to'g'ri sozlanganligini tekshiring:
- `telegram.bot_token` - Telegram bot token (@BotFather dan olingan)
- `telegram.chat_id` - Sizning chat ID (@userinfobot dan olingan)
- `database.type` - `sqlite` yoki `mariadb`
- `github.ssh_key_path` - GitHub SSH kalit yo'li (agar kerak bo'lsa)

### 2. Service holatini tekshirish

```bash
sudo systemctl status autobuilder
```

Service `active (running)` bo'lishi kerak.

### 3. Loglarni tekshirish

```bash
sudo journalctl -u autobuilder -n 50 --no-pager
```

Xatoliklar bo'lmasligi kerak.

## 🧪 Test buyruqlari

### Test 1: Bot javob beradimi?

Telegram'da botga quyidagi buyruqni yuboring:

```
/start
```

**Kutilgan natija:** Bot javob beradi va mavjud buyruqlar ro'yxatini ko'rsatadi.

### Test 2: Server holati

```
/status
```

**Kutilgan natija:**
- Bot "⏳ Server holatini tekshiryapman..." xabari yuboradi
- Bir necha soniyadan keyin Markdown hisobot yuboriladi
- Hisobotda quyidagilar bo'lishi kerak:
  - Nginx, PHP-FPM, MariaDB holati
  - Disk va RAM foydalanishi
  - CPU foydalanishi

### Test 3: Xavfsizlik tekshiruvi

```
/audit_site
```

**Kutilgan natija:**
- Bot "🔍 Saytni tekshiryapman..." xabari yuboradi
- Bir necha soniyadan keyin Markdown hisobot yuboriladi
- Hisobotda quyidagilar bo'lishi kerak:
  - Exposed pathlar tekshiruvi
  - TLS/SSL sozlamalari
  - HTTP security headers
  - Tavsiyalar

### Test 4: Job ro'yxati

```
/jobs
```

**Kutilgan natija:**
- Oxirgi 10 ta job ro'yxati ko'rsatiladi
- Har bir job uchun ID, buyruq va holat ko'rsatiladi

### Test 5: Job holati

Avval `/jobs` buyrug'i bilan job ID ni oling, keyin:

```
/job <job_id>
```

**Kutilgan natija:**
- Job haqida batafsil ma'lumot
- Agar report mavjud bo'lsa, Markdown fayl yuboriladi

## 🏗️ Build test (ixtiyoriy)

**Eslatma:** Bu test uchun Flutter SDK o'rnatilgan bo'lishi kerak.

```
/build_weather_apk
```

**Kutilgan natija:**
- Bot "🏗️ Weather app APK yaratilmoqda..." xabari yuboradi
- Bir necha daqiqadan keyin:
  - APK fayli yuboriladi (agar muvaffaqiyatli bo'lsa)
  - Build hisoboti yuboriladi
  - Kod GitHub'ga push qilinadi (agar sozlangan bo'lsa)

## 🔍 Tuzatish

### Bot javob bermayapti

1. Service ishlayaptimi?
   ```bash
   sudo systemctl status autobuilder
   ```

2. Loglarni tekshiring:
   ```bash
   sudo journalctl -u autobuilder -f
   ```

3. Bot token to'g'rimi?
   ```bash
   sudo grep bot_token /etc/autobuilder/config.toml
   ```

### Joblar bajarilmayapti

1. Database mavjudmi?
   ```bash
   ls -la /opt/autobuilder/storage/jobs.db
   ```

2. Workspace papkalari yaratiladimi?
   ```bash
   ls -la /opt/autobuilder/workspaces/
   ```

3. Permissions to'g'rimi?
   ```bash
   sudo chown -R autobuilder:autobuilder /opt/autobuilder
   ```

### APK build ishlamayapti

1. Flutter o'rnatilganmi?
   ```bash
   flutter --version
   ```

2. Android SDK mavjudmi?
   ```bash
   echo $ANDROID_HOME
   ```

3. Java o'rnatilganmi?
   ```bash
   java -version
   ```

## ✅ Muvaffaqiyatli test natijalari

Agar barcha testlar muvaffaqiyatli bo'lsa:

- ✅ Bot javob beradi
- ✅ `/status` buyrug'i hisobot yuboradi
- ✅ `/audit_site` buyrug'i xavfsizlik hisoboti yuboradi
- ✅ `/jobs` buyrug'i job ro'yxatini ko'rsatadi
- ✅ Joblar to'g'ri bajariladi va hisobotlar yuboriladi

## 📝 Qo'shimcha tekshiruvlar

### Database tozalash

```bash
# SQLite database'ni ko'rish
sqlite3 /opt/autobuilder/storage/jobs.db "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

### Log fayllarini ko'rish

```bash
# Application loglari
sudo tail -f /var/log/autobuilder/bot.log

# Systemd loglari
sudo journalctl -u autobuilder -f
```

### Disk foydalanishini tekshirish

```bash
# Workspace hajmini ko'rish
du -sh /opt/autobuilder/workspaces/*

# Reports hajmini ko'rish
du -sh /opt/autobuilder/reports/*
```

