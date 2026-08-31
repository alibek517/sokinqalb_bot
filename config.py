"""
SOKIN QALB — konfiguratsiya moduli.
Barcha maxfiy va sozlanadigan qiymatlar .env faylidan o'qiladi.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"'{name}' muhit o'zgaruvchisi topilmadi. "
            f".env faylini .env.example asosida to'ldiring."
        )
    return value


BOT_TOKEN = _require("BOT_TOKEN")
GEMINI_API_KEY = _require("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # ixtiyoriy — bo'sh bo'lishi mumkin
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID) if ADMIN_CHAT_ID and ADMIN_CHAT_ID.strip().isdigit() else None

# Bir nechta admin ID lari: .env da ADMIN_IDS="12345,67890" yoki ADMIN_ID="12345,67890" dan olinadi
_raw_admin_ids = os.getenv("ADMIN_IDS", "") or os.getenv("ADMIN_ID", "")
ADMIN_IDS: list[int] = []
if _raw_admin_ids:
    for part in str(_raw_admin_ids).split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.append(int(part))
if ADMIN_CHAT_ID and ADMIN_CHAT_ID not in ADMIN_IDS:
    ADMIN_IDS.append(ADMIN_CHAT_ID)


def is_admin(telegram_id: int) -> bool:
    """Foydalanuvchi admin yoki yo'qligini tekshiradi."""
    return telegram_id in ADMIN_IDS

DATABASE_PATH = os.getenv("DATABASE_PATH", "sokinqalb.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

DAILY_CONTENT_TIME = os.getenv("DAILY_CONTENT_TIME", "08:00")
DAILY_CHECKIN_TIME = os.getenv("DAILY_CHECKIN_TIME", "20:00")

FOUNDER_NAME = "Bagbekov Furqat"
BRAND_NAME = "SOKIN QALB"

# Majburiy obuna va ijtimoiy tarmoqlar sozlamalari
REQUIRED_CHANNEL_ID = os.getenv("REQUIRED_CHANNEL_ID", "@Sokin_Qalb_Furqat")
if REQUIRED_CHANNEL_ID in ("@sokin_qalb_rasmiy", "sokin_qalb_rasmiy"):
    REQUIRED_CHANNEL_ID = "@Sokin_Qalb_Furqat"

REQUIRED_CHANNEL_URL = os.getenv("REQUIRED_CHANNEL_URL", "https://t.me/Sokin_Qalb_Furqat")
if "sokin_qalb_rasmiy" in REQUIRED_CHANNEL_URL:
    REQUIRED_CHANNEL_URL = "https://t.me/Sokin_Qalb_Furqat"

REQUIRED_INSTAGRAM_URL = os.getenv("REQUIRED_INSTAGRAM_URL", "https://www.instagram.com/sokinqalb_tm?igsi=MTZyOGY0eDVnY25mdA==")
REQUIRED_YOUTUBE_URL = os.getenv("REQUIRED_YOUTUBE_URL", "https://www.youtube.com/@Sokin_Qalb_Furqat")

# Diagnostika yakunida yoki har qanday xavotirli javobda ko'rsatiladigan
# inson mutaxassisi bilan bog'lanish ma'lumoti.
CLINIC_CONTACT = "@sokinqalb_admin"
