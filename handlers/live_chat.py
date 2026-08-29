"""SOKIN QALB — Foydalanuvchi va Admin o'rtasidagi to'g'ridan-to'g'ri Jonli Muloqot (Live Chat).

Ushbu modul foydalanuvchilarning barcha murojaatlari va xabarlarini adminga real vaqt rejimida
yetkazadi va adminning bot orqali qaytargan javoblarini foydalanuvchiga yuboradi.
"""
import os
import re
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile, URLInputFile
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS, FOUNDER_NAME, is_admin
from keyboards import (
    live_chat_user_kb,
    admin_reply_btn_kb,
    user_after_admin_reply_kb,
    main_menu_kb,
    back_to_admin_kb,
    team_hub_kb,
    team_member_detail_kb,
)
from states import LiveChatFlow, AdminReplyToUser

router = Router(name="live_chat")
logger = logging.getLogger(__name__)


# =========================================================================
# SOKIN QALB PSIXOTERAPEVTLAR JAMOASI RASMLARI & MA'LUMOTLARI
# =========================================================================

MEMBER_PHOTOS = {
    "furqat": {
        "local": [
            "images/furqat_bagibekov.png",
            "sokinqalb-uz/public/furqat_bagibekov.png",
            "sokinqalb-uz/dist/furqat_bagibekov.png",
            "images/furqat_hero.png",
        ],
        "url": "https://sokinqalb.uz/furqat_bagibekov.png"
    },
    "dilfuza": {
        "local": [
            "images/dilfuza_muminova.png",
            "sokinqalb-uz/public/dilfuza_muminova.png",
            "sokinqalb-uz/dist/dilfuza_muminova.png"
        ],
        "url": "https://sokinqalb.uz/dilfuza_muminova.png"
    },
    "temur": {
        "local": [
            "images/temur_baydjanov.png",
            "sokinqalb-uz/public/temur_baydjanov.png",
            "sokinqalb-uz/dist/temur_baydjanov.png"
        ],
        "url": "https://sokinqalb.uz/temur_baydjanov.png"
    }
}

def resolve_team_member_photo(member_key: str, photo_file_id: str | None, member_name: str = ""):
    """Mutaxassisning fotosuratini Telegram uchun FSInputFile, URLInputFile yoki file_id ko'rinishida qaytaradi."""
    # 1. Telegram file_id (agar telegram orqali yuborilgan bo'lsa)
    if photo_file_id and not photo_file_id.startswith("http") and not os.path.exists(photo_file_id):
        return photo_file_id

    # 2. Kalit yoki ism bo'yicha standart mutaxassis rasmini aniqlash
    search_str = f"{member_key} {member_name}".lower()
    for key, pinfo in MEMBER_PHOTOS.items():
        if key in search_str:
            for loc in pinfo["local"]:
                if os.path.exists(loc):
                    return FSInputFile(loc)
            if pinfo.get("url"):
                return URLInputFile(pinfo["url"])

    # 3. Agar photo_file_id mahalliy fayl yoki URL bo'lsa
    if photo_file_id:
        if os.path.exists(photo_file_id):
            return FSInputFile(photo_file_id)
        if photo_file_id.startswith("http://") or photo_file_id.startswith("https://"):
            return URLInputFile(photo_file_id)

    # 4. Zaxira rasm (Furqat Bag'ibekov yoki Logo)
    if os.path.exists("images/furqat_bagibekov.png"):
        return FSInputFile("images/furqat_bagibekov.png")
    if os.path.exists("images/logo.jpg"):
        return FSInputFile("images/logo.jpg")

    return None
# =========================================================================

TEAM_DATA = {
    "furqat": {
        "name": "Bag'ibekov Furqat",
        "title": "Bosh Psixoterapevt, Sokin Qalb markazi asoschisi",
        "experience": "12 yillik klinik tajriba",
        "avatar_icon": "👨‍⚕️",
        "directions": [
            "Kognitiv-xulq-atvor psixoterapiyasi va neyropsixologiya",
            "Chuqur somatik tana terapiyasi va psixosomatika",
            "Surunkali stress, vahima (panik ataka) va chuqur psixozlar",
            "Ong osti psixologik travmalari va ildiz bloklarini yechish",
        ],
        "methodology": (
            "• 💊 <b>Xitoy Davolash Kapsulasi (Kapsulaterapiya):</b> Tanani chuqur relaksatsiya qilish, barcha psixosomatik spazm va mushak qisilishlarini yechish.\n"
            "• 💡 <b>Fransiya Neyro-Lampasi (Ko'z uchun stroboskopik yorug'lik):</b> Miya to'lqinlarini alfa/teta darajasiga tushirib, inson ong osti bilan to'g'ridan-to'g'ri muloqot o'rnatish.\n"
            "• 🎶 <b>Maxsus Neyro-Akustik Musiqa:</b> Ong ostidagi stress va psixoz ildizini bir zumda ochish va to'liq davolash (lichina)."
        ),
        "achievements": [
            "15,400+ muvaffaqiyatli sog'lomlashtirilgan mijozlar",
            "89% holatda 14 kunda vahima va xavotirdan to'liq xalos qilish",
            "94% mijozlarda sifatli uyqu va ruhiy immunitetni tiklash",
            "4.95 / 5.0 mijozlar mamnuniyat bahosi",
        ],
    },
    "dilfuza": {
        "name": "Muminova Dilfuza",
        "title": "Yetakchi Psixoterapevt, Ayollar va Oilaviy Psixologiya Eksperti",
        "experience": "15 yillik professional tajriba",
        "avatar_icon": "👩‍⚕️",
        "directions": [
            "Ayollar ruhiy salomatligi va ichki resurslarini qayta tiklash",
            "Oilaviy munosabatlar inqirozi, ajralish va xiyonat og'riqlari",
            "Tug'ruqdan keyingi depressiya va hissiy charchoq (burnout)",
            "Bolalik travmalari, qo'rquvlar va o'ziga ishonchsizlik",
        ],
        "methodology": (
            "• 🌿 <b>Gestalt va Tizimli Oilaviy Terapiya:</b> Oila a'zolari o'rtasidagi sovuqlik va ko'p yillik tushunmovchiliklarni ildizidan bartaraf etish.\n"
            "• 💎 <b>Hissiy Tozalash Texnikalari:</b> Ong ostida to'plangan aybdorlik, xafagarchilik va og'riqlarni xavfsiz bartaraf etish.\n"
            "• 🎨 <b>Integrativ Art-Terapiya:</b> Ayollarning nozik his-tuyg'ularini kashf qilish va yangi hayotiy quvvat bag'ishlash."
        ),
        "achievements": [
            "12,000+ muvaffaqiyatli individual va oilaviy konsultatsiyalar",
            "Minglab oilalarni ajralish yoqasidan saqlab qolish va totuvlikka qaytarish",
            "Ko'plab ayollarga o'z qadrini bilish va baxtli hayot qurishda yo'l ko'rsatish",
        ],
    },
    "temur": {
        "name": "Baydjanov Temur",
        "title": "Yetakchi Psixoterapevt, Neyropsixologik Xulq-atvor Mutaxassisi",
        "experience": "10 yillik klinik tajriba",
        "avatar_icon": "👨‍⚕️",
        "directions": [
            "Erkaklar psixologiyasi va yuqori mas'uliyatdagi hissiy bosim",
            "Biznes, moliya va faoliyatdagi o'tkir stress va inqirozlar",
            "Nevrozlar, fobiya, vahima (panika) va uyqusizlik",
            "Agressiya, asabiylik va ichki zo'riqishni boshqarish",
        ],
        "methodology": (
            "• 🧠 <b>Kognitiv-Xulq-atvor Terapiyasi (KXT / REBT):</b> Salbiy avtomatik fikrlar va ichki qo'rquvlarni mantiqiy qayta dasturlash.\n"
            "• 🫁 <b>Vagus Nervi va Nafas Neyro-Terapiyasi:</b> Tanani zudlik bilan tinchlantiruvchi somatik mashqlar.\n"
            "• 🛡 <b>Psixologik Immunitet:</b> Shaxsiy samaradorlik va bosim ostida xotirjam qaror qabul qilish ko'nikmalari."
        ),
        "achievements": [
            "8,500+ dori-darmonsiz sog'lomlashtirilgan mijozlar",
            "Rahbarlar va tadbirkorlarning hissiy quvvatini tiklash bo'yicha yuqori natijalar",
            "O'tkir nevroz va xavotirlarni qisqa muddatda bartaraf etish",
        ],
    },
}


# =========================================================================
# 1. SOKIN QALB JAMOYASI BOSH SAHIFASI
# =========================================================================

@router.callback_query(F.data.in_(["sokinqalb_team", "contact_specialist"]))
async def show_team_hub(callback: CallbackQuery) -> None:
    """Sokin Qalb jamoasi bosh sahifasi."""
    members = await db.get_all_team_members()
    team_intro = ""
    for i, m in enumerate(members):
        exp = f" ({m.get('experience', '')})" if m.get('experience') else ""
        team_intro += f"{i+1}️⃣ <b>{m['name']}</b> — {m['title']}{exp}\n"

    if not team_intro:
        team_intro = (
            "1️⃣ <b>Bag'ibekov Furqat</b> — Bosh psixoterapevt, markaz asoschisi (12 yillik tajriba)\n"
            "2️⃣ <b>Muminova Dilfuza</b> — Yetakchi psixoterapevt, ayollar va oila eksperti (15 yillik tajriba)\n"
            "3️⃣ <b>Baydjanov Temur</b> — Yetakchi psixoterapevt, neyropsixologiya mutaxassisi (10 yillik tajriba)\n"
        )

    text = (
        "👥 <b>SOKIN QALB PSIXOTERAPEVTLAR JAMOASI</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Markazimizda ko'p yillik klinik tajribaga ega, xalqaro ilg'or metodikalar va zamonaviy uskunalar bilan faoliyat olib boruvchi yetakchi psixoterapevtlar xizmatingizda:\n\n"
        f"{team_intro}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Mutaxassisning faoliyati, metodikasi va yutuqlari bilan tanishish hamda konsultatsiyaga yozilish uchun quyidagilardan birini tanlang 👇</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=team_hub_kb(members))
    await callback.answer()


# ---------- Alohida Mutaxassis Profili (Rasm + Ma'lumot) ----------

@router.callback_query(F.data.startswith("team_member:"))
async def show_team_member_detail(callback: CallbackQuery) -> None:
    """Mutaxassis haqida batafsil ma'lumot, rasmi, ish faoliyati, yutuqlari va metodikasi."""
    member_key = callback.data.split(":")[1]
    member = await db.get_team_member(member_key)
    if not member and member_key.isdigit():
        member = await db.get_team_member_by_id(int(member_key))
    if not member:
        member = TEAM_DATA.get(member_key)

    if not member:
        await callback.answer("Mutaxassis topilmadi", show_alert=True)
        return

    name = member.get("name", "Mutaxassis")
    title = member.get("title", "Psixoterapevt")
    exp = member.get("experience", "")
    icon = member.get("avatar_icon") or "👨‍⚕️"
    dirs = member.get("directions_text") or "\n".join(f"• {d}" for d in member.get("directions", []))
    meth = member.get("methodology_text") or member.get("methodology", "")
    achs = member.get("achievements_text") or "\n".join(f"🏆 {a}" for a in member.get("achievements", []))
    photo_id = member.get("photo_file_id")
    photo_obj = resolve_team_member_photo(member_key, photo_id, name)

    card_text = (
        f"{icon} <b>{name.upper()}</b>\n"
        f"<i>{title} ({exp})</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>Asosiy Faoliyat Yo'nalishlari:</b>\n{dirs}\n\n"
        f"🔬 <b>Davolash Metodikasi:</b>\n{meth}\n\n"
        f"🌟 <b>Erishgan Asosiy Yutuqlari:</b>\n{achs}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>{name} bilan shaxsiy konsultatsiyaga yozilish uchun quyidagi tugmani bosing 👇</i>"
    )

    kb = team_member_detail_kb(member_key)

    if photo_obj:
        try:
            if len(card_text) <= 1000:
                await callback.message.answer_photo(photo=photo_obj, caption=card_text, parse_mode="HTML", reply_markup=kb)
            else:
                await callback.message.answer_photo(
                    photo=photo_obj,
                    caption=f"{icon} <b>{name.upper()}</b>\n<i>{title} ({exp})</i>",
                    parse_mode="HTML"
                )
                await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            logger.warning("Rasm yuborishda xatolik: %s. Matn yuborilmoqda.", e)
            await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.answer(card_text, parse_mode="HTML", reply_markup=kb)

    await callback.answer()


# ---------- Mutaxassisga To'g'ridan-to'g'ri Konsultatsiya So'rovi ----------

@router.callback_query(F.data.startswith("consult_with:"))
async def start_consult_with_member(callback: CallbackQuery, state: FSMContext) -> None:
    """Aynan tanlangan mutaxassis bilan bog'lanish."""
    member_key = callback.data.split(":")[1]
    member = await db.get_team_member(member_key)
    if not member and member_key.isdigit():
        member = await db.get_team_member_by_id(int(member_key))
    if not member:
        member = TEAM_DATA.get(member_key, {})

    member_name = member.get("name", "Mutaxassis")
    await state.set_state(LiveChatFlow.waiting_user_message)
    await state.update_data(target_doctor=member_name)

    text = (
        f"👨‍⚕️ <b>{member_name.upper()}GA MUROJAAT / KONSULTATSIYA</b> 🌿\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Siz <b>{member_name}</b> bilan to'g'ridan-to'g'ri bog'lanmoqdasiz.\n\n"
        f"O'zingizni qiynayotgan savol, holat yoki konsultatsiyaga yozilish istagingizni yozib qoldiring "
        f"<i>(Matn, ovozli xabar yoki rasm ko'rinishida yuborishingiz mumkin)</i> 👇\n\n"
        f"Xabaringiz zudlik bilan {member_name} va markaz ma'muriyatiga yetkaziladi."
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=live_chat_user_kb())
    await callback.answer()


@router.callback_query(F.data == "contact_specialist_direct")
async def start_live_chat_direct(callback: CallbackQuery, state: FSMContext) -> None:
    """Markaz ma'muriyatiga umumiy xabar yo'llash."""
    await state.set_state(LiveChatFlow.waiting_user_message)
    await state.update_data(target_doctor="Sokin Qalb Ma'muriyati")
    text = (
        "👨‍⚕️ <b>SOKIN QALB MARKAZI BILAN BOG'LANISH</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "O'zingizni qiziqtirgan savol, muammo yoki konsultatsiya bo'yicha murojaatingizni yozing.\n"
        "<i>(Matn, ovozli xabar yoki rasm)</i> 👇\n\n"
        "Xabaringiz zudlik bilan mutaxassislarga yetkaziladi va bot orqali javob qaytariladi."
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=live_chat_user_kb())
    await callback.answer()


# =========================================================================
# 2. FOYDALANUVCHI XABARINI ADMINGA YETKAZISH
# =========================================================================

@router.message(LiveChatFlow.waiting_user_message)
async def handle_user_live_message(message: Message, state: FSMContext, bot: Bot) -> None:
    """Foydalanuvchi yozgan xabarni adminlarga yo'llash."""
    # Agar foydalanuvchi menyu komandasi yuborsa
    if message.text and message.text.startswith("/"):
        if message.text in ("/start", "/menu", "/cancel", "/stop"):
            await state.clear()
            await message.answer(
                "Muloqot yakunlandi. Asosiy menyu:",
                reply_markup=main_menu_kb(is_admin=is_admin(message.from_user.id)),
            )
            return

    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            message.from_user.id, message.from_user.full_name, message.from_user.username
        )

    fsm_data = await state.get_data()
    target_doc = fsm_data.get("target_doctor", "Sokin Qalb Mutaxassislari")

    username_str = f"@{user['username']}" if user.get("username") else "mavjud emas"
    diag_status = "✅ O'tgan" if user.get("diagnostic_done") else "⏳ O'tmagan"

    header_text = (
        "📩 <b>YANGI MUROJAAT (Foydalanuvchidan)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Murojaat qilingan mutaxassis:</b> <b>{target_doc}</b>\n"
        f"👤 <b>Foydalanuvchi:</b> {user['full_name']} ({username_str})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user['telegram_id']}</code> | Baza ID: {user['id']}\n"
        f"📅 <b>Kurs kuni:</b> {user['course_day']}-kun | Diag: {diag_status}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )

    admin_kb = admin_reply_btn_kb(user["telegram_id"])

    # Barcha adminlarga yuborish
    sent_to_admin = False
    for admin_id in ADMIN_IDS:
        try:
            if message.text:
                full_admin_text = f"{header_text}\n💬 <b>Xabar matni:</b>\n{message.text}"
                await bot.send_message(admin_id, full_admin_text, parse_mode="HTML", reply_markup=admin_kb)
            elif message.voice:
                caption = f"{header_text}\n🎤 <i>Ovozli xabar (Voice)</i>"
                await bot.send_voice(admin_id, voice=message.voice.file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)
            elif message.photo:
                caption = f"{header_text}\n🖼 <i>Rasm:</i>\n" + (message.caption or "")
                await bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)
            elif message.video_note:
                await bot.send_message(admin_id, header_text, parse_mode="HTML")
                await bot.send_video_note(admin_id, video_note=message.video_note.file_id, reply_markup=admin_kb)
            elif message.audio:
                caption = f"{header_text}\n🎵 <i>Audio:</i>\n" + (message.caption or "")
                await bot.send_audio(admin_id, audio=message.audio.file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)
            elif message.document:
                caption = f"{header_text}\n📄 <i>Hujjat:</i>\n" + (message.caption or "")
                await bot.send_document(admin_id, document=message.document.file_id, caption=caption, parse_mode="HTML", reply_markup=admin_kb)
            else:
                await bot.send_message(admin_id, header_text + "\n(Foydalanuvchi media yubordi)", parse_mode="HTML", reply_markup=admin_kb)
            sent_to_admin = True
        except Exception:
            logger.exception("Adminga (%s) foydalanuvchi xabarini yetkazishda xatolik", admin_id)

    if sent_to_admin:
        await message.answer(
            "✅ <b>Xabaringiz mutaxassisga muvaffaqiyatli yetkazildi!</b> 🌿\n\n"
            "Tez orada admin sizga bot orqali javob qaytaradi. "
            "Yana qo'shimcha xabar yozishingiz yoki kutishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=live_chat_user_kb(),
        )
    else:
        await message.answer(
            "Xabaringiz qabul qilindi. Tez orada siz bilan bog'lanamiz 🌿",
            reply_markup=live_chat_user_kb(),
        )


# ---------- 3. Admin Tugma Orqali Javob Berishi ----------

@router.callback_query(F.data.startswith("admin_reply:"))
async def cb_admin_reply_click(callback: CallbackQuery, state: FSMContext) -> None:
    """Admin 'Javob yozish' tugmasini bosganda."""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    target_tg_id = int(callback.data.split(":")[1])
    target_user = await db.get_user_by_telegram_id(target_tg_id)
    target_name = target_user["full_name"] if target_user else f"Foydalanuvchi ({target_tg_id})"

    await state.set_state(AdminReplyToUser.waiting_admin_reply)
    await state.update_data(target_telegram_id=target_tg_id, target_name=target_name)

    await callback.message.answer(
        f"✍️ <b>{target_name}</b> (<code>{target_tg_id}</code>) ga javob yozish:\n\n"
        f"Javob matningizni yoki ovozli xabaringizni yuboring 👇",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb(),
    )
    await callback.answer()


@router.message(AdminReplyToUser.waiting_admin_reply)
async def handle_admin_reply_message(message: Message, state: FSMContext, bot: Bot) -> None:
    """Admin yozgan javobni foydalanuvchiga yetkazish."""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    target_tg_id = data.get("target_telegram_id")
    target_name = data.get("target_name", "Foydalanuvchi")
    await state.clear()

    reply_header = f"👨‍⚕️ <b>Mutaxassis ({FOUNDER_NAME} / Sokin Qalb) javobi:</b>\n\n"

    try:
        if message.text:
            await bot.send_message(
                target_tg_id,
                reply_header + message.text,
                parse_mode="HTML",
                reply_markup=user_after_admin_reply_kb(),
            )
        elif message.voice:
            await bot.send_voice(
                target_tg_id,
                voice=message.voice.file_id,
                caption=reply_header + (message.caption or ""),
                parse_mode="HTML",
                reply_markup=user_after_admin_reply_kb(),
            )
        elif message.photo:
            await bot.send_photo(
                target_tg_id,
                photo=message.photo[-1].file_id,
                caption=reply_header + (message.caption or ""),
                parse_mode="HTML",
                reply_markup=user_after_admin_reply_kb(),
            )
        elif message.video_note:
            await bot.send_message(target_tg_id, reply_header, parse_mode="HTML")
            await bot.send_video_note(target_tg_id, video_note=message.video_note.file_id, reply_markup=user_after_admin_reply_kb())
        elif message.audio:
            await bot.send_audio(
                target_tg_id,
                audio=message.audio.file_id,
                caption=reply_header + (message.caption or ""),
                parse_mode="HTML",
                reply_markup=user_after_admin_reply_kb(),
            )
        else:
            await bot.send_message(target_tg_id, reply_header + (message.caption or ""), parse_mode="HTML", reply_markup=user_after_admin_reply_kb())

        await message.answer(
            f"✅ Javobingiz <b>{target_name}</b> ga muvaffaqiyatli yetkazildi!",
            parse_mode="HTML",
            reply_markup=back_to_admin_kb(),
        )
    except Exception as e:
        logger.exception("Foydalanuvchiga javob yuborishda xatolik")
        await message.answer(
            f"❌ Xabarni yetkazib bo'lmadi (foydalanuvchi botni bloklagan bo'lishi mumkin): {e}",
            reply_markup=back_to_admin_kb(),
        )


# ---------- 4. Admin Telegram Reply (Ответить) Orqali Javob Berishi ----------

@router.message(F.reply_to_message)
async def handle_admin_telegram_reply(message: Message, bot: Bot) -> None:
    """Admin bot yuborgan xabarga to'g'ridan-to'g'ri 'Reply' (Ответить) qilganda."""
    if not is_admin(message.from_user.id):
        return

    replied_msg = message.reply_to_message
    replied_text = replied_msg.text or replied_msg.caption or ""

    # Xabar matnidan 'Telegram ID: 12345678' ni qidirish
    match = re.search(r"Telegram ID:\s*<code>?(\d+)</code>?", replied_text)
    if not match:
        return

    target_tg_id = int(match.group(1))
    target_user = await db.get_user_by_telegram_id(target_tg_id)
    target_name = target_user["full_name"] if target_user else f"Foydalanuvchi ({target_tg_id})"

    reply_header = f"👨‍⚕️ <b>Mutaxassis ({FOUNDER_NAME} / Sokin Qalb) javobi:</b>\n\n"

    try:
        if message.text:
            await bot.send_message(
                target_tg_id,
                reply_header + message.text,
                parse_mode="HTML",
                reply_markup=user_after_admin_reply_kb(),
            )
        elif message.voice:
            await bot.send_voice(
                target_tg_id,
                voice=message.voice.file_id,
                caption=reply_header + (message.caption or ""),
                parse_mode="HTML",
                reply_markup=user_after_admin_reply_kb(),
            )
        elif message.photo:
            await bot.send_photo(
                target_tg_id,
                photo=message.photo[-1].file_id,
                caption=reply_header + (message.caption or ""),
                parse_mode="HTML",
                reply_markup=user_after_admin_reply_kb(),
            )
        else:
            await bot.send_message(target_tg_id, reply_header + (message.caption or ""), parse_mode="HTML", reply_markup=user_after_admin_reply_kb())

        await message.answer(
            f"✅ Javobingiz <b>{target_name}</b> ga to'g'ridan-to'g'ri yetkazildi!",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Telegram Reply orqali yetkazishda xatolik")
        await message.answer(f"❌ Xabarni yetkazishda xatolik yuz berdi: {e}")
