# SOKIN QALB — Telegram bot

Sun'iy intellekt asosida ishlaydigan, foydalanuvchini doimiy kuzatib boradigan
psixosomatik yordamchi bot. Python + [aiogram 3](https://docs.aiogram.dev) +
[Google Gemini API](https://ai.google.dev/gemini-api/docs) asosida qurilgan.

## Imkoniyatlar

| Funksiya | Tavsif |
|---|---|
| 🧠 AI diagnostika | 8 ta savol orqali holatni aniqlaydi, Claude API yordamida tahlil qiladi, 5 kunlik kirish dasturi tuziladi |
| 📝 Kunlik kuzatuv | Har kuni kayfiyat/stress darajasi (1–10) va ixtiyoriy izoh qayd etiladi |
| ✅ Kunlik topshiriqlar | Har kuni yangi amaliy mashq beriladi, bajarilishi tugma orqali nazorat qilinadi |
| 📖 Kunlik darslik + meditatsiya | Asoschi nomidan kunlik qisqa dars va meditatsiya matni yuboriladi |
| 📊 Progress | Foydalanuvchi so'nggi 7 kunlik kuzatuvini va o'rtacha ko'rsatkichlarni ko'radi |
| 🛡️ Xavfsizlik filtri | O'z-o'ziga zarar berish xavfi haqidagi javob AI tahlilini chetlab o'tib, darhol inson mutaxassisga yo'naltiradi |
| ⏰ Avtomatik jadval | Har kuni belgilangan vaqtda kontent yuboriladi va kechqurun kuzatuv eslatmasi keladi (APScheduler) |

## Loyiha tuzilishi

```
sokinqalb_bot/
├── bot.py                 # Kirish nuqtasi (polling ishga tushiradi)
├── config.py               # .env dan sozlamalarni o'qiydi
├── database.py              # aiosqlite ustidagi barcha DB funksiyalar
├── ai_service.py            # Claude API bilan ishlash (diagnostika tahlili)
├── scheduler.py              # Kunlik avtomatik xabarlar (APScheduler)
├── keyboards.py              # Inline tugmalar
├── states.py                 # aiogram FSM holatlari
├── data/
│   └── content.py            # Kunlik topshiriq/darslik/meditatsiya matnlari
├── handlers/
│   ├── start.py               # /start
│   ├── diagnostics.py          # AI diagnostika oqimi
│   ├── checkin.py              # Kunlik kayfiyat/stress kuzatuvi
│   ├── tasks.py                 # Kunlik topshiriqlar
│   ├── content.py               # Kunlik darslik/meditatsiya
│   └── menu.py                   # Progress va mutaxassis bilan bog'lanish
├── requirements.txt
└── .env.example
```

## O'rnatish

1. **Python 3.11+** o'rnatilganiga ishonch hosil qiling.

2. Virtual muhit yarating va kutubxonalarni o'rnating:

   ```bash
   python3 -m venv venv
   source venv/bin/activate          # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. `.env.example` faylini nusxalab `.env` nomida saqlang va qiymatlarni to'ldiring:

   ```bash
   cp .env.example .env
   ```

   - `BOT_TOKEN` — [@BotFather](https://t.me/BotFather) orqali oling.
  - `GEMINI_API_KEY` — [Google AI Studio](https://aistudio.google.com/apikey) dan oling.
  - `GEMINI_MODEL` — odatda `gemini-2.5-flash` qoldiriladi.
   - `ADMIN_CHAT_ID` — ixtiyoriy, keyingi bosqichda admin xabarnomalari uchun.
   - `CLINIC_CONTACT` (config.py ichida) — real Telegram username yoki telefon raqamiga almashtiring.

4. Botni ishga tushiring:

   ```bash
   python bot.py
   ```

   Birinchi ishga tushishda `sokinqalb.db` fayli avtomatik yaratiladi.

## Muhim: mazmunni to'ldirish

`data/content.py` faylidagi `DAILY_TASKS` va `DAILY_LESSONS` — namuna matnlar.
Real loyihada bu yerga:

- Bagbekov Furqatning haqiqiy video/audio darslarini (Telegram `file_id` orqali
  `bot.send_video` / `bot.send_audio` bilan) ulashingiz,
- yoki bulutdagi (YouTube, Google Drive) havolalarni qo'shishingiz kerak.

## Xavfsizlik va halollik bo'yicha eslatmalar

- `ai_service.py` ichidagi tizim ko'rsatmasi AI'ga **tibbiy tashxis qo'ymaslik**ni
  qat'iy talab qiladi — bu botning huquqiy va axloqiy xavfsizligi uchun muhim.
  Bu qoidani yumshatmang.
- Diagnostikadagi so'nggi savol xavfsizlik skriningi hisoblanadi — agar
  foydalanuvchi o'z-o'ziga/boshqalarga zarar berish haqida ijobiy javob bersa,
  bot avtomatik tahlilni to'xtatib, darhol inson mutaxassisga yo'naltiradi.
  Bu qismni olib tashlamang yoki zaiflashtirmang.
- `CLINIC_CONTACT` doim haqiqiy va ishlaydigan aloqa kanaliga yo'naltirilishi
  kerak — bu xavfsizlik oqimining markaziy qismi.

## Keyingi qadamlar (production uchun tavsiyalar)

- **Webhook rejimi**: `dp.start_polling()` o'rniga production serverda
  webhook (masalan `aiohttp` bilan) ishlatish tavsiya etiladi.
- **Ma'lumotlar bazasi**: foydalanuvchilar ko'payganda SQLite o'rniga
  PostgreSQL'ga o'tish tavsiya etiladi.
- **Shaxsiy ma'lumotlar himoyasi**: O'zbekiston qonunchiligi talablariga mos
  ravishda foydalanuvchi ma'lumotlarini saqlash va ishlov berish siyosatini
  ishlab chiqing (rozilik, o'chirish huquqi va h.k.).
- **Monitoring**: `ADMIN_CHAT_ID` orqali xavfsizlik flagi (`risk_flag`)
  ko'tarilgan holatlar haqida adminlarga avtomatik xabar yuborishni qo'shish
  mumkin (hozircha bu funksiya asosiy oqimga kiritilmagan — qo'shimcha
  privacy siyosati bilan birga joriy etilishi tavsiya etiladi).
