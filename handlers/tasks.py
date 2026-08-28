"""SOKIN QALB — 'Orzular tomon bir qadam': Shaxsiylashtirilgan Soatma-soat Topshiriqlar va Motivatsiya.

Foydalanuvchining psixologik diagnostikasi, 4 ta soha va suhbatlariga asoslanib,
soatma-soat maxsus topshiriqlar jadvali tuzadi, vaqti kelganda eslatadi,
tasdig'ini oladi va shaxsiy profil fotosi asosida kiberxavfsiz motivatsiyalar berib boradi.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import ai_service
from config import FOUNDER_NAME
from keyboards import daily_tasks_checklist_kb, task_reminder_prompt_kb, main_menu_kb

router = Router(name="tasks")
logger = logging.getLogger(__name__)


def _render_progress_bar(percent: int) -> str:
    """Foiz bo'yicha progress bar."""
    total_blocks = 10
    filled = max(0, min(total_blocks, round(percent / 10)))
    empty = total_blocks - filled
    return f"[{'🟩' * filled}{'⬜️' * empty}] {percent}%"


def _format_tasks_message(user_name: str, tasks: list[dict], percent: int, completed: int, total: int) -> str:
    """Topshiriqlar ro'yxati matnini formatlash."""
    bar = _render_progress_bar(percent)
    
    default_hours = ["07:00", "09:30", "13:30", "17:30", "21:30"]
    tasks_body = ""
    for i, t in enumerate(tasks):
        icon = "✅" if t.get("is_done") else "⏳"
        t_time = t.get("scheduled_time") or default_hours[i % len(default_hours)]
        title = t.get("task_title") or t.get("task_text", f"Topshiriq {i+1}")
        desc = t.get("task_desc", "")
        benefit = t.get("task_benefit", "")

        tasks_body += f"\n⏰ <b>[{t_time}]</b> {icon} <b>{title}</b>\n"
        if desc:
            tasks_body += f"   🤝 <i>{desc}</i>\n"
        if benefit:
            tasks_body += f"   💡 <i>Foydasi: {benefit}</i>\n"

    if total > 0 and completed == total:
        status_note = "🎉 <b>Ajoyib natija! Bugungi barcha orzular qadamini 100% bajardingiz!</b>"
    else:
        status_note = "🌿 <i>Keling, orzular sari navbatdagi qadamni birgalikda bajaramiz! Qilingan topshiriqni bosing 👇</i>"

    return (
        "🎯 <b>ORZULAR TOMON BIR QADAM — KUNDALIK SOATMA-SOAT REJA</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Qadrdonimiz:</b> {user_name}\n"
        f"📊 <b>Bugungi bajarilish ko'rsatkichi:</b> {completed}/{total} ta ({percent}%)\n"
        f"{bar}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Bugungi rejalashtirilgan harakatlar:</b>\n"
        f"{tasks_body}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_note}"
    )


async def send_daily_task(bot: Bot, telegram_id: int, user_id: int, course_day: int) -> None:
    """Ertalabki scheduler orqali kunlik soatma-soat topshiriqlarni yuborish."""
    user = await db.get_user_by_id(user_id)
    if not user:
        return

    diag = await db.get_first_diagnostic(user_id)
    recent_checkins = await db.get_recent_checkins(user_id, limit=3)

    ai_tasks = await ai_service.generate_personalized_daily_tasks(user, diag, recent_checkins)
    await db.save_daily_tasks(user_id, ai_tasks)

    stats = await db.get_today_task_stats(user_id)
    text = _format_tasks_message(
        user_name=user["full_name"],
        tasks=stats["tasks"],
        percent=stats["percent"],
        completed=stats["completed"],
        total=stats["total"],
    )

    try:
        await bot.send_message(
            telegram_id,
            text,
            parse_mode="HTML",
            reply_markup=daily_tasks_checklist_kb(stats["tasks"]),
        )
    except Exception:
        logger.exception("Foydalanuvchi %s ga kunlik topshiriq yuborishda xatolik", telegram_id)


# ---------- 1. 'Orzular tomon bir qadam' Bosh Menyusi ----------

@router.callback_query(F.data == "today_task")
async def show_today_task(callback: CallbackQuery, state: FSMContext) -> None:
    """Foydalanuvchi '🎯 Orzular tomon bir qadam' tugmasini bosganda."""
    await state.clear()
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    tasks = await db.get_today_tasks(user["id"])

    # Agar bugun uchun hali topshiriqlar shakllanmagan bo'lsa — AI orqali yaratamiz
    if not tasks:
        await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
        diag = await db.get_first_diagnostic(user["id"])
        recent_checkins = await db.get_recent_checkins(user["id"], limit=3)
        ai_tasks = await ai_service.generate_personalized_daily_tasks(user, diag, recent_checkins)
        tasks = await db.save_daily_tasks(user["id"], ai_tasks)

    stats = await db.get_today_task_stats(user["id"])
    text = _format_tasks_message(
        user_name=user["full_name"],
        tasks=stats["tasks"],
        percent=stats["percent"],
        completed=stats["completed"],
        total=stats["total"],
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=daily_tasks_checklist_kb(stats["tasks"]),
    )
    await callback.answer()


# ---------- 2. Topshiriqni Bajarilgan deb Belgilash (Toggle) ----------

@router.callback_query(F.data.startswith("task_toggle:"))
async def handle_task_toggle(callback: CallbackQuery) -> None:
    """Foydalanuvchi topshiriq tugmasini bosib, checkbox'ni almashtiradi."""
    task_id = int(callback.data.split(":")[1])
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    new_status, completed, total, percent = await db.toggle_task_done(task_id)
    stats = await db.get_today_task_stats(user["id"])

    text = _format_tasks_message(
        user_name=user["full_name"],
        tasks=stats["tasks"],
        percent=stats["percent"],
        completed=stats["completed"],
        total=stats["total"],
    )

    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=daily_tasks_checklist_kb(stats["tasks"]),
        )
    except Exception:
        pass

    if new_status:
        if percent == 100:
            await callback.answer("🎉 Barakalla! Barcha rejalarni 100% bajardingiz! Orzularingizga juda yaqinsiz!", show_alert=True)
        else:
            await callback.answer(f"✅ Qadam bajarildi! Ko'rsatkich: {percent}%", show_alert=False)
    else:
        await callback.answer(f"⏳ Bekor qilindi ({percent}%)", show_alert=False)


# ---------- 3. Soatlik Bildirishnoma Tasdig'i (Confirmation) ----------

@router.callback_query(F.data.startswith("task_confirm:"))
async def handle_task_confirm(callback: CallbackQuery) -> None:
    """Foydalanuvchi 'Ha, bajardim' tugmasi orqali eslatmani tasdiqlaganda."""
    task_id = int(callback.data.split(":")[1])
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)

    task = await db.complete_task(task_id)
    stats = await db.get_today_task_stats(user["id"])

    task_title = task.get("task_title", "Topshiriq") if task else "Topshiriq"

    text = (
        f"🎉 <b>BARAKALLA! TOPSHIRIQ TASDIQLANDI!</b> 🌿\n\n"
        f"✅ <b>{task_title}</b> muvaffaqiyatli bajarildi deb belgilandi.\n\n"
        f"📊 Bugungi ko'rsatkichingiz: <b>{stats['completed']}/{stats['total']} ta ({stats['percent']}%)</b>\n\n"
        f"<i>Siz har bir qadam bilan orzularingizga va ichki xotirjamlikka yanada yaqinlashmoqdasiz! ✨</i>"
    )

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=daily_tasks_checklist_kb(stats["tasks"]))
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=daily_tasks_checklist_kb(stats["tasks"]))

    await callback.answer("✅ Muvaffaqiyatli qayd etildi!")


@router.callback_query(F.data.startswith("task_snooze:"))
async def handle_task_snooze(callback: CallbackQuery) -> None:
    """Topshiriqni 15 daqiqadan keyin eslatish."""
    await callback.answer("⏳ Yaxshi, birozdan so'ng yana birgalikda eslatamiz!", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass


# ---------- 4. Dinamik Matnli AI Motivatsiyasini Ko'rish ----------

@router.callback_query(F.data == "get_dynamic_motivation")
async def show_dynamic_motivation(callback: CallbackQuery) -> None:
    """Foydalanuvchiga har safar yangi, ilhomlantiruvchi matnli motivatsiya taqdim etish."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)

    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    motivation_text = await ai_service.generate_dynamic_motivation(user)
    stats = await db.get_today_task_stats(user["id"])

    text = (
        "✨ <b>KUNDALIK SHAXSIY MOTIVATSIYA & ILHOM</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{motivation_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"— <i>{FOUNDER_NAME}</i>"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=daily_tasks_checklist_kb(stats["tasks"]),
    )
    await callback.answer()


# ---------- 5. AI Rejasini Qayta Tuzish (Refresh) ----------

@router.callback_query(F.data == "refresh_ai_tasks")
async def refresh_ai_tasks(callback: CallbackQuery) -> None:
    """Foydalanuvchi yangi soatma-soat AI reja so'raganda."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    diag = await db.get_first_diagnostic(user["id"])
    recent_checkins = await db.get_recent_checkins(user["id"], limit=3)

    ai_tasks = await ai_service.generate_personalized_daily_tasks(user, diag, recent_checkins)
    tasks = await db.save_daily_tasks(user["id"], ai_tasks)
    stats = await db.get_today_task_stats(user["id"])

    text = _format_tasks_message(
        user_name=user["full_name"],
        tasks=stats["tasks"],
        percent=stats["percent"],
        completed=stats["completed"],
        total=stats["total"],
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=daily_tasks_checklist_kb(stats["tasks"]),
    )
    await callback.answer("🔄 Yangi soatma-soat reja tuzildi!")
