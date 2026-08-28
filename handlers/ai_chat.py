"""SOKIN QALB — AI Maslahatchi bilan jonli psixologik suhbat.

Diagnostikadan so'ng:
1. AI Maslahatchi foydalanuvchiga birinchi bo'lib uning diagnostikasi va ismi bilan shaxsiy xat yozadi.
2. Aniqlangan muammolarini tasdiqlashini va his-tuyg'ularini so'raydi.
3. Foydalanuvchi javob berishi bilan uzluksiz, empatik jonli konsultatsiya davom etadi.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import database as db
import ai_service
from keyboards import ai_chat_kb, main_menu_kb
from states import AIChatFlow
from config import is_admin

router = Router(name="ai_chat")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "open_ai_chat")
async def open_ai_chat_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """AI Maslahatchi rejimiga o'tish va diagnostika bo'yicha birinchi AI xabarini yuborish."""
    await state.set_state(AIChatFlow.chatting)
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id,
            callback.from_user.full_name or "Foydalanuvchi",
            callback.from_user.username,
        )

    # Chat typing status
    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    # Foydalanuvchining oxirgi diagnostikasini olish
    diag = await db.get_latest_diagnostic(user["id"])
    user_name = user.get("full_name") or "Qadrdonim"

    if diag:
        # AI birinchi bo'lib diagnostika asosida samimiy murojaat yozadi
        opening_text = await ai_service.generate_diagnostic_opening_message(
            user_name=user_name,
            diagnostic=diag,
        )
        # AI xabarini suhbat tarixiga saqlaymiz
        await db.save_ai_message(user_id=user["id"], role="assistant", content=opening_text)
        await callback.message.answer(opening_text, parse_mode="HTML", reply_markup=ai_chat_kb())
    else:
        # Hali diagnostika qilmagan bo'lsa, umumiy iliq taklif
        from config import FOUNDER_NAME
        intro_text = (
            f"Assalomu alaykum, <b>{user_name}</b>! 🌿\n\n"
            f"Men — <b>{FOUNDER_NAME}ning shaxsiy yordamchisiman</b>. "
            "Sizni tinglashga, ichki kechinmalaringizni tushunishga va ruhiy yengillik topishingizga yordam berish uchun shu yerdaman.\n\n"
            "Sizni ayni paytda nima bezovta qilyapti? O'z his-tuyg'ularingiz yoki savollaringizni bemalol yozing 👇\n\n"
            "<i>(Suhbatdan chiqish yoki tarixni tozalash uchun quyidagi tugmalardan foydalaning)</i>"
        )
        await db.save_ai_message(user_id=user["id"], role="assistant", content=intro_text)
        await callback.message.answer(intro_text, parse_mode="HTML", reply_markup=ai_chat_kb())

    await callback.answer()


@router.message(AIChatFlow.chatting, F.text)
async def handle_ai_chat_message(message: Message, state: FSMContext) -> None:
    """Foydalanuvchining AI ga yozgan xabarlarini qayta ishlash va suhbatni davom ettirish."""
    raw_text = message.text.strip()
    user_text = raw_text[:800] if len(raw_text) > 800 else raw_text
    if user_text.startswith("/"):
        if user_text == "/clear":
            user = await db.get_user_by_telegram_id(message.from_user.id)
            if user:
                await db.clear_ai_history(user["id"])
            await message.answer("🧹 Suhbat tarixi tozalandi. Yangi suhbatni boshlashingiz mumkin.", reply_markup=ai_chat_kb())
            return
        elif user_text in ("/start", "/menu", "/stop", "/exit"):
            await state.clear()
            await message.answer(
                "Suhbat yakunlandi. Asosiy menyu:",
                reply_markup=main_menu_kb(is_admin=is_admin(message.from_user.id)),
            )
            return

    # Foydalanuvchi ma'lumotlarini olish
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        user = await db.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)

    # Chat typing status
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Diagnostika va suhbat tarixini olish
    diag = await db.get_latest_diagnostic(user["id"])
    history = await db.get_ai_history(user["id"], limit=8)

    # Foydalanuvchi xabarini bazaga saqlash
    await db.save_ai_message(user_id=user["id"], role="user", content=user_text)

    # Gemini AI dan diagnostika kontekstida javob olish
    reply_text = await ai_service.ai_consultant_chat(
        user_message=user_text,
        history=history,
        user_info=user,
        diagnostic=diag,
    )

    # AI javobini bazaga saqlash
    await db.save_ai_message(user_id=user["id"], role="assistant", content=reply_text)

    await message.answer(reply_text, parse_mode="HTML", reply_markup=ai_chat_kb())


@router.callback_query(AIChatFlow.chatting, F.data == "clear_ai_chat")
@router.callback_query(F.data == "clear_ai_chat")
async def clear_chat_handler(callback: CallbackQuery) -> None:
    """Suhbat tarixini tozalash."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user:
        await db.clear_ai_history(user["id"])
    await callback.message.answer("🧹 Suhbat xotirasi tozalandi. Endi yangi mavzuda suhbatlashishimiz mumkin 🌿", reply_markup=ai_chat_kb())
    await callback.answer()
