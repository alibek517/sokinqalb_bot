"""SOKIN QALB — Tezkor SOS / Anti-stress va Vahima yordami."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import ai_service
from keyboards import sos_menu_kb, back_to_main_kb
from states import SOSFlow

router = Router(name="sos")
logger = logging.getLogger(__name__)

CATEGORY_NAMES = {
    "panic": "Vahima va Kuchli Xavotir",
    "insomnia": "Uyqusizlik va Xayollar Girdobi",
    "anger": "Asabiylik va G'azab",
    "overthinking": "Salbiy Fikrlar va Tushkunlik",
}


@router.callback_query(F.data == "open_sos")
async def open_sos_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """SOS tezkor yordam menyusi."""
    await state.clear()
    text = (
        "🆘 <b>Tezkor Yengillik (SOS Xonasi)</b> 🌿\n\n"
        "Agar hozir o'zingizda kuchli hayajon, vahima, uyqusizlik yoki asabiylik sezsangiz, "
        "quyidagi toifalardan birini tanlang. Sizga ayni damda yordam beruvchi "
        "1 daqiqalik maxsus tinchlantirish mashqini taqdim etamiz 👇"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=sos_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("sos:"))
async def handle_sos_choice(callback: CallbackQuery, state: FSMContext) -> None:
    category_key = callback.data.split(":")[1]

    if category_key == "custom":
        await state.set_state(SOSFlow.waiting_custom_text)
        await callback.message.answer(
            "✍️ Ayni damda o'zingizda nimalarni his qilyapsiz? Bir necha so'z bilan yozing (masalan: <i>yuragim tez uryapti, qo'rquv kelyapti</i>):",
            parse_mode="HTML",
            reply_markup=back_to_main_kb(),
        )
        await callback.answer()
        return

    category_name = CATEGORY_NAMES.get(category_key, "Stress va Xavotir")
    await callback.message.answer("🌿 Bir zum kuting, siz uchun maxsus mashq tayyorlanmoqda... ⏳")
    await callback.answer()

    relief_text = await ai_service.sos_emergency_relief(category_name)
    await callback.message.answer(
        f"🆘 <b>{category_name} uchun tezkor ko'rsatma:</b>\n\n{relief_text}",
        parse_mode="HTML",
        reply_markup=sos_menu_kb(),
    )


@router.message(SOSFlow.waiting_custom_text, F.text)
async def handle_custom_sos_text(message: Message, state: FSMContext) -> None:
    user_desc = message.text.strip()
    await state.clear()
    await message.answer("🌿 Holatingiz tahlil qilinmoqda, biroz kuting... ⏳")

    relief_text = await ai_service.sos_emergency_relief("Foydalanuvchi aytgan maxsus holat", user_desc)
    await message.answer(
        f"🆘 <b>Siz uchun shaxsiy tezkor ko'rsatma:</b>\n\n{relief_text}",
        parse_mode="HTML",
        reply_markup=sos_menu_kb(),
    )
