"""
SOKIN QALB — Telegram bot uchun kirish nuqtasi.

Ishga tushirish:
    python bot.py

Talab qilinadi: .env fayli (.env.example asosida) to'ldirilgan bo'lishi kerak.
"""
import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from config import BOT_TOKEN
from handlers import register_all_handlers
from scheduler import setup_scheduler
from subscription import SubscriptionMiddleware, ReviewEnforcementMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await db.init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # FSM Storage (Agar .env da REDIS_URL bo'lsa Redis, aks holda MemoryStorage)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            storage = RedisStorage.from_url(redis_url)
            logger.info("Redis FSM Storage faollashtirildi.")
        except Exception:
            logger.warning("Redis kutubxonasi yoki ulanish mavjud emas, MemoryStorage ishlatilmoqda.")
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)

    # 1. Majburiy obuna tekshiruvi (Telegram kanal va Instagram)
    sub_middleware = SubscriptionMiddleware()
    dp.message.outer_middleware(sub_middleware)
    dp.callback_query.outer_middleware(sub_middleware)

    # 2. Majburiy haftalik va oylik monitoring tekshiruvi
    review_middleware = ReviewEnforcementMiddleware()
    dp.message.middleware(review_middleware)
    dp.callback_query.middleware(review_middleware)

    register_all_handlers(dp)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Rejalashtiruvchi (scheduler) ishga tushdi.")

    try:
        logger.info("SOKIN QALB boti ishga tushmoqda...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
