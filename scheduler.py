"""
SOKIN QALB — kunlik rejalashtiruvchi (scheduler).

Har kuni belgilangan vaqtda:
  1) diagnostikadan o'tgan barcha faol foydalanuvchilarga kunlik topshiriq + darslik/meditatsiya
     yuboriladi va kurs kuni bittaga oshiriladi;
  2) kechqurun hali kuzatuv (check-in) qilmagan foydalanuvchilarga eslatma yuboriladi.
"""
import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import database as db
import ai_service
from config import TIMEZONE, DAILY_CONTENT_TIME, DAILY_CHECKIN_TIME
from handlers.tasks import send_daily_task
from handlers.content import send_daily_lesson
from keyboards import daily_tasks_checklist_kb

logger = logging.getLogger(__name__)


async def _job_send_daily_content(bot: Bot) -> None:
    users = await db.get_all_active_users()
    for user in users:
        if not user["diagnostic_done"]:
            continue
        try:
            course_day = await db.advance_course_day(user["id"])
            await send_daily_lesson(bot, user["telegram_id"], user["id"], course_day - 1)
            await send_daily_task(bot, user["telegram_id"], user["id"], course_day - 1)
        except Exception:
            logger.exception("Foydalanuvchi %s uchun kunlik kontent yuborishda xatolik", user["telegram_id"])


async def _job_checkin_and_task_reminder(bot: Bot) -> None:
    users = await db.get_all_active_users()
    for user in users:
        if not user["diagnostic_done"]:
            continue
        try:
            # 1. Topshiriqlar eslatmasi (agar bajarilmagan topshiriqlari bo'lsa)
            task_stats = await db.get_today_task_stats(user["id"])
            if task_stats["total"] > 0 and task_stats["completed"] < task_stats["total"]:
                pending_titles = [t["task_title"] for t in task_stats["tasks"] if not t["is_done"]]
                reminder_msg = await ai_service.generate_task_reminder_message(
                    user_name=user["full_name"],
                    completed=task_stats["completed"],
                    total=task_stats["total"],
                    pending_tasks=pending_titles,
                )
                await bot.send_message(
                    user["telegram_id"],
                    f"🔔 <b>Kunlik topshiriqlar eslatmasi:</b>\n\n{reminder_msg}",
                    parse_mode="HTML",
                    reply_markup=daily_tasks_checklist_kb(task_stats["tasks"]),
                )

            # 2. Check-in eslatmasi
            if not await db.has_checked_in_today(user["id"]):
                await bot.send_message(
                    user["telegram_id"],
                    "🌙 <b>Kun yakunlanmoqda!</b>\n\nBugungi kayfiyat, stress, yutuq va qiyinchiliklaringizni "
                    "qayd etishni unutmang — bu bor-yo'g'i 1 daqiqa vaqt oladi 🌿",
                    parse_mode="HTML",
                )
        except Exception:
            logger.exception("Foydalanuvchi %s uchun eslatmada xatolik", user["telegram_id"])


async def _job_weekly_four_pillars_reminder(bot: Bot) -> None:
    """Har hafta yakshanba kuni 4 ta hayotiy ustunni yangilash eslatmasi."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    users = await db.get_all_active_users()
    for user in users:
        if not user["diagnostic_done"]:
            continue
        try:
            kb = InlineKeyboardBuilder()
            kb.button(text="⚖️ Haftalik So'rovnomani Boshlash", callback_data="start_four_pillars")
            kb.button(text="📝 Sokin Qaydlar", callback_data="sokin_qaydlar")
            kb.adjust(1)
            await bot.send_message(
                user["telegram_id"],
                "📊 <b>HAFTALIK 4 TA HAYOTIY USTUN MONITORINGI</b> 🌿\n\n"
                "Bugun haftalik yakuniy hisob-kitob vaqti!\n"
                "Moliyaviy, ruhiy, jismoniy va munosabatlar holatingizni yangilab, "
                "o'tgan haftadagi o'zgarishlaringizni ko'ring va <b>10 dan 10 natijaga</b> chiqish yo'l xaritasini oling 👇",
                parse_mode="HTML",
                reply_markup=kb.as_markup(),
            )
        except Exception:
            logger.exception("Foydalanuvchi %s uchun haftalik 4 ustun eslatmasida xatolik", user["telegram_id"])


async def _job_hourly_task_reminders(bot: Bot) -> None:
    """Soatma-soat topshiriqlarni aniq vaqtida eslatish va tasdiq olish."""
    from datetime import datetime
    import pytz
    from keyboards import task_reminder_prompt_kb

    tz = pytz.timezone(TIMEZONE)
    now_dt = datetime.now(tz)
    current_time_str = now_dt.strftime("%H:%M")

    try:
        pending_tasks = await db.get_pending_hourly_tasks(current_time_str)
        for task in pending_tasks:
            try:
                title = task.get("task_title") or task.get("task_text", "Topshiriq")
                desc = task.get("task_desc", "")
                benefit = task.get("task_benefit", "")
                t_time = task.get("scheduled_time", "Hozir")

                text = (
                    f"🔔 <b>VAQT BO'LDI! KELING, BIRGALIKDA BAJARAMIZ!</b> 🌿\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏰ <b>Rejalashtirilgan vaqt:</b> [{t_time}]\n"
                    f"🎯 <b>Topshiriq:</b> <b>{title}</b>\n\n"
                )
                if desc:
                    text += f"🤝 <i>{desc}</i>\n\n"
                if benefit:
                    text += f"💡 <b>Foydasi:</b> <i>{benefit}</i>\n\n"

                text += (
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "<i>Keling, ushbu kichik qadamni rohatlanib bajaramiz va orzularimizga yanada yaqinlashamiz! ✨\n"
                    "Bajarib bo'lgach, 'Ha, bajardim' tugmasini bosing 👇</i>"
                )

                await bot.send_message(
                    task["telegram_id"],
                    text,
                    parse_mode="HTML",
                    reply_markup=task_reminder_prompt_kb(task["id"]),
                )
                await db.increment_task_reminder(task["id"])
            except Exception:
                logger.exception("Topshiriq %s eslatmasini yuborishda xatolik", task.get("id"))
    except Exception:
        logger.exception("Soatlik topshiriqlar monitoringida umumiy xatolik")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    content_hour, content_minute = map(int, DAILY_CONTENT_TIME.split(":"))
    checkin_hour, checkin_minute = map(int, DAILY_CHECKIN_TIME.split(":"))

    scheduler.add_job(
        _job_send_daily_content,
        trigger=CronTrigger(hour=content_hour, minute=content_minute, timezone=TIMEZONE),
        args=[bot],
        id="daily_content",
        replace_existing=True,
    )
    scheduler.add_job(
        _job_checkin_and_task_reminder,
        trigger=CronTrigger(hour=checkin_hour, minute=checkin_minute, timezone=TIMEZONE),
        args=[bot],
        id="checkin_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        _job_weekly_four_pillars_reminder,
        trigger=CronTrigger(day_of_week="sun", hour=19, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="weekly_four_pillars_reminder",
        replace_existing=True,
    )
    # Har 15 daqiqada soatma-soat topshiriqlar jadvalini tekshirish
    scheduler.add_job(
        _job_hourly_task_reminders,
        trigger=CronTrigger(minute="*/15", timezone=TIMEZONE),
        args=[bot],
        id="hourly_task_reminders",
        replace_existing=True,
    )
    return scheduler
