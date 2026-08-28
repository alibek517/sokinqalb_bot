"""SOKIN QALB — Adaptiv Dinamik Kunlik Kuzatuv (Check-in).

Ushbu modul har kuni foydalanuvchiga bir xil quruq savollar bermasdan,
hayotiy vaziyatli nozik savollar beradi va AI orqali:
1. Kayfiyat darajasi (1-10)
2. Stress darajasi (1-10)
3. Erishgan yutuqlari (achievements)
4. Qiyinchiliklari (struggles)
5. AI psixologik xulosasini avtomatik belgilab, bazaga saqlaydi.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import database as db
import ai_service
from keyboards import (
    dynamic_checkin_options_kb,
    sokin_qaydlar_hub_kb,
    main_menu_kb,
)
from states import CheckinFlow
from config import is_admin

router = Router(name="checkin")
logger = logging.getLogger(__name__)


async def start_checkin(message_or_callback, state: FSMContext) -> None:
    """Kunlik kuzatuv jarayonini boshlash."""
    await state.clear()
    await state.set_state(CheckinFlow.in_progress)

    from_user = message_or_callback.from_user
    user = await db.get_user_by_telegram_id(from_user.id)
    if not user:
        user = await db.get_or_create_user(from_user.id, from_user.full_name, from_user.username)

    bot = message_or_callback.bot
    chat_id = message_or_callback.message.chat.id if isinstance(message_or_callback, CallbackQuery) else message_or_callback.chat.id

    await bot.send_chat_action(chat_id=chat_id, action="typing")
    step_data = await ai_service.generate_adaptive_daily_checkin_step([], user, step_count=0)

    q_text = step_data.get("question", "Bugungi kuningiz qanday o'tdi va o'zingizni qanday his qildingiz?")
    options = step_data.get("options", [
        "Xotirjam va yengil",
        "Ish bilan band va charchagan",
        "Asabiylashish va xavotir",
        "Kutilmagan quvonchli lahzalar",
    ])

    await state.update_data(
        history=[],
        current_question=q_text,
        current_options=options,
        step_count=0,
    )

    text = (
        "📝 <b>BUGUNGI HOLATNI QAYD ETISH (KUNLIK CHECK-IN)</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Bugungi holatingizni vaziyatli savollar orqali xolisona tahlil qilib, ruhiy holatingizni baholaymiz.</i>\n\n"
        f"❓ <b>1-savol:</b>\n{q_text}"
    )
    kb = dynamic_checkin_options_kb(options)

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message_or_callback.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "start_checkin")
async def cb_start_checkin(callback: CallbackQuery, state: FSMContext) -> None:
    await start_checkin(callback, state)
    await callback.answer()


@router.callback_query(CheckinFlow.in_progress, F.data.startswith("checkin_opt:"))
async def handle_checkin_option(callback: CallbackQuery, state: FSMContext) -> None:
    """Foydalanuvchi variant tugmasini bosganda."""
    data = callback.data
    state_data = await state.get_data()
    current_options = state_data.get("current_options", [])

    if data == "checkin_opt:custom":
        await state.set_state(CheckinFlow.waiting_custom_text)
        await callback.message.answer(
            "✍️ <b>Bugungi holatingiz haqida qisqacha yozib yuboring:</b>\n\n"
            "<i>(Nimalarni his qildingiz, qanday vaziyatlar bo'ldi?)</i> 👇",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    try:
        opt_idx = int(data.split(":")[1])
        answer_text = current_options[opt_idx]
    except Exception:
        answer_text = "Belgilandi"

    await _process_next_checkin_step(callback.message, state, callback.from_user, answer_text)
    await callback.answer()


@router.message(CheckinFlow.waiting_custom_text)
async def handle_checkin_custom_text(message: Message, state: FSMContext) -> None:
    """Foydalanuvchi o'z matnini yuborganda."""
    raw_text = message.text.strip() if message.text else ""
    answer_text = raw_text[:600] if len(raw_text) > 600 else raw_text
    await state.set_state(CheckinFlow.in_progress)
    await _process_next_checkin_step(message, state, message.from_user, answer_text)


async def _process_next_checkin_step(message: Message, state: FSMContext, from_user, answer_text: str) -> None:
    """Keyingi adaptiv savolni berish yoki yakuniy check-inni bazaga saqlash."""
    state_data = await state.get_data()
    history = state_data.get("history", [])
    current_question = state_data.get("current_question", "")
    step_count = state_data.get("step_count", 0) + 1

    history.append({
        "question": current_question,
        "answer": answer_text,
    })

    user = await db.get_user_by_telegram_id(from_user.id)
    if not user:
        user = await db.get_or_create_user(from_user.id, from_user.full_name, from_user.username)

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    step_res = await ai_service.generate_adaptive_daily_checkin_step(
        history=history,
        user=user,
        step_count=step_count,
    )

    if not step_res.get("is_finished") and step_count < 2:
        next_q = step_res.get("question", "Bugun sizga eng ko'p kuch bergan yoki qiynagan asosiy narsa nima bo'ldi?")
        next_options = step_res.get("options", [
            "Sokinlik his qildim",
            "Ishdagi muvaffaqiyat",
            "Ortiqcha asabiylashish",
            "Vaqt yetishmasligi",
        ])
        await state.update_data(
            history=history,
            current_question=next_q,
            current_options=next_options,
            step_count=step_count,
        )
        text = (
            f"✅ <i>Javobingiz qabul qilindi.</i>\n\n"
            f"❓ <b>{step_count + 1}-savol:</b>\n{next_q}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=dynamic_checkin_options_kb(next_options))
    else:
        # Yakuniy hisob-kitob (AI o'zi aniqlagan ballar va xulosalar)
        mood = max(1, min(10, step_res.get("mood_score", 7)))
        stress = max(1, min(10, step_res.get("stress_score", 4)))
        achievements = step_res.get("achievements") or "Ichki xotirjamlikka intilish"
        struggles = step_res.get("struggles") or "Yengil kundalik charchoq"
        feedback = step_res.get("ai_feedback") or "Bugungi kuningiz barqaror o'tdi. Kechqurun o'zingizga vaqt ajrating 🌿"

        # Bazaga saqlaymiz
        await db.save_checkin(
            user_id=user["id"],
            mood=mood,
            stress=stress,
            achievements=achievements,
            struggles=struggles,
            note=answer_text,
        )
        await state.clear()

        text = (
            "📅 <b>BUGUNGI KUNLIK KUZATUVINGIZ QAYD ETILDI</b> 🌿\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>Kayfiyat darajasi:</b> {mood}/10\n"
            f"⚡️ <b>Stress darajasi:</b> {stress}/10\n"
            f"🏆 <b>Erishilgan yutuq:</b> {achievements}\n"
            f"⚠️ <b>Duch kelingan qiyinchilik:</b> {struggles}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🧑‍⚕️ <b>Furqat Bag'ibekov Yordamchisi Xulosasi:</b>\n{feedback}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Har kuni o'z holatingizni qayd etib boring — bu barqaror ichki sokinlik kafolatidir 🌿</i>"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=sokin_qaydlar_hub_kb())
