"""SOKIN QALB — To'liq Admin Panel Moduli.

Admin funktsiyalari:
- 📊 Jonli statistika va ko'rsatkichlar
- ⚠️ Xavfli holatlar (Risk Alerts) nazorati
- 👥 Foydalanuvchilar ro'yxati (sahifalash) va qidiruv
- 🔍 Foydalanuvchi batafsil kartasi va to'g'ridan-to'g'ri xabar yozish
- 🚫 Foydalanuvchini bloklash / faollashtirish
- 📢 Barcha a'zolarga xabar tarqatish (Rassilka / Broadcast)
- 🤖 AI Post Generator (tayyor post yaratish va yuborish)
- 🧠 AI Auditoriya Tahlili
"""
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import database as db
import ai_service
from config import is_admin, FOUNDER_NAME
from keyboards import (
    admin_menu_kb,
    admin_broadcast_confirm_kb,
    admin_users_pagination_kb,
    admin_user_card_kb,
    back_to_admin_kb,
    main_menu_kb,
    admin_courses_list_kb,
    admin_course_lessons_kb,
    admin_material_manage_kb,
    admin_course_manage_kb,
    admin_team_list_kb,
    admin_team_member_manage_kb,
    admin_gifts_list_kb,
    admin_gift_manage_kb,
    payment_receipt_review_kb,
)
from states import (
    AdminBroadcast,
    AdminUserSearch,
    AdminDirectMessage,
    AdminAIPost,
    AdminCourseManagement,
    AdminTeamManagement,
    AdminGiftManagement,
    AdminCourseEdit,
)

router = Router(name="admin")
logger = logging.getLogger(__name__)


def _check_admin(telegram_id: int) -> bool:
    return is_admin(telegram_id)


# ---------- 1. Admin Panel Bosh Menyusi ----------

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        await message.answer("Kechirasiz, sizda admin huquqlari yo'q.")
        return
    await state.clear()
    text = (
        f"👑 <b>SOKIN QALB — Boshqaruv Paneli (Admin)</b>\n\n"
        f"Assalomu alaykum! Kerakli bo'limni tanlang 👇"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "open_admin_panel")
async def cb_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q!", show_alert=True)
        return
    await state.clear()
    text = (
        f"👑 <b>SOKIN QALB — Boshqaruv Paneli (Admin)</b>\n\n"
        f"Kerakli bo'limni tanlang 👇"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_menu_kb())
    await callback.answer()


def _render_bar(val: float, max_val: float = 10.0, length: int = 10) -> str:
    """Vizual progress bar (Unicode) chizish."""
    filled = int(round((max(0.0, min(val, max_val)) / max_val) * length))
    return "█" * filled + "░" * (length - filled)


# ---------- 2. Jonli Dashboard va Vizual Statistika ----------

@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    stats = await db.get_admin_dashboard_stats()
    
    # 4 ta ustun progress barlari
    fin_bar = _render_bar(stats['avg_fin'])
    men_bar = _render_bar(stats['avg_men'])
    phys_bar = _render_bar(stats['avg_phys'])
    rel_bar = _render_bar(stats['avg_rel'])
    
    diag_percent = round((stats['diag_done'] / stats['total_users'] * 100), 1) if stats['total_users'] > 0 else 0

    text = (
        "📊 <b>SOKIN QALB — VIZUAL ADMIN DASHBOARD</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👥 <b>FOYDALANUVCHILAR VORONKASI (FUNNEL):</b>\n"
        f"• Jami a'zolar: <b>{stats['total_users']} ta</b>\n"
        f"• Faol a'zolar: <b>{stats['active_users']} ta</b>\n"
        f"• Diagnostikadan o'tganlar: <b>{stats['diag_done']} ta ({diag_percent}%)</b>\n"
        f"• Bugun yangi qo'shilgan: <b>+{stats['today_new']} ta</b>\n"
        f"• Jami check-inlar: <b>{stats['total_checkins']} ta</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚖️ <b>4 TA HAYOTIY USTUN O'RTACHA KO'RSATKICHLARI:</b>\n"
        f"💰 Moliya:       <code>[{fin_bar}]</code> <b>{stats['avg_fin']}/10</b>\n"
        f"🧘 Ruhiyat:      <code>[{men_bar}]</code> <b>{stats['avg_men']}/10</b>\n"
        f"🏃 Tana/Quvvat:  <code>[{phys_bar}]</code> <b>{stats['avg_phys']}/10</b>\n"
        f"👥 Munosabatlar: <code>[{rel_bar}]</code> <b>{stats['avg_rel']}/10</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💳 <b>SAVDO VA TO'LOVLAR NATIJALARI:</b>\n"
        f"• Tasdiqlangan sotuvlar: <b>{stats['total_sales']} ta</b>\n"
        f"• Jami tushum: <b>{stats['total_revenue']:,} so'm</b>\n"
        f"⚠️ Xavf guruhidagi a'zolar: <b>{stats['risk_count']} ta</b>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


# ---------- 3. Xavfli Holatlar (Risk Alerts) ----------

@router.callback_query(F.data == "admin_risk_cases")
async def cb_admin_risk_cases(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    risk_users = await db.get_risk_users()
    if not risk_users:
        await callback.message.answer(
            "✅ <b>Xavf guruhida foydalanuvchilar mavjud emas!</b>\n\n"
            "Barcha foydalanuvchilar diagnostikadan muammosiz o'tgan.",
            parse_mode="HTML",
            reply_markup=back_to_admin_kb(),
        )
        await callback.answer()
        return

    text = f"⚠️ <b>Xavf aniqlangan foydalanuvchilar ({len(risk_users)} ta):</b>\n\n"
    for idx, u in enumerate(risk_users[:10], start=1):
        username_str = f"@{u['username']}" if u['username'] else "mavjud emas"
        text += (
            f"{idx}. <b>{u['full_name']}</b> ({username_str})\n"
            f"   🆔 ID: <code>{u['telegram_id']}</code> (Baza ID: {u['id']})\n"
            f"   📅 Sana: {u['diag_date'][:10]}\n"
            f"   💬 Mutaxassis Xulosasi: <i>{u.get('ai_summary', '')[:100]}...</i>\n\n"
        )

    text += "<i>Foydalanuvchiga to'g'ridan-to'g'ri xabar yozish uchun Qidiruv orqali uning ID sini kiriting.</i>"
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


# ---------- 4. Foydalanuvchilar Ro'yxati & Qidiruv ----------

@router.callback_query(F.data.startswith("admin_users:"))
async def cb_admin_users(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    page = int(callback.data.split(":")[1])
    users, total_pages = await db.get_users_paginated(page=page, page_size=6)

    if not users:
        await callback.message.answer("Foydalanuvchilar topilmadi.", reply_markup=back_to_admin_kb())
        await callback.answer()
        return

    text = f"👥 <b>Foydalanuvchilar ro'yxati (Sahifa {page}/{total_pages}):</b>\n\n"
    for u in users:
        status_icon = "🟢" if u["is_active"] else "🔴"
        diag_icon = "🧠" if u["diagnostic_done"] else "⏳"
        username_str = f"@{u['username']}" if u['username'] else "username yo'q"
        text += (
            f"{status_icon} <b>{u['full_name']}</b> | {username_str}\n"
            f"   🆔 <code>{u['telegram_id']}</code> | Kun: {u['course_day']} | Diag: {diag_icon}\n"
            f"   🔗 Ko'rish: /user_{u['id']}\n\n"
        )

    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_users_pagination_kb(page, total_pages))
    await callback.answer()


@router.message(F.text.regexp(r"^/user_(\d+)$"))
async def cmd_user_details(message: Message) -> None:
    if not _check_admin(message.from_user.id):
        return
    user_id = int(message.text.split("_")[1])
    details = await db.get_user_full_details(user_id)
    if not details:
        await message.answer("Foydalanuvchi topilmadi.")
        return

    u = details["user"]
    diag = details["diagnostic"]
    checkins = details["checkins"]
    task = details["today_task"]

    status_str = "🟢 Faol" if u["is_active"] else "🔴 Bloklangan"
    diag_str = "✅ O'tgan" if u["diagnostic_done"] else "❌ O'tmagan"
    username_str = f"@{u['username']}" if u['username'] else "yo'q"

    text = (
        f"👤 <b>Foydalanuvchi Ma'lumotlari:</b>\n\n"
        f"• <b>Ism:</b> {u['full_name']}\n"
        f"• <b>Username:</b> {username_str}\n"
        f"• <b>Telegram ID:</b> <code>{u['telegram_id']}</code>\n"
        f"• <b>Baza ID:</b> {u['id']}\n"
        f"• <b>Ro'yxatdan o'tgan:</b> {u['created_at'][:10]}\n"
        f"• <b>Holat:</b> {status_str}\n"
        f"• <b>Kurs kuni:</b> {u['course_day']}-kun\n"
        f"• <b>Diagnostika:</b> {diag_str}\n\n"
    )

    if diag:
        focus_str = ", ".join(diag.get("focus_areas", [])) or "—"
        text += (
            f"🧠 <b>Diagnostika Tahlili:</b>\n"
            f"• Xulosa: <i>{diag.get('ai_summary', '—')}</i>\n"
            f"• Yo'nalishlar: {focus_str}\n"
            f"• Risk flag: {'⚠️ HA' if diag.get('risk_flag') else 'Yo\'q'}\n\n"
        )

    if checkins:
        text += "📝 <b>So'nggi kuzatuvlar:</b>\n"
        for c in checkins[:3]:
            note_str = f" (Izoh: {c['note']})" if c.get("note") else ""
            text += f"• {c['checkin_date']}: Kayfiyat {c['mood_score']}/10, Stress {c['stress_score']}/10{note_str}\n"
        text += "\n"

    if task:
        task_status = "✅ Bajarilgan" if task["is_done"] else "⏳ Kutilmoqda"
        text += f"📅 <b>Bugungi topshiriq:</b> {task['task_text'][:60]}... ({task_status})\n"

    await message.answer(text, parse_mode="HTML", reply_markup=admin_user_card_kb(u["id"], u["is_active"]))


@router.callback_query(F.data.startswith("admin_toggle_active:"))
async def cb_toggle_active(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split(":")[1])
    new_state = await db.toggle_user_active_by_id(user_id)
    status_text = "faollashtirildi ✅" if new_state else "bloklandi 🚫"
    await callback.message.answer(f"Foydalanuvchi (ID: {user_id}) holati o'zgartirildi: {status_text}")
    await callback.answer()


@router.callback_query(F.data == "admin_search_user")
async def cb_search_user(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.set_state(AdminUserSearch.waiting_query)
    await callback.message.answer(
        "🔍 <b>Foydalanuvchini qidirish:</b>\n\n"
        "Foydalanuvchining <b>Telegram ID</b>si, <b>@username</b>i yoki <b>Ismi</b>ni yozing:",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AdminUserSearch.waiting_query, F.text)
async def handle_user_search(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    query = message.text.strip()
    await state.clear()
    results = await db.search_users(query)
    if not results:
        await message.answer(f"'{query}' bo'yicha hech qanday foydalanuvchi topilmadi.", reply_markup=back_to_admin_kb())
        return

    text = f"🔍 <b>Qidiruv natijalari ({len(results)} ta):</b>\n\n"
    for u in results:
        status_icon = "🟢" if u["is_active"] else "🔴"
        username_str = f"@{u['username']}" if u['username'] else "yo'q"
        text += (
            f"{status_icon} <b>{u['full_name']}</b> ({username_str})\n"
            f"   🆔 <code>{u['telegram_id']}</code> | Baza ID: {u['id']}\n"
            f"   👉 Profilni ko'rish: /user_{u['id']}\n\n"
        )
    await message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())


# ---------- 5. Foydalanuvchiga To'g'ridan-to'g'ri Xabar Yozish ----------

@router.callback_query(F.data.startswith("admin_dm:"))
async def cb_admin_dm(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split(":")[1])
    target_user = await db.get_user_by_id(user_id)
    if not target_user:
        await callback.message.answer("Foydalanuvchi topilmadi.")
        await callback.answer()
        return

    await state.set_state(AdminDirectMessage.waiting_text)
    await state.update_data(target_user_id=user_id, target_telegram_id=target_user["telegram_id"], target_name=target_user["full_name"])

    await callback.message.answer(
        f"✉️ <b>{target_user['full_name']}</b> ga xabar yuborish:\n\n"
        f"Xabar matnini yozing. Ushbu xabar bot nomidan foydalanuvchiga yetkaziladi 👇",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AdminDirectMessage.waiting_text, F.text)
async def handle_direct_message(message: Message, state: FSMContext, bot: Bot) -> None:
    if not _check_admin(message.from_user.id):
        return
    data = await state.get_data()
    target_tg_id = data["target_telegram_id"]
    target_name = data["target_name"]
    dm_text = message.text.strip()
    await state.clear()

    try:
        await bot.send_message(
            target_tg_id,
            f"📩 <b>{FOUNDER_NAME} / Sokin Qalb ma'muriyatidan xabar:</b>\n\n{dm_text}",
            parse_mode="HTML",
        )
        await message.answer(f"✅ Xabar <b>{target_name}</b> ga muvaffaqiyatli yetkazildi!", parse_mode="HTML", reply_markup=back_to_admin_kb())
    except Exception as e:
        logger.exception("Direct message xatoligi")
        await message.answer(f"❌ Xabarni yetkazib bo'lmadi (Foydalanuvchi botni bloklagan bo'lishi mumkin): {e}", reply_markup=back_to_admin_kb())


# ---------- 6. Xabar Tarqatish (Broadcast / Rassilka) ----------

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_content)
    text = (
        "📢 <b>Barcha foydalanuvchilarga xabar tarqatish (Rassilka)</b>\n\n"
        "Yubormoqchi bo'lgan xabaringizni yozing yoki rasm/video bilan yuboring.\n\n"
        "<i>Eslatma: Keyingi bosqichda xabar ko'rib chiqiladi va tasdiqlanadi.</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


@router.message(AdminBroadcast.waiting_content)
async def handle_broadcast_content(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_confirm)
    await state.update_data(
        content_type=message.content_type,
        text=message.html_text or message.caption or "",
        photo_id=message.photo[-1].file_id if message.photo else None,
        video_id=message.video.file_id if message.video else None,
    )

    await message.answer("👁 <b>Xabar ko'rinishi (Preview):</b>\n👇👇👇")
    if message.photo:
        await message.answer_photo(photo=message.photo[-1].file_id, caption=message.caption, parse_mode="HTML")
    elif message.video:
        await message.answer_video(video=message.video.file_id, caption=message.caption, parse_mode="HTML")
    else:
        await message.answer(message.html_text, parse_mode="HTML")

    total_active = len(await db.get_all_user_telegram_ids())
    await message.answer(
        f"📢 Ushbu xabar <b>{total_active} ta</b> faol foydalanuvchiga yuboriladi.\n\n"
        f"Tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=admin_broadcast_confirm_kb(),
    )


@router.callback_query(AdminBroadcast.waiting_confirm, F.data == "broadcast_confirm")
async def cb_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if not _check_admin(callback.from_user.id):
        return
    data = await state.get_data()
    await state.clear()

    from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

    user_ids = await db.get_all_user_telegram_ids()
    total_count = len(user_ids)
    await callback.message.answer(f"🚀 Xabar tarqatish boshlandi ({total_count} ta a'zoga)...")
    await callback.answer()

    success = 0
    fail = 0
    blocked = 0

    for idx, tg_id in enumerate(user_ids, start=1):
        try:
            if data.get("photo_id"):
                await bot.send_photo(tg_id, photo=data["photo_id"], caption=data.get("text"), parse_mode="HTML")
            elif data.get("video_id"):
                await bot.send_video(tg_id, video=data["video_id"], caption=data.get("text"), parse_mode="HTML")
            else:
                await bot.send_message(tg_id, data.get("text", ""), parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.04)  # Safe ~25 msgs/sec
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                if data.get("photo_id"):
                    await bot.send_photo(tg_id, photo=data["photo_id"], caption=data.get("text"), parse_mode="HTML")
                else:
                    await bot.send_message(tg_id, data.get("text", ""), parse_mode="HTML")
                success += 1
            except Exception:
                fail += 1
        except TelegramForbiddenError:
            # Botni bloklagan userlarni faolsizlantirish
            blocked += 1
            await db.set_active(tg_id, False)
        except Exception:
            fail += 1

    report = (
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"• Muvaffaqiyatli: <b>{success} ta</b>\n"
        f"• Botni bloklagan (tozalandi): <b>{blocked} ta</b>\n"
        f"• Boshqa xatoliklar: <b>{fail} ta</b>"
    )
    await callback.message.answer(report, parse_mode="HTML", reply_markup=back_to_admin_kb())


@router.callback_query(AdminBroadcast.waiting_confirm, F.data == "broadcast_cancel")
async def cb_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("❌ Xabar tarqatish bekor qilindi.", reply_markup=back_to_admin_kb())
    await callback.answer()


# ---------- 8. To'lov Cheklarini Ko'rish va Tasdiqlash ----------

@router.callback_query(F.data == "admin_receipts")
async def cb_admin_receipts(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    pending = await db.get_pending_receipts()
    if not pending:
        await callback.message.answer(
            "✅ <b>Tasdiqlash kutilayotgan yangi to'lov cheklari yo'q.</b>",
            parse_mode="HTML",
            reply_markup=back_to_admin_kb(),
        )
        await callback.answer()
        return

    await callback.message.answer(f"💳 <b>Kutilayotgan to'lov cheklari ({len(pending)} ta):</b>", parse_mode="HTML")
    from keyboards import payment_receipt_review_kb
    for r in pending[:5]:
        caption = (
            f"👤 <b>Foydalanuvchi:</b> {r['full_name']} (@{r.get('username') or 'yoq'})\n"
            f"🆔 Telegram ID: <code>{r['telegram_id']}</code>\n"
            f"📚 Kurs: <b>{r['course_key']}</b>\n"
            f"💵 Summa: <b>{r.get('amount_uzs', 0):,} so'm</b>\n"
            f"📅 Yuborilgan: {r['created_at'][:16]}"
        )
        kb = payment_receipt_review_kb(r["id"])
        if r.get("receipt_file_id"):
            try:
                await callback.message.answer_photo(photo=r["receipt_file_id"], caption=caption, parse_mode="HTML", reply_markup=kb)
            except Exception:
                await callback.message.answer(caption, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.answer(caption, parse_mode="HTML", reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data.startswith("pay_approve:"))
async def cb_pay_approve(callback: CallbackQuery, bot: Bot) -> None:
    if not _check_admin(callback.from_user.id):
        return
    receipt_id = int(callback.data.split(":")[1])
    receipt = await db.approve_payment_receipt(receipt_id)
    if not receipt:
        await callback.answer("Chek topilmadi yoki allaqachon tasdiqlangan!", show_alert=True)
        return

    await callback.answer("✅ To'lov tasdiqlandi va kurs ochildi!", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xushxabar yuboramiz
    u = await db.get_user_by_id(receipt["user_id"])
    if u:
        try:
            from data.content import COURSES_CATALOG
            c_info = COURSES_CATALOG.get(receipt["course_key"], {})
            c_title = c_info.get("title", receipt["course_key"])
            await bot.send_message(
                u["telegram_id"],
                f"🎉 <b>Tabriklaymiz! Sizning to'lovingiz muvaffaqiyatli tasdiqlandi!</b> 🌿\n\n"
                f"Sizga <b>«{c_title}»</b> kursi to'liq ochildi.\n\n"
                f"Darslarni boshlash uchun quyidagi menyudan foydalaning 👇",
                parse_mode="HTML",
                reply_markup=main_menu_kb(is_admin=is_admin(u["telegram_id"])),
            )
        except Exception:
            logger.exception("Foydalanuvchiga to'lov tasdiqlangani haqida xabar yetib bormadi")


@router.callback_query(F.data.startswith("pay_reject:"))
async def cb_pay_reject(callback: CallbackQuery, bot: Bot) -> None:
    if not _check_admin(callback.from_user.id):
        return
    receipt_id = int(callback.data.split(":")[1])
    receipt = await db.reject_payment_receipt(receipt_id)
    if not receipt:
        await callback.answer("Chek topilmadi!", show_alert=True)
        return

    await callback.answer("❌ Chek bekor qilindi.", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    u = await db.get_user_by_id(receipt["user_id"])
    if u:
        try:
            await bot.send_message(
                u["telegram_id"],
                "⚠️ <b>To'lov chekingiz tasdiqlanmadi.</b>\n\n"
                "Iltimos, haqiqiy to'lov skrinshotini qayta yuboring yoki admin (@sokinqalb_admin) bilan bog'laning.",
                parse_mode="HTML",
            )
        except Exception:
            pass


# ---------- 7. AI Post Generator & Auditoriya Tahlili ----------

@router.callback_query(F.data == "admin_ai_post")
async def cb_admin_ai_post(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.set_state(AdminAIPost.waiting_topic)
    text = (
        "🤖 <b>AI Post Generator</b> ✍️\n\n"
        "Mavzu yoki asosiy g'oyani yozing (masalan: <i>Uyqu gigiyenasi va tungi xavotirlar</i> yoki <i>O'ziga bo'lgan ishonchni tiklash</i>):\n\n"
        "Gemini AI {FOUNDER_NAME} uslubida tayyor Telegram postini generatsiya qilib beradi."
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


@router.message(AdminAIPost.waiting_topic, F.text)
async def handle_ai_post_topic(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    topic = message.text.strip()
    await state.clear()

    await message.answer("✍️ Gemini AI postni tayyorlamoqda, biroz kuting... ⏳")

    try:
        post_text = await ai_service.admin_generate_post(topic)
        await message.answer(
            f"📄 <b>Generatsiya qilingan post:</b>\n\n{post_text}\n\n"
            f"<i>(Ushbu postni nusxalab kanalingizda ulashishingiz yoki Rassilka bo'limi orqali yuborishingiz mumkin)</i>",
            parse_mode="HTML",
            reply_markup=back_to_admin_kb(),
        )
    except Exception as e:
        await message.answer(f"Post yaratishda xatolik yuz berdi: {e}", reply_markup=back_to_admin_kb())


@router.callback_query(F.data == "admin_ai_audience")
async def cb_admin_ai_audience(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await callback.message.answer("🧠 Auditoriya ruhiy tendensiyasi tahlil qilinmoqda... ⏳")
    await callback.answer()

    stats = await db.get_bot_statistics()
    analysis = await ai_service.admin_analyze_audience(stats)

    text = (
        f"🧠 <b>AI Auditoriya Psixologik Tahlili:</b>\n\n{analysis}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())


# =========================================================================
# 11. SOKIN QALB JAMOYASI BOSHQARUVI (ADMIN PANEL)
# =========================================================================

@router.callback_query(F.data == "admin_team")
async def cb_admin_team(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    members = await db.get_all_team_members(active_only=False)
    text = (
        "👥 <b>SOKIN QALB PSIXOTERAPEVTLAR JAMOYASI BOSHQARUVI</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Jami a'zolar: <b>{len(members)} ta</b>\n\n"
        "<i>Mutaxassisni ko'rish, rasmini yuklash, ma'lumotlarini o'zgartirish yoki yangi a'zo qo'shish uchun quyidagilardan birini tanlang:</i> 👇"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_team_list_kb(members))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_team_view:"))
async def cb_adm_team_view(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    member_id = int(callback.data.split(":")[1])
    member = await db.get_team_member_by_id(member_id)
    if not member:
        await callback.answer("Mutaxassis topilmadi!", show_alert=True)
        return

    photo_status = "✅ Yuklangan" if member.get("photo_file_id") else "⚪️ Hali rasm yuklanmagan"
    card_text = (
        f"{member.get('avatar_icon', '👨‍⚕️')} <b>{member['name'].upper()}</b>\n"
        f"<i>{member['title']} ({member['experience']})</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📸 <b>Rasm holati:</b> {photo_status}\n\n"
        f"📌 <b>Faoliyat yo'nalishlari:</b>\n{member.get('directions_text', 'Mavjud emas')}\n\n"
        f"🔬 <b>Metodikasi:</b>\n{member.get('methodology_text', 'Mavjud emas')}\n\n"
        f"🌟 <b>Yutuqlari:</b>\n{member.get('achievements_text', 'Mavjud emas')}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    kb = admin_team_member_manage_kb(member["id"])
    if member.get("photo_file_id"):
        try:
            if len(card_text) <= 1000:
                await callback.message.answer_photo(photo=member["photo_file_id"], caption=card_text, parse_mode="HTML", reply_markup=kb)
            else:
                await callback.message.answer_photo(photo=member["photo_file_id"], caption=f"👨‍⚕️ <b>{member['name']}</b>", parse_mode="HTML")
                await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "adm_add_team_member")
async def cb_adm_add_team_member(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.set_state(AdminTeamManagement.waiting_name)
    await callback.message.answer(
        "➕ <b>YANGI MUTAXASSIS QO'SHISH (1/5)</b>\n\n"
        "Mutaxassisning to'liq <b>Ism-familiyasini</b> kiriting (Masalan: <i>Bag'ibekov Furqat</i>):",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AdminTeamManagement.waiting_name, F.text)
async def handle_adm_team_name(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    name = message.text.strip()
    await state.update_data(new_team_name=name)
    await state.set_state(AdminTeamManagement.waiting_title_exp)
    await message.answer(
        f"👤 <b>Ism:</b> {name}\n\n"
        "Endi uning <b>Lavozimi va Tajribasini</b> kiriting\n"
        "(Masalan: <i>Bosh Psixoterapevt, 12 yillik klinik tajriba</i>):",
        parse_mode="HTML",
    )


@router.message(AdminTeamManagement.waiting_title_exp, F.text)
async def handle_adm_team_title_exp(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    title_exp = message.text.strip()
    await state.update_data(new_team_title=title_exp)
    await state.set_state(AdminTeamManagement.waiting_directions)
    await message.answer(
        "📌 Endi mutaxassisning <b>Asosiy Faoliyat Yo'nalishlarini</b> kiriting\n"
        "(Masalan: <i>• Kognitiv terapiya\n• Surunkali stress va panik ataka\n• Psixosomatika</i>):",
        parse_mode="HTML",
    )


@router.message(AdminTeamManagement.waiting_directions, F.text)
async def handle_adm_team_directions(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    dirs = message.text.strip()
    await state.update_data(new_team_dirs=dirs)
    await state.set_state(AdminTeamManagement.waiting_methodology)
    await message.answer(
        "🔬 Endi mutaxassisning <b>Davolash Metodikasini</b> kiriting\n"
        "(Masalan: <i>• Xitoy Kapsulaterapiyasi\n• Fransiya Neyro-Lampasi\n• Neyro-akustik musiqa</i>):",
        parse_mode="HTML",
    )


@router.message(AdminTeamManagement.waiting_methodology, F.text)
async def handle_adm_team_methodology(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    meth = message.text.strip()
    await state.update_data(new_team_meth=meth)
    await state.set_state(AdminTeamManagement.waiting_achievements)
    await message.answer(
        "🌟 Endi mutaxassisning <b>Erishgan Yutuqlarini</b> kiriting\n"
        "(Masalan: <i>🏆 15,400+ muvaffaqiyatli mijozlar\n🏆 89% panikadan xalos qilish</i>):",
        parse_mode="HTML",
    )


@router.message(AdminTeamManagement.waiting_achievements, F.text)
async def handle_adm_team_achievements(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    achs = message.text.strip()
    data = await state.get_data()
    name = data.get("new_team_name", "Mutaxassis")
    title_exp = data.get("new_team_title", "Psixoterapevt")
    dirs = data.get("new_team_dirs", "")
    meth = data.get("new_team_meth", "")

    # Generatsiya qilingan key
    import time
    m_key = f"doc_{int(time.time())}"

    new_member = await db.save_team_member(
        member_key=m_key,
        name=name,
        title=title_exp,
        experience=title_exp,
        avatar_icon="👨‍⚕️",
        directions_text=dirs,
        methodology_text=meth,
        achievements_text=achs,
        photo_file_id=None,
    )
    await state.clear()
    await message.answer(
        f"🎉 <b>Yangi mutaxassis '{name}' muvaffaqiyatli qo'shildi!</b>\n\n"
        f"<i>Ixtiyoriy ravishda unga profil rasmini yuklashingiz mumkin:</i> 👇",
        parse_mode="HTML",
        reply_markup=admin_team_member_manage_kb(new_member["id"]),
    )


@router.callback_query(F.data.startswith("adm_team_photo:"))
async def cb_adm_team_photo(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    member_id = int(callback.data.split(":")[1])
    await state.set_state(AdminTeamManagement.waiting_photo)
    await state.update_data(target_member_id=member_id)
    await callback.message.answer("📸 <b>Mutaxassis uchun rasm yuboring:</b>", parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


@router.message(AdminTeamManagement.waiting_photo, F.photo)
async def handle_adm_team_photo_upload(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    data = await state.get_data()
    member_id = data.get("target_member_id")
    photo_file_id = message.photo[-1].file_id

    await db.update_team_member_field(member_id, "photo_file_id", photo_file_id)
    await state.clear()

    member = await db.get_team_member_by_id(member_id)
    name = member["name"] if member else "Mutaxassis"
    await message.answer(
        f"✅ <b>'{name}' uchun rasm muvaffaqiyatli saqlandi!</b>\n\n"
        f"Endi foydalanuvchilar ushbu mutaxassis kartochkasini rasm bilan birga ko'radilar.",
        parse_mode="HTML",
        reply_markup=admin_team_member_manage_kb(member_id),
    )


@router.callback_query(F.data.startswith("adm_team_del:"))
async def cb_adm_team_del(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    member_id = int(callback.data.split(":")[1])
    await db.delete_team_member(member_id)
    await callback.answer("🗑 Mutaxassis o'chirildi!", show_alert=True)
    members = await db.get_all_team_members(active_only=False)
    await callback.message.answer(
        "👥 <b>YANGILANGAN JAMOA RO'YXATI:</b>",
        parse_mode="HTML",
        reply_markup=admin_team_list_kb(members),
    )


# =========================================================================
# 12. KURSLAR VA RETREATLAR BOSHQARUVI (ADMIN PANEL)
# =========================================================================

@router.callback_query(F.data == "admin_courses")
async def cb_admin_courses(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    courses = await db.get_all_dynamic_courses(active_only=False)
    text = (
        "📚 <b>KURSLAR, SEANSLAR VA RETREATLAR BOSHQARUVI</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Jami dasturlar: <b>{len(courses)} ta</b>\n\n"
        "<i>Dasturni tahrirlash, darsliklarini boshqarish, yangi kurs qo'shish yoki o'chirish uchun tanlang:</i> 👇"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_courses_list_kb(courses))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_course_view:"))
async def cb_adm_course_view(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    course_id = int(callback.data.split(":")[1])
    course = await db.get_dynamic_course_by_id(course_id)
    if not course:
        await callback.answer("Kurs topilmadi!", show_alert=True)
        return

    mats = await db.get_course_materials(course["course_key"])
    card_text = (
        f"📚 <b>{course['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Narxi:</b> {course.get('price', 'Mavjud emas')}\n"
        f"⏳ <b>Davomiyligi:</b> {course.get('duration', 'Mavjud emas')}\n"
        f"👨‍⚕️ <b>Muallif:</b> {course.get('author', FOUNDER_NAME)}\n"
        f"🎥 <b>Yuklangan darslar:</b> <b>{len(mats)} ta</b>\n\n"
        f"📝 <b>Tavsif:</b>\n{course.get('description', '')}\n\n"
        f"✨ <b>Xususiyatlari:</b>\n{course.get('features_text', '')}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    kb = admin_course_manage_kb(course["id"], course["course_key"])
    if course.get("photo_file_id"):
        try:
            await callback.message.answer_photo(photo=course["photo_file_id"], caption=card_text[:1000], parse_mode="HTML", reply_markup=kb)
        except Exception:
            await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "adm_add_course")
async def cb_adm_add_course(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.set_state(AdminCourseEdit.waiting_title)
    await callback.message.answer(
        "➕ <b>YANGI KURS / SEANS QO'SHISH (1/4)</b>\n\n"
        "Dastur nomini kiriting (Masalan: <i>💎 50$ Yangi Transformatsiya Kursi</i>):",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AdminCourseEdit.waiting_title, F.text)
async def handle_adm_course_title(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    title = message.text.strip()
    await state.update_data(new_course_title=title)
    await state.set_state(AdminCourseEdit.waiting_price)
    await message.answer(
        f"📚 <b>Nomi:</b> {title}\n\n"
        "Endi uning <b>Narxini</b> kiriting (Masalan: <i>50$ (~640 000 so'm)</i>):",
        parse_mode="HTML",
    )


@router.message(AdminCourseEdit.waiting_price, F.text)
async def handle_adm_course_price(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    price = message.text.strip()
    await state.update_data(new_course_price=price)
    await state.set_state(AdminCourseEdit.waiting_description)
    await message.answer(
        "📝 Endi ushbu dastur haqida <b>Tavsif va Ma'lumot</b> matnini kiriting:",
        parse_mode="HTML",
    )


@router.message(AdminCourseEdit.waiting_description, F.text)
async def handle_adm_course_desc(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    desc = message.text.strip()
    data = await state.get_data()
    title = data.get("new_course_title", "Yangi Kurs")
    price = data.get("new_course_price", "10$")

    import time
    c_key = f"c_{int(time.time())}"

    new_c = await db.save_dynamic_course(
        course_key=c_key,
        title=title,
        price=price,
        duration="Amaliy darslar",
        description=desc,
        features_text=desc,
    )
    await state.clear()

    await message.answer(
        f"🎉 <b>'{title}' dasturi muvaffaqiyatli qo'shildi!</b>\n\n"
        f"<i>Endi ushbu kursga darsliklar va videolar biriktirishingiz mumkin:</i> 👇",
        parse_mode="HTML",
        reply_markup=admin_course_manage_kb(new_c["id"], c_key),
    )


@router.callback_query(F.data.startswith("adm_course_photo:"))
async def cb_adm_course_photo(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    c_id = int(callback.data.split(":")[1])
    await state.set_state(AdminCourseEdit.waiting_photo)
    await state.update_data(target_course_id=c_id)
    await callback.message.answer("📸 <b>Kurs uchun rasm yuboring:</b>", parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


@router.message(AdminCourseEdit.waiting_photo, F.photo)
async def handle_adm_course_photo_upload(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    data = await state.get_data()
    c_id = data.get("target_course_id")
    photo_file_id = message.photo[-1].file_id

    await db.update_dynamic_course_field(c_id, "photo_file_id", photo_file_id)
    await state.clear()
    c = await db.get_dynamic_course_by_id(c_id)
    await message.answer(
        f"✅ <b>'{c['title']}' uchun rasm saqlandi!</b>",
        parse_mode="HTML",
        reply_markup=admin_course_manage_kb(c_id, c["course_key"]),
    )


@router.callback_query(F.data.startswith("adm_course_del:"))
async def cb_adm_course_del(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    c_id = int(callback.data.split(":")[1])
    await db.delete_dynamic_course(c_id)
    await callback.answer("🗑 Kurs o'chirildi!", show_alert=True)
    courses = await db.get_all_dynamic_courses(active_only=False)
    await callback.message.answer(
        "📚 <b>YANGILANGAN KURSLAR RO'YXATI:</b>",
        parse_mode="HTML",
        reply_markup=admin_courses_list_kb(courses),
    )


# ---------- Darsliklar & Media Boshqaruvi ----------

@router.callback_query(F.data.startswith("adm_course_lessons:"))
async def cb_admin_course_lessons_hub(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    course_key = callback.data.split(":")[1]
    materials = await db.get_course_materials(course_key)

    text = (
        f"🎬 <b>'{course_key}' Kursi — Darslar va Videolar</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Jami darslar: <b>{len(materials)} ta</b>\n\n"
        f"<i>Dars ustiga bosib video/audio yuklashingiz yoki yangi dars qo'shishingiz mumkin:</i> 👇"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_course_lessons_kb(course_key, materials))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_mat:"))
async def cb_admin_material_detail(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    mat_id = int(callback.data.split(":")[1])
    mat = await db.get_course_material_by_id(mat_id)
    if not mat:
        await callback.answer("Darslik topilmadi!", show_alert=True)
        return

    status = f"✅ Biriktirilgan (File ID: <code>{mat['media_file_id'][:15]}...</code>)" if mat.get("media_file_id") else "⚠️ Fayl biriktirilmagan"
    text = (
        f"🎬 <b>DARSLIK KARTASI:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Nomi:</b> {mat['title']}\n"
        f"📝 <b>Tavsif:</b> {mat.get('description', 'Mavjud emas')}\n"
        f"🎞 <b>Media turi:</b> {mat.get('media_type', 'video').upper()}\n"
        f"📎 <b>Holat:</b> {status}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_material_manage_kb(mat_id, mat['course_key']))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_upload_media:"))
async def cb_admin_upload_media(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    mat_id = int(callback.data.split(":")[1])
    mat = await db.get_course_material_by_id(mat_id)
    if not mat:
        await callback.answer("Darslik topilmadi!", show_alert=True)
        return

    await state.set_state(AdminCourseManagement.waiting_media_upload)
    await state.update_data(current_mat_id=mat_id, course_key=mat["course_key"])

    text = (
        f"📹 <b>'{mat['title']}' uchun video/audio yuboring:</b>\n\n"
        f"<i>(Video, audio, voice yoki hujjat faylini ushbu chatga tashlang)</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


@router.message(AdminCourseManagement.waiting_media_upload)
async def handle_admin_media_upload(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    data = await state.get_data()
    mat_id = data.get("current_mat_id")
    course_key = data.get("course_key", "1usd")

    file_id = None
    media_type = "video"

    if message.video:
        file_id = message.video.file_id
        media_type = "video"
    elif message.audio:
        file_id = message.audio.file_id
        media_type = "audio"
    elif message.voice:
        file_id = message.voice.file_id
        media_type = "audio"
    elif message.video_note:
        file_id = message.video_note.file_id
        media_type = "video"
    elif message.document:
        file_id = message.document.file_id
        media_type = "document"

    if not file_id:
        await message.answer("⚠️ Iltimos, video, audio yoki fayl yuboring!")
        return

    await db.update_course_material_media(mat_id, media_type, file_id)
    await state.clear()
    mat = await db.get_course_material_by_id(mat_id)

    await message.answer(
        f"✅ <b>'{mat['title']}' darsligiga {media_type.upper()} muvaffaqiyatli biriktirildi!</b>",
        parse_mode="HTML",
        reply_markup=admin_material_manage_kb(mat_id, course_key),
    )


@router.callback_query(F.data.startswith("adm_del_mat:"))
async def cb_admin_delete_material(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    mat_id = int(callback.data.split(":")[1])
    mat = await db.get_course_material_by_id(mat_id)
    course_key = mat["course_key"] if mat else "1usd"

    await db.delete_course_material(mat_id)
    materials = await db.get_course_materials(course_key)
    await callback.message.answer(
        "🗑 <b>Darslik o'chirildi!</b>",
        parse_mode="HTML",
        reply_markup=admin_course_lessons_kb(course_key, materials),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_add_mat:"))
async def cb_admin_add_material(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    course_key = callback.data.split(":")[1]
    await state.set_state(AdminCourseManagement.waiting_lesson_title)
    await state.update_data(new_course_key=course_key)

    text = (
        "➕ <b>Yangi Dars Qo'shish:</b>\n\n"
        "Darslik nomini kiriting (Masalan: <i>🎬 4-Dars: Meditatsiya sirlari</i>):"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


@router.message(AdminCourseManagement.waiting_lesson_title, F.text)
async def handle_admin_new_lesson_title(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    title = message.text.strip()
    await state.update_data(new_lesson_title=title)
    await state.set_state(AdminCourseManagement.waiting_lesson_description)
    await message.answer(
        f"📝 <b>Darslik nomi:</b> {title}\n\n"
        "Endi darslik uchun qisqa tavsif yozing (yoki '-' deb yuboring):",
        parse_mode="HTML",
    )


@router.message(AdminCourseManagement.waiting_lesson_description, F.text)
async def handle_admin_new_lesson_desc(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    data = await state.get_data()
    course_key = data.get("new_course_key", "1usd")
    title = data.get("new_lesson_title", "Yangi dars")

    materials = await db.get_course_materials(course_key)
    new_order = len(materials) + 1

    new_id = await db.add_course_material(
        course_key=course_key,
        lesson_order=new_order,
        title=title,
        description=desc,
        media_type="video",
        media_file_id=None,
    )
    await state.clear()

    await message.answer(
        f"🎉 <b>Yangi darslik muvaffaqiyatli yaratildi!</b>\n\n"
        f"📌 <b>Nomi:</b> {title}\n"
        f"<i>Endi ushbu darslikka Video/Audio yuklashingiz mumkin:</i> 👇",
        parse_mode="HTML",
        reply_markup=admin_material_manage_kb(new_id, course_key),
    )


# =========================================================================
# 13. SOKIN SOVG'ALAR (REFERRAL) BOSHQARUVI (ADMIN PANEL)
# =========================================================================

@router.callback_query(F.data == "admin_gifts")
async def cb_admin_gifts(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    gifts = await db.get_all_referral_gifts(active_only=False)
    text = (
        "🎁 <b>SOKIN SOVG'ALAR (REFERRAL REWARDS) BOSHQARUVI</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Jami sovg'alar: <b>{len(gifts)} ta</b>\n\n"
        "<i>Sovg'a shartlarini o'zgartirish, yangi sovg'a qo'shish yoki o'chirish uchun tanlang:</i> 👇"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_gifts_list_kb(gifts))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_gift_view:"))
async def cb_adm_gift_view(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.clear()
    gift_id = int(callback.data.split(":")[1])
    gift = await db.get_referral_gift_by_id(gift_id)
    if not gift:
        await callback.answer("Sovg'a topilmadi!", show_alert=True)
        return

    card_text = (
        f"🎁 <b>{gift['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Talab qilinadigan do'stlar soni:</b> <b>{gift['required_friends']} ta do'st</b>\n"
        f"🏷 <b>Mukofot turi:</b> {gift.get('reward_type', 'course')}\n"
        f"🔑 <b>Ochuvchi kalit:</b> <code>{gift.get('reward_content', '')}</code>\n\n"
        f"📝 <b>Tavsif:</b>\n{gift.get('description', 'Mavjud emas')}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    kb = admin_gift_manage_kb(gift["id"])
    if gift.get("photo_file_id"):
        try:
            await callback.message.answer_photo(photo=gift["photo_file_id"], caption=card_text[:1000], parse_mode="HTML", reply_markup=kb)
        except Exception:
            await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "adm_add_gift")
async def cb_adm_add_gift(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    await state.set_state(AdminGiftManagement.waiting_title)
    await callback.message.answer(
        "➕ <b>YANGI SOVG'A QO'SHISH (1/3)</b>\n\n"
        "Sovg'a nomini kiriting (Masalan: <i>🎁 5 ta do'st: Maxsus Meditatsiya Kursi</i>):",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AdminGiftManagement.waiting_title, F.text)
async def handle_adm_gift_title(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    title = message.text.strip()
    await state.update_data(new_gift_title=title)
    await state.set_state(AdminGiftManagement.waiting_required_friends)
    await message.answer(
        f"🎁 <b>Nomi:</b> {title}\n\n"
        "Ushbu sovg'ani ochish uchun nechta do'st taklif qilinishi kerak? (Raqam kiriting, masalan: <i>5</i>):",
        parse_mode="HTML",
    )


@router.message(AdminGiftManagement.waiting_required_friends, F.text)
async def handle_adm_gift_friends(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat musbat butun son kiriting (masalan: 5)!")
        return
    count = int(text)
    await state.update_data(new_gift_count=count)
    await state.set_state(AdminGiftManagement.waiting_description)
    await message.answer(
        f"👥 <b>Do'stlar soni:</b> {count} ta\n\n"
        "Endi sovg'a haqidagi qisqa tavsifni yuboring:",
        parse_mode="HTML",
    )


@router.message(AdminGiftManagement.waiting_description, F.text)
async def handle_adm_gift_desc(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    desc = message.text.strip()
    data = await state.get_data()
    title = data.get("new_gift_title", "Yangi Sovg'a")
    count = data.get("new_gift_count", 5)

    import time
    g_key = f"gift_{int(time.time())}"

    new_g = await db.save_referral_gift(
        gift_key=g_key,
        title=title,
        required_friends=count,
        description=desc,
        reward_content="custom",
    )
    await state.clear()

    await message.answer(
        f"🎉 <b>'{title}' sovg'asi muvaffaqiyatli saqlandi!</b>\n\n"
        f"Endi foydalanuvchilar {count} ta do'st taklif qilganda ushbu sovg'ani ko'rishadi.",
        parse_mode="HTML",
        reply_markup=admin_gift_manage_kb(new_g["id"]),
    )


@router.callback_query(F.data.startswith("adm_gift_photo:"))
async def cb_adm_gift_photo(callback: CallbackQuery, state: FSMContext) -> None:
    if not _check_admin(callback.from_user.id):
        return
    gift_id = int(callback.data.split(":")[1])
    await state.set_state(AdminGiftManagement.waiting_photo)
    await state.update_data(target_gift_id=gift_id)
    await callback.message.answer("📸 <b>Sovg'a uchun rasm yuboring:</b>", parse_mode="HTML", reply_markup=back_to_admin_kb())
    await callback.answer()


@router.message(AdminGiftManagement.waiting_photo, F.photo)
async def handle_adm_gift_photo_upload(message: Message, state: FSMContext) -> None:
    if not _check_admin(message.from_user.id):
        return
    data = await state.get_data()
    gift_id = data.get("target_gift_id")
    photo_file_id = message.photo[-1].file_id

    await db.update_referral_gift_field(gift_id, "photo_file_id", photo_file_id)
    await state.clear()
    g = await db.get_referral_gift_by_id(gift_id)
    await message.answer(
        f"✅ <b>'{g['title']}' uchun rasm saqlandi!</b>",
        parse_mode="HTML",
        reply_markup=admin_gift_manage_kb(gift_id),
    )


@router.callback_query(F.data.startswith("adm_gift_del:"))
async def cb_adm_gift_del(callback: CallbackQuery) -> None:
    if not _check_admin(callback.from_user.id):
        return
    gift_id = int(callback.data.split(":")[1])
    await db.delete_referral_gift(gift_id)
    await callback.answer("🗑 Sovg'a o'chirildi!", show_alert=True)
    gifts = await db.get_all_referral_gifts(active_only=False)
    await callback.message.answer(
        "🎁 <b>YANGILANGAN SOVG'ALAR RO'YXATI:</b>",
        parse_mode="HTML",
        reply_markup=admin_gifts_list_kb(gifts),
    )
