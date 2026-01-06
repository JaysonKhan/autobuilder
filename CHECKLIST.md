# Pre-Deployment Checklist

Production'ga o'rnatishdan oldin tekshirilishi kerak bo'lgan barcha narsalar.

## ✅ Kod va Fayllar

- [x] Barcha source fayllar yaratilgan
- [x] Config example fayli mavjud
- [x] Requirements.txt to'liq
- [x] Install script tayyor
- [x] Systemd service fayli tayyor
- [x] Hujjatlar yaratilgan

## ⚙️ Konfiguratsiya

- [ ] Bot token olingan (@BotFather)
- [ ] Chat ID olingan (@userinfobot)
- [ ] `/etc/autobuilder/config.toml` yaratilgan va to'ldirilgan
- [ ] Config fayl permissions: `chmod 600`
- [ ] GitHub SSH kalit yaratilgan (agar kerak bo'lsa)
- [ ] GitHub SSH kalit GitHub'ga qo'shilgan (agar kerak bo'lsa)

## 🛠️ O'rnatish

- [ ] `install.sh` scripti muvaffaqiyatli ishladi
- [ ] `autobuilder` user yaratilgan
- [ ] Virtual environment yaratilgan
- [ ] Python paketlar o'rnatilgan
- [ ] Systemd service o'rnatilgan
- [ ] Log rotation sozlangan

## 🧪 Test

- [ ] Service ishlayapti: `sudo systemctl status autobuilder`
- [ ] Bot javob beradi: `/start` buyrug'i
- [ ] Server holati ishlaydi: `/status` buyrug'i
- [ ] Xavfsizlik tekshiruvi ishlaydi: `/audit_site` buyrug'i
- [ ] Job ro'yxati ishlaydi: `/jobs` buyrug'i
- [ ] Loglar to'g'ri yozilmoqda

## 🔒 Xavfsizlik

- [ ] Config fayl faqat root o'qiy oladi
- [ ] Service dedicated user'da ishlaydi
- [ ] Workspace permissions to'g'ri
- [ ] Log fayllar xavfsiz
- [ ] Sensitive ma'lumotlar redact qilinmoqda

## 📊 Monitoring

- [ ] Loglar ko'rinmoqda: `sudo journalctl -u autobuilder`
- [ ] Database yaratilgan: `/opt/autobuilder/storage/jobs.db`
- [ ] Workspace papkalari yaratilmoqda
- [ ] Reportlar yaratilmoqda

## 🚀 Production Ready

- [ ] Barcha testlar o'tdi
- [ ] Xatoliklar yo'q
- [ ] Performance qoniqarli
- [ ] Hujjatlar to'liq
- [ ] Backup strategiyasi aniqlangan

## 📝 Qo'shimcha (ixtiyoriy)

- [ ] Flutter SDK o'rnatilgan (APK build uchun)
- [ ] Android SDK sozlangan (APK build uchun)
- [ ] MariaDB sozlangan (agar SQLite o'rniga)
- [ ] Webhook sozlangan (agar long polling o'rniga)
- [ ] Custom domain sozlangan

## ✅ Tayyor!

Agar barcha punktlar belgilangan bo'lsa, loyiha production'ga tayyor!

