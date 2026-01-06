# Architecture Documentation

AutoBuilder Bot arxitekturasining batafsil tavsifi.

## 🏗️ Umumiy arxitektura

```
┌─────────────────┐
│  Telegram Bot   │
│   (python-telegram-bot)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Command        │
│  Handlers       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Job Manager    │
│  (SQLite/MariaDB)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Job Executor   │
│  (Async Tasks)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Task Modules   │
│  (status, audit,│
│   build, etc.) │
└─────────────────┘
```

## 📁 Fayl tuzilishi

### `src/main.py`
- Bot'ning asosiy kirish nuqtasi
- Telegram bot'ni ishga tushiradi
- Signal handlerlar va graceful shutdown

### `src/telegram/handlers.py`
- Barcha Telegram buyruqlarini qayta ishlaydi
- `/start`, `/status`, `/audit_site`, `/build_weather_apk`, va boshqalar
- Job'lar yaratadi va natijalarni yuboradi

### `src/jobs/job_manager.py`
- Job queue boshqaruvi
- SQLite yoki MariaDB'da job'lar saqlanadi
- Job holatini kuzatadi (pending, running, completed, failed)

### `src/jobs/job_executor.py`
- Job'lar asinxron bajariladi
- Workspace'lar yaratadi va tozalaydi
- Loglarni redact qiladi

### `src/tasks/`
- **system_status.py**: Server holatini tekshiradi
- **audit_public_site.py**: Xavfsizlik tekshiruvi
- **build_android_apk.py**: Android APK yaratadi
- **github_push.py**: GitHub'ga kod push qiladi

### `src/utils/`
- **config.py**: Konfiguratsiyani yuklaydi
- **shell.py**: Xavfsiz shell buyruqlarini bajaradi
- **markdown.py**: Markdown hisobotlar yaratadi
- **redact.py**: Sensitive ma'lumotlarni yashiradi

## 🔄 Job Lifecycle

```
1. User buyruq yuboradi (/status, /audit_site, etc.)
   │
   ▼
2. Handler job yaratadi (JobManager.create_job)
   │
   ▼
3. JobExecutor job'ni bajaradi
   │
   ├─► Workspace yaratadi
   ├─► Task'ni bajaradi
   ├─► Report yaratadi
   └─► Job holatini yangilaydi
   │
   ▼
4. Handler natijani Telegram'ga yuboradi
   │
   ▼
5. Workspace tozalanadi
```

## 🔒 Xavfsizlik

### 1. Shell Buyruqlari
- `ShellRunner` xavfsiz buyruqlarni bajaradi
- Timeout bilan
- Xavfli buyruqlar bloklanadi
- Working directory cheklangan

### 2. Ma'lumotlar Yashirish
- `Redactor` sensitive patternlarni yashiradi
- Loglar va hisobotlarda parollar ko'rsatilmaydi
- Config fayllar `chmod 600` bilan himoyalangan

### 3. Resource Limits
- Maksimal job vaqti: 30 daqiqa
- Maksimal disk: 5GB per job
- Auto-cleanup eski job'lar va reportlar

### 4. Permissions
- Service `autobuilder` user'da ishlaydi
- Faqat kerakli papkalarga yozish huquqi
- Systemd security sozlamalari

## 💾 Ma'lumotlar Bazasi

### SQLite (default)
- Fayl: `/opt/autobuilder/storage/jobs.db`
- Schema:
  ```sql
  CREATE TABLE jobs (
      id TEXT PRIMARY KEY,
      command TEXT NOT NULL,
      status TEXT NOT NULL,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      completed_at TIMESTAMP,
      logs_path TEXT,
      report_path TEXT,
      error_message TEXT,
      metadata TEXT
  )
  ```

### MariaDB (ixtiyoriy)
- Connection string: `mysql://user:pass@host:port/db`
- Xuddi shu schema

## 📊 Report Format

Har bir report Markdown formatida:

```markdown
# Title

## Summary
Status: ✅ GREEN / ⚠️ YELLOW / ❌ RED

## Findings
| Severity | Title | Description |
|----------|-------|-------------|

## Recommendations
1. Recommendation 1
2. Recommendation 2

## What Was Checked
- Item 1
- Item 2
```

## 🔧 Konfiguratsiya

Konfiguratsiya TOML formatida:
- Production: `/etc/autobuilder/config.toml`
- Development: `config/config.toml`

Asosiy sozlamalar:
- Telegram bot token va chat ID
- Database turi va connection
- GitHub SSH kalit va repo
- Security limits
- Path'lar

## 🚀 Deployment

### Systemd Service
- Service fayl: `/etc/systemd/system/autobuilder.service`
- User: `autobuilder`
- Auto-restart: enabled
- Logs: `journalctl -u autobuilder`

### Log Rotation
- Config: `/etc/logrotate.d/autobuilder`
- Retention: 14 kun
- Compression: enabled

## 📈 Kengaytirish

Yangi task qo'shish:

1. `src/tasks/` papkasida yangi fayl yaratish
2. `execute()` metodini implement qilish
3. `src/telegram/handlers.py` da handler qo'shish
4. `/help` buyrug'iga qo'shish

Misol:
```python
# src/tasks/my_task.py
class MyTask:
    def execute(self, job_id, workspace_dir, logs_path, report_path):
        # Task logic
        pass
```

## 🔍 Monitoring

- Loglar: `/var/log/autobuilder/bot.log`
- Systemd logs: `journalctl -u autobuilder`
- Job holati: `/jobs` buyrug'i
- Database: SQLite yoki MariaDB query'lar

## 🛠️ Maintenance

### Cleanup
- Eski job'lar: 30 kundan keyin
- Reportlar: 7 kundan keyin
- Workspace'lar: job tugagandan keyin

### Backup
- Database: SQLite faylini backup qilish
- Config: `/etc/autobuilder/config.toml` ni backup qilish

### Updates
1. Code'ni yangilash
2. Dependencies yangilash: `pip install -r requirements.txt --upgrade`
3. Service'ni qayta ishga tushirish: `sudo systemctl restart autobuilder`

