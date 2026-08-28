"""SOKIN QALB — Dinamik Adaptiv Shaxsiy AI Diagnostika Oqimi.

Foydalanuvchi har bir savolga bergan javobiga qarab, Gemini AI real vaqtda:
1. Yangi, chuqurlashtiruvchi individual savol va unga mos variantlar yaratadi.
2. Variantlar to'liq o'qilishi uchun xabar matnida to'liq chiqariladi va pastda raqamli tugmalar bo'ladi.
3. Insonni to'liq anglab yetgach, yakuniy psixologik tashxis (diagnoz) qo'yadi va kamchiliklarni bartaraf etishning 2 ta yo'lini beradi.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import database as db
import ai_service
from config import CLINIC_CONTACT, FOUNDER_NAME, is_admin
from keyboards import (
    dynamic_diagnostic_options_kb,
    diagnostic_result_choice_kb,
    main_menu_kb,
)
from states import DiagnosticFlow

router = Router(name="diagnostics")
logger = logging.getLogger(__name__)


def _format_diagnostic_question(step_number: int, question_text: str) -> str:
    """Savol matnini chiroyli qilib formatlaydi."""
    return (
        f"📊 <b>Diagnostika — {step_number}-savol:</b>\n\n"
        f"❓ <b>{question_text}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Quyidagi variantlardan birini tanlang yoki o'zingiz yozib yuboring 👇</i>"
    )


# =========================================================================
# 1. DIAGNOSTIKANI BOSHLASH (1-QADAM)
# =========================================================================

@router.callback_query(F.data == "start_diagnostic")
async def start_diagnostic(callback: CallbackQuery, state: FSMContext) -> None:
    """Dinamik AI diagnostikani boshlash."""
    await state.clear()
    await state.set_state(DiagnosticFlow.in_progress)

    user_name = callback.from_user.full_name or "Foydalanuvchi"

    intro_text = (
        "🧠 <b>KENG QAMROVLI SHAXSIY DIAGNOSTIKA</b> 🌿\n\n"
        "Ushbu diagnostika hayotingizning barcha asosiy sohalarini qamrab oladi:\n"
        "• 💰 <b>Moliyaviy va moddiy xavotirlar</b>\n"
        "• 👥 <b>Munosabatlar va oilaviy ziddiyatlar</b>\n"
        "• 💎 <b>O'ziga ishonchsizlik va qadrsizlik hissi</b>\n"
        "• 🧘 <b>Ichki xavotir, uyqusizlik va tana zo'riqishlari</b>\n"
        "• 🎂 <b>Yoshingiz va xarakteringizning kuchli va kuchsiz taraflari</b>\n\n"
        "<i>Har bir javobingiz orqali sizning ayni damdagi holatingizni to'liq o'rganib chiqamiz.</i>\n\n"
        "⏳ <b>Siz uchun 1-savol tayyorlanmoqda...</b>"
    )
    await callback.message.answer(intro_text, parse_mode="HTML")
    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    # 1-savol generatsiyasi
    step_data = await ai_service.generate_adaptive_diagnostic_step(
        history=[],
        user_name=user_name,
        step_count=0,
    )

    q_text = step_data.get("question", "Assalomu alaykum! Shaxsiy kuchli va kuchsiz taraflaringizni aniqlash uchun ayting-chi, ayni paytda sizni ko'proq qaysi soha qiynamoqda?")
    options = step_data.get("options", [
        "Moliyaviy va moddiy qiyinchilik",
        "Oilaviy munosabatlar va ziddiyat",
        "O'ziga ishonchsizlik va qadrsizlik",
        "Kuchli stress, xavotir va uyqusizlik",
    ])

    await state.update_data(
        history=[],
        step_count=1,
        current_question=q_text,
        current_options=options,
    )

    formatted_msg = _format_diagnostic_question(1, q_text)
    await callback.message.answer(
        formatted_msg,
        parse_mode="HTML",
        reply_markup=dynamic_diagnostic_options_kb(options),
    )
    await callback.answer()


# =========================================================================
# 2. JAVOBNI QAYTA ISHLASH (TUGMA YOKI MATN ORQALI)
# =========================================================================

async def _process_diagnostic_step(
    message_or_callback,
    state: FSMContext,
    answer_text: str,
    user_id_tg: int,
    user_full_name: str,
    user_username: str,
    bot: Bot,
) -> None:
    """Foydalanuvchi javobini qabul qilish va AI orqali keyingi qadamni tashkil qilish."""
    data = await state.get_data()
    history = data.get("history", [])
    step_count = data.get("step_count", 1)
    current_q = data.get("current_question", "Holatingiz")

    # Tarixga qo'shish
    history.append({
        "question": current_q,
        "answer": answer_text,
    })

    chat_id = message_or_callback.message.chat.id if isinstance(message_or_callback, CallbackQuery) else message_or_callback.chat.id
    await bot.send_chat_action(chat_id=chat_id, action="typing")

    # Gemini AI orqali keyingi adaptiv qadam yoki tashxis olish
    step_data = await ai_service.generate_adaptive_diagnostic_step(
        history=history,
        user_name=user_full_name,
        step_count=step_count,
    )

    is_finished = step_data.get("is_finished", False)
    risk_flag = step_data.get("risk_flag", False)

    # 1. Xavfli holat tekshiruvi (Suitsid / o'ziga zarar)
    if risk_flag:
        await state.clear()
        user = await db.get_user_by_telegram_id(user_id_tg)
        if not user:
            user = await db.get_or_create_user(user_id_tg, user_full_name, user_username)

        await db.save_diagnostic(
            user_id=user["id"],
            answers={h["question"]: h["answer"] for h in history},
            ai_summary="Foydalanuvchida o'ta yuqori xavf belgilari aniqlandi. Jonli mutaxassis yordami zarur.",
            focus_areas=["Shoshilinch mutaxassis aralashuvi", "Ruhiy qo'llab-quvvatlash"],
            course_outline=[],
            risk_flag=True,
        )
        await db.mark_diagnostic_done(user["id"])

        urgent_text = (
            "Bu haqda ochiq ayta olganingiz uchun rahmat — bu katta va jasur qadam 💙\n\n"
            "Bunday vaziyatda avtomatlashtirilgan dasturdan ko'ra jonli mutaxassis yordami juda muhim. "
            f"Iltimos, zudlik bilan psixoterapevt {FOUNDER_NAME} yoki ishonchli yaqiningiz bilan bog'laning:\n\n"
            f"📞 <b>Aloqa:</b> {CLINIC_CONTACT}\n\n"
            "Siz yolg'iz emassiz, yordam so'rashdan aslo tortinmang 🌿"
        )
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(urgent_text, parse_mode="HTML", reply_markup=main_menu_kb(is_admin=is_admin(user_id_tg)))
        else:
            await message_or_callback.answer(urgent_text, parse_mode="HTML", reply_markup=main_menu_kb(is_admin=is_admin(user_id_tg)))
        return

    # 2. Diagnostika davom etmoqda (Keyingi adaptiv savol)
    if not is_finished:
        next_q = step_data.get("question", "Ushbu holat sizga qanday ta'sir o'tkazmoqda?")
        next_options = step_data.get("options", [
            "Ish faoliyatim va diqqatimga",
            "Yaqinlarim bilan munosabatga",
            "Salomatligim va uyqumga",
            "O'zimga bo'lgan ishonchimga",
        ])

        new_step_count = step_count + 1
        await state.update_data(
            history=history,
            step_count=new_step_count,
            current_question=next_q,
            current_options=next_options,
        )

        formatted_msg = _format_diagnostic_question(new_step_count, next_q)
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(
                formatted_msg,
                parse_mode="HTML",
                reply_markup=dynamic_diagnostic_options_kb(next_options),
            )
        else:
            await message_or_callback.answer(
                formatted_msg,
                parse_mode="HTML",
                reply_markup=dynamic_diagnostic_options_kb(next_options),
            )
        return

    # 3. Diagnostika yakunlandi — AI Tashxisi va 2 ta yechim yo'li
    await state.clear()
    user = await db.get_user_by_telegram_id(user_id_tg)
    if not user:
        user = await db.get_or_create_user(user_id_tg, user_full_name, user_username)

    summary = step_data.get("summary", "Sizda ichki xavotir va tana tarangligi to'plangan.")
    strengths = step_data.get("strengths", [
        "Yuqori mas'uliyat va o'z ustida ishlash xohishi",
        "Empatiya va insoniy samimiylik",
        "Rivojlanish va o'zgarishga intilish",
    ])
    issues = step_data.get("identified_issues", [
        "Moliyaviy xavotirlar va pulga nisbatan ichki bloklar",
        "O'ziga past baho berish va o'z qadrini sezmaslik",
        "Surunkali ichki xavotir va his-tuyg'ularni ichga yutish",
    ])
    focus = step_data.get("focus_areas", [
        "O'z qadrini tiklash va ichki ishonchni mustahkamlash",
        "Moliyaviy xavotirlarni kamaytirish va kognitiv xotirjamlik",
        "Tana relaksatsiyasi va his-tuyg'ularni erkin ifodalash",
    ])
    course_outline = step_data.get("course_outline", [])

    answers_dict = {h["question"]: h["answer"] for h in history}
    await db.save_diagnostic(
        user_id=user["id"],
        answers=answers_dict,
        ai_summary=summary,
        focus_areas=focus,
        course_outline=course_outline,
        risk_flag=False,
    )
    await db.mark_diagnostic_done(user["id"])

    strengths_text = "\n".join(f"• <b>{s}</b>" for s in strengths)
    issues_text = "\n".join(f"• <b>{issue}</b>" for issue in issues)
    focus_text = "\n".join(f"• {f}" for f in focus)

    response_text = (
        "🧠 <b>SIZNING SHAXSIY PSIXOLOGIK TASHXISINGIZ VA PORTRETINGIZ</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>Umumiy holatingiz va xarakter tahlili:</b>\n"
        f"{summary}\n\n"
        f"🌟 <b>Sizning kuchli taraflaringiz va ichki resurslaringiz:</b>\n"
        f"{strengths_text}\n\n"
        f"⚠️ <b>Aniqlangan zaif nuqtalaringiz va kamchiliklar:</b>\n"
        f"{issues_text}\n\n"
        f"🎯 <b>Birinchi navbatda tiklanishi lozim bo'lgan sohalar:</b>\n"
        f"{focus_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Ushbu holatni bartaraf etish va yangi bosqichga chiqish uchun 2 ta yo'nalish mavjud:</b>\n\n"
        "1️⃣ <b>1-usul: Sokin Suhbat (Furqat Bag'ibekov yordamchisi bilan)</b>\n"
        "Har kuni bot orqali savol-javob, shaxsiy mashqlar va 24/7 doimiy ruhiy ko'mak.\n\n"
        "2️⃣ <b>2-usul: Sokin Qalb Mutaxassisi / Adminiga murojaat qilish</b>\n"
        f"Psixoterapevt {FOUNDER_NAME} va markaz ma'muriyati bilan to'g'ridan-to'g'ri jonli yozishish hamda shaxsiy konsultatsiya olish.\n\n"
        "<i>Quyidagi tugmalardan birini tanlab, davom eting 👇</i>"
    )

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(
            response_text,
            parse_mode="HTML",
            reply_markup=diagnostic_result_choice_kb(),
        )
    else:
        await message_or_callback.answer(
            response_text,
            parse_mode="HTML",
            reply_markup=diagnostic_result_choice_kb(),
        )


# ---------- Variant tugmasi bosilganda ----------
@router.callback_query(DiagnosticFlow.in_progress, F.data.startswith("diag_opt:"))
async def handle_diagnostic_option(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    action = callback.data.split(":")[1]
    if action == "custom":
        await callback.message.answer("O'z holatingiz yoki javobingizni erkin tarzda yozib yuboring 👇")
        await callback.answer()
        return

    data = await state.get_data()
    options = data.get("current_options", [])
    try:
        opt_idx = int(action)
        answer_text = options[opt_idx]
    except Exception:
        answer_text = "Variant tanlandi"

    await callback.answer(f"Tanlandi: {opt_idx+1}-variant")
    await _process_diagnostic_step(
        message_or_callback=callback,
        state=state,
        answer_text=answer_text,
        user_id_tg=callback.from_user.id,
        user_full_name=callback.from_user.full_name or "Foydalanuvchi",
        user_username=callback.from_user.username or "",
        bot=bot,
    )


# ---------- Foydalanuvchi matn yoki ovoz yozib yuborganda ----------
@router.message(DiagnosticFlow.in_progress)
async def handle_diagnostic_custom_text(message: Message, state: FSMContext, bot: Bot) -> None:
    raw_text = message.text.strip() if message.text else "Ovozli xabar yuborildi"
    answer_text = raw_text[:600] if len(raw_text) > 600 else raw_text
    await _process_diagnostic_step(
        message_or_callback=message,
        state=state,
        answer_text=answer_text,
        user_id_tg=message.from_user.id,
        user_full_name=message.from_user.full_name or "Foydalanuvchi",
        user_username=message.from_user.username or "",
        bot=bot,
    )
