"""SOKIN QALB — Mualliflik Kurslari, Retreatlar, Darslar va Mukammal Referral Tizimi.

Referral qoidalari:
- 1 ta do'st taklif qilsa -> 1$ lik kurs (Mini-intensiv) bepul ochiladi!
- 10 ta do'st taklif qilsa -> 10$ lik kurs (14 kunlik Sokinlik San'ati) bepul ochiladi!
- 200 ta do'st taklif qilsa -> 100$ lik VIP Kurs (Hissiy Erkinlik & Mentorlik) bepul ochiladi!
"""
import logging
from urllib.parse import quote_plus
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from data.content import COURSES_CATALOG, get_lesson_for_day
from config import ADMIN_IDS, FOUNDER_NAME, is_admin
from keyboards import (
    courses_catalog_kb,
    course_detail_kb,
    course_apply_confirm_kb,
    referral_hub_kb,
    admin_reply_btn_kb,
    main_menu_kb,
)

router = Router(name="content")
logger = logging.getLogger(__name__)


# ---------- 1. Kunlik Darslik Yuborish (Scheduler uchun) ----------

async def send_daily_lesson(bot: Bot, telegram_id: int, user_id: int, course_day: int) -> None:
    lesson = get_lesson_for_day(course_day)
    text = (
        f"📖 <b>{lesson['title']}</b>\n\n"
        f"{lesson['text']}\n\n"
        f"🧘 Bugungi meditatsiya: <i>{lesson['meditation']}</i>\n\n"
        f"— {FOUNDER_NAME}"
    )
    try:
        await bot.send_message(telegram_id, text, parse_mode="HTML")
        await db.log_content_sent(
            user_id=user_id, lesson_title=lesson["title"], meditation_title=lesson["meditation"]
        )
    except Exception:
        logger.exception("Foydalanuvchi %s ga darslik yuborishda xatolik", telegram_id)


# ---------- 2. Kurslar & Retreatlar Bosh Katalogi ----------

@router.callback_query(F.data.in_(["courses_catalog", "today_lesson"]))
async def show_courses_catalog(callback: CallbackQuery) -> None:
    """Kurslar va retreatlar katalogi menyusi."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    ref_stats = await db.get_referral_stats(user["id"])
    c = ref_stats["count"]

    tier_1_status = "[🔓 BEPUL OCHILGAN]" if ref_stats["unlocked_1usd"] else "(1 ta do'st = Bepul)"
    tier_10_status = "[🔓 BEPUL OCHILGAN]" if ref_stats["unlocked_10usd"] else "(3 ta do'st = Bepul)"
    tier_100_status = "[🔓 BEPUL OCHILGAN]" if ref_stats["unlocked_100usd"] else "(10 ta do'st = Bepul)"

    courses = await db.get_all_dynamic_courses()
    course_list_text = ""
    for i, cr in enumerate(courses):
        tag = ""
        if cr["course_key"] == "1usd":
            tag = f" {tier_1_status}"
        elif cr["course_key"] == "10usd":
            tag = f" {tier_10_status}"
        elif cr["course_key"] == "100usd":
            tag = f" {tier_100_status}"
        course_list_text += f"{i+1}️⃣ <b>{cr['title']}</b> ({cr.get('price', '')}){tag}\n"

    if not course_list_text:
        course_list_text = (
            "🎁 <b>1. Bepul Kirish Kursi (0$)</b> — 5 kunlik audio-darslar va meditatsiyalar\n"
            f"💎 <b>2. 1$ Kurs (1 ta darslik)</b> {tier_1_status}\n"
            f"🌟 <b>3. 10$ Kurs (3 ta darslik)</b> {tier_100_status}\n"
            f"💫 <b>4. 100$ Kurs (5 ta darslik + konsultatsiya)</b> {tier_100_status}\n"
            "🌿 <b>5. 1 Seans: Konsultatsiya + Kapsulaterapiya (150$)</b>\n"
            "🌿 <b>6. 3 Seans: 3 Konsultatsiya + 3 Kapsulaterapiya (350$)</b>\n"
            "👑 <b>7. VIP Seans: VIP Konsultatsiya + Kapsulaterapiya (500$)</b>\n"
            "🏔 <b>8. Retreat O'zbekiston</b> — Tog' bag'rida 3 kunlik qayta yuklanish\n"
            "🌴 <b>9. Retreat Tailand</b> — 7 kunlik ekzotik sokinlik va qayta tiklanish\n"
        )

    text = (
        "📚 <b>BAGBEKOV FURQATNING MUALLIFLIK KURSLARI VA RETREATLARI</b> 🌿\n\n"
        "12 yillik amaliy psixoterapiya tajribasi asosida yaratilgan dasturlar:\n\n"
        f"{course_list_text}\n"
        f"👥 <i>Siz taklif qilgan do'stlar: <b>{c} ta</b></i>\n\n"
        "<i>Batafsil ma'lumot olish, darslarni ochish yoki yozilish uchun bo'limni tanlang 👇</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=courses_catalog_kb())
    await callback.answer()


# ---------- 3. Muayyan Kurs Tafsilotlarini Ko'rish ----------

@router.callback_query(F.data.startswith("course_view:"))
async def show_course_details(callback: CallbackQuery) -> None:
    """Tanlangan kurs bo'yicha to'liq ma'lumot (imkoniyatlar, narx, yozilish, referral ochilishi)."""
    tier_key = callback.data.split(":")[1]
    course_db = await db.get_dynamic_course(tier_key)
    course = COURSES_CATALOG.get(tier_key, COURSES_CATALOG.get("free", {}))

    title = course_db.get("title") if course_db else course.get("title", "Kurs")
    author = course_db.get("author") if course_db else course.get("author", FOUNDER_NAME)
    price = course_db.get("price") if course_db else course.get("price", "Bepul")
    duration = course_db.get("duration") if course_db else course.get("duration", "")
    target = course_db.get("target") if course_db else course.get("target", "")
    features = course_db.get("features_text") if course_db else "\n".join(f"• {f}" for f in course.get("features", []))
    description = course_db.get("description") if course_db else course.get("description", "")
    photo_id = course_db.get("photo_file_id") if course_db else None

    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    ref_stats = await db.get_referral_stats(user["id"])
    is_unlocked = ref_stats.get(f"unlocked_{tier_key}", False)

    unlock_banner = ""
    if is_unlocked:
        unlock_banner = "🎉 <b>TABRIKLAYMIZ! Ushbu kurs sizga do'stlaringizni taklif qilganingiz uchun BEPUL OCHILGAN!</b> 🔓\n\n"
    elif tier_key == "1usd":
        unlock_banner = f"💡 <i>Yoki <b>1 ta do'stingizni taklif qiling</b> va 1 ta darslikni BEPUL oching! (Hozir: {ref_stats['count']}/1 ta)</i>\n\n"
    elif tier_key == "10usd":
        unlock_banner = f"💡 <i>Yoki <b>3 ta do'stingizni taklif qiling</b> va 3 ta darslikni BEPUL oching! (Hozir: {ref_stats['count']}/3 ta)</i>\n\n"
    elif tier_key == "100usd":
        unlock_banner = f"💡 <i>Yoki <b>10 ta do'stingizni taklif qiling</b> va 5 ta darslik + Konsultatsiyani oching! (Hozir: {ref_stats['count']}/10 ta)</i>\n\n"

    text = (
        f"<b>{title}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{unlock_banner}"
        f"👨‍⚕️ <b>Muallif:</b> {author}\n"
        f"💰 <b>Narxi:</b> <b>{price}</b>\n"
        f"⏳ <b>Davomiyligi:</b> {duration}\n\n"
        f"🎯 <b>Kimlar uchun:</b>\n<i>{target}</i>\n\n"
        f"🌟 <b>Siz nimalarga ega bo'lasiz:</b>\n{features}\n\n"
        f"📝 <b>Batafsil:</b>\n{description}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    kb = course_detail_kb(tier_key, is_unlocked=is_unlocked)
    if photo_id:
        try:
            if len(text) <= 1000:
                await callback.message.answer_photo(photo=photo_id, caption=text, parse_mode="HTML", reply_markup=kb)
            else:
                await callback.message.answer_photo(photo=photo_id, caption=f"<b>{title}</b>\n💰 Narxi: {price}", parse_mode="HTML")
                await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)

    await callback.answer()


# ---------- 4. Referral Markazi (Referral Hub) ----------

@router.callback_query(F.data == "referral_hub")
async def show_referral_hub(callback: CallbackQuery, bot: Bot) -> None:
    """Foydalanuvchining shaxsiy referral markazi, havolasi va sovg'alari."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    bot_info = await bot.get_me()
    bot_username = bot_info.username

    ref_link = f"https://t.me/{bot_username}?start=ref_{user['telegram_id']}"
    ref_stats = await db.get_referral_stats(user["id"])
    count = ref_stats["count"]

    gifts = await db.get_all_referral_gifts()
    gifts_text = ""
    for g in gifts:
        unl = count >= g["required_friends"]
        status = "✅ <b>OCHILGAN!</b>" if unl else f"🔒 <i>(Yana {max(0, g['required_friends'] - count)} ta do'st)</i>"
        gifts_text += f"🎁 <b>{g['required_friends']} ta do'st</b> ➔ <b>{g['title']}</b> {status}\n"

    if not gifts_text:
        status_1 = "✅ <b>OCHILGAN!</b>" if ref_stats["unlocked_1usd"] else f"🔒 <i>(Yana {ref_stats['needed_1usd']} ta)</i>"
        status_10 = "✅ <b>OCHILGAN!</b>" if ref_stats["unlocked_10usd"] else f"🔒 <i>(Yana {ref_stats['needed_10usd']} ta)</i>"
        status_100 = "✅ <b>OCHILGAN!</b>" if ref_stats["unlocked_100usd"] else f"🔒 <i>(Yana {ref_stats['needed_100usd']} ta)</i>"
        gifts_text = (
            f"💎 <b>1 ta do'st</b> ➔ <b>1$ Kurs (1 ta darslik)</b> {status_1}\n"
            f"🌟 <b>3 ta do'st</b> ➔ <b>10$ Kurs (3 ta darslik)</b> {status_10}\n"
            f"💫 <b>10 ta do'st</b> ➔ <b>100$ Kurs (5 ta darslik + konsultatsiya)</b> {status_100}\n"
        )

    share_text = (
        f"🌿 SOKIN QALB — psixoterapevt Bagbekov Furqatning ichki xotirjamlik va "
        f"stressni yengish bo'yicha amaliy boti. Bepul qo'shiling!"
    )
    share_url = f"https://t.me/share/url?url={quote_plus(ref_link)}&text={quote_plus(share_text)}"

    text = (
        "🎁 <b>SOKIN SOVG'ALAR — KURSLARNI BEPUL OCHING!</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Do'stlaringizni taklif qiling va pullik kurslarni bepul oling:\n\n"
        f"{gifts_text}"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Siz taklif qilgan do'stlar soni:</b> <b>{count} ta</b>\n\n"
        f"🔗 <b>Sizning havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        "<i>Havolani ulashish uchun pastdagi tugmani bosing 👇</i>"
    )

    await callback.message.answer(text, parse_mode="HTML", reply_markup=referral_hub_kb(share_url=share_url))
    await callback.answer()


# ---------- 5. Ochilgan Kurslar Kontentini Ko'rish ----------

@router.callback_query(F.data.startswith("course_content:"))
async def view_unlocked_course_content(callback: CallbackQuery) -> None:
    """Ochilgan kurs materiallarini (video, audio va matnlarni) taqdim etish."""
    tier_key = callback.data.split(":")[1]
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)

    is_unlocked = await db.is_course_unlocked(user["id"], tier_key)
    if not is_unlocked:
        await callback.answer("Ushbu kurs hali ochilmagan. Do'stlaringizni taklif qiling yoki to'lov qiling!", show_alert=True)
        return

    materials = await db.get_course_materials(tier_key)

    course_headers = {
        "1usd": "🔓 <b>1$ KURS: 1 TA DARSLIK (SIZGA OCHILGAN!)</b> 💎",
        "10usd": "🔓 <b>10$ KURS: 3 TA DARSLIK (SIZGA OCHILGAN!)</b> 🌟",
        "100usd": "🔓 <b>100$ KURS: 5 TA DARSLIK + KONSULTATSIYA (SIZGA OCHILGAN!)</b> 💫",
    }
    header = course_headers.get(tier_key, "🔓 <b>KURSLAR MATERIALLARI</b> 🌿")

    await callback.message.answer(
        f"{header}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"👨‍⚕️ <b>Muallif:</b> Psixoterapevt Bagbekov Furqat\n\n"
        f"Quyida siz uchun maxsus tayyorlangan darsliklar va amaliyotlar taqdim etiladi 👇",
        parse_mode="HTML",
    )

    # Materiallarni foydalanuvchiga yuborish
    for mat in materials:
        title = mat["title"]
        desc = mat.get("description", "")
        file_id = mat.get("media_file_id")
        media_type = mat.get("media_type", "text")

        caption_text = f"<b>{title}</b>\n\n<i>{desc}</i>" if desc else f"<b>{title}</b>"

        if file_id:
            try:
                if media_type in ("video", "video_note"):
                    await callback.message.answer_video(video=file_id, caption=caption_text, parse_mode="HTML")
                elif media_type == "audio":
                    await callback.message.answer_audio(audio=file_id, caption=caption_text, parse_mode="HTML")
                elif media_type == "voice":
                    await callback.message.answer_voice(voice=file_id, caption=caption_text, parse_mode="HTML")
                elif media_type == "document":
                    await callback.message.answer_document(document=file_id, caption=caption_text, parse_mode="HTML")
                elif media_type == "photo":
                    await callback.message.answer_photo(photo=file_id, caption=caption_text, parse_mode="HTML")
                else:
                    await callback.message.answer(caption_text, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Media yuborishda xatolik: {e}")
                await callback.message.answer(caption_text, parse_mode="HTML")
        else:
            card = (
                f"📌 <b>{title}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{desc}\n\n"
                f"<i>(Darslik materiali yoki qo'llanma) 📚</i>"
            )
            await callback.message.answer(card, parse_mode="HTML")

    # Agar 100$ kurs bo'lsa — Shaxsiy Konsultatsiya tugmasi
    if tier_key == "100usd":
        vip_kb = InlineKeyboardBuilder()
        vip_kb.button(text="👨‍⚕️ Furqat Bag'ibekov bilan Konsultatsiya Vaqtini Belgilash", callback_data="contact_specialist")
        vip_kb.button(text="🔙 Kurslar katalogi", callback_data="courses_catalog")
        vip_kb.adjust(1)
        await callback.message.answer(
            "🎁 <b>SHAXSIY KONSULTATSIYA (1-ON-1)</b> 👨‍⚕️\n\n"
            "Siz 100$ kurs sohibi sifatida psixoterapevt Furqat Bag'ibekov bilan "
            "to'g'ridan-to'g'ri 45 daqiqalik shaxsiy video-konsultatsiyaga ega bo'ldingiz.\n\n"
            "Quyidagi tugma orqali mutaxassis bilan bog'lanib, qulay vaqtni tanlang 👇",
            parse_mode="HTML",
            reply_markup=vip_kb.as_markup(),
        )
    else:
        kb = InlineKeyboardBuilder()
        kb.button(text="📚 Kurslar katalogi", callback_data="courses_catalog")
        kb.button(text="🔙 Asosiy menyu", callback_data="back_to_main")
        kb.adjust(1)
        await callback.message.answer("🌿 <i>Darsliklarni muntazam amalda qo'llang va ichki xotirjamlikni his eting!</i>", reply_markup=kb.as_markup())

    await callback.answer()


# ---------- 6. Mening Ochilgan Kurslarim ----------

@router.callback_query(F.data == "my_unlocked_courses")
async def show_my_unlocked_courses(callback: CallbackQuery) -> None:
    """Foydalanuvchining referral yoki to'lov orqali ochilgan barcha kurslari ro'yxati."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(callback.from_user.id, callback.from_user.full_name, callback.from_user.username)

    ref_stats = await db.get_referral_stats(user["id"])
    unl_1 = await db.is_course_unlocked(user["id"], "1usd")
    unl_10 = await db.is_course_unlocked(user["id"], "10usd")
    unl_100 = await db.is_course_unlocked(user["id"], "100usd")

    kb = InlineKeyboardBuilder()
    unlocked_any = False

    if unl_1:
        kb.button(text="▶️ 1$ Kurs (1 ta darslik)", callback_data="course_content:1usd")
        unlocked_any = True
    if unl_10:
        kb.button(text="▶️ 10$ Kurs (3 ta darslik)", callback_data="course_content:10usd")
        unlocked_any = True
    if unl_100:
        kb.button(text="▶️ 100$ Kurs (5 ta darslik + konsultatsiya)", callback_data="course_content:100usd")
        unlocked_any = True

    kb.button(text="👥 Do'stlarni taklif qilish", callback_data="referral_hub")
    kb.button(text="📚 Kurslar & Xizmatlar katalogi", callback_data="courses_catalog")
    kb.button(text="🔙 Asosiy menyu", callback_data="back_to_main")
    kb.adjust(1)

    if unlocked_any:
        text = (
            "🎁 <b>SIZNING OCHILGAN KURSLARINGIZ RO'YXATI</b> 🌿\n\n"
            f"Siz taklif qilgan do'stlar soni: <b>{ref_stats['count']} ta</b>\n\n"
            "Quyidagi ochilgan kurslardan birini tanlab, darslarni darhol boshlang 👇"
        )
    else:
        text = (
            "🔒 <b>Sizda hali ochilgan pullik kurslar mavjud emas.</b>\n\n"
            f"Hozirgi taklif qilgan do'stlaringiz: <b>{ref_stats['count']} ta</b>\n\n"
            "• <b>1 ta do'st taklif qiling</b> -> 1$ Kurs (1 ta darslik) bepul ochiladi!\n"
            "• <b>3 ta do'st taklif qiling</b> -> 10$ Kurs (3 ta darslik) bepul ochiladi!\n"
            "• <b>10 ta do'st taklif qiling</b> -> 100$ Kurs (5 ta darslik + konsultatsiya) bepul ochiladi!\n\n"
            "Do'stlaringizga o'z havolangizni ulashing 👇"
        )

    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


# ---------- 7. Kursni Sotib Olish (Sokin Qalb Adminiga Murojaat) ----------

@router.callback_query(F.data.startswith("course_buy_admin:"))
async def cb_course_buy_admin(callback: CallbackQuery, bot: Bot) -> None:
    """Kursni sotib olish uchun Sokin Qalb adminiga murojaat qilish."""
    tier_key = callback.data.split(":")[1]
    course = COURSES_CATALOG.get(tier_key, COURSES_CATALOG["1usd"])

    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    username_str = f"@{user['username']}" if user.get("username") else "mavjud emas"

    # Adminga yangi xarid arizasi va bildirishnoma yuborish
    admin_text = (
        "🎓 <b>YANGI KURS SOTIB OLISH SO'ROVI!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Dastur:</b> {course['title']}\n"
        f"💰 <b>Qiymati:</b> {course['price']}\n"
        f"👤 <b>Mijoz:</b> {user['full_name']} ({username_str})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user['telegram_id']}</code> | Baza ID: {user['id']}\n"
        f"📅 <b>Kursdagi faol kun:</b> {user['course_day']}-kun\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Mijozga to'lov rekvizitlarini yuborish yoki bog'lanish uchun quyidagi tugmani bosing:</i> 👇"
    )

    admin_kb = admin_reply_btn_kb(user["telegram_id"])
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="HTML", reply_markup=admin_kb)
        except Exception:
            logger.exception("Adminga xarid so'rovini yetkazishda xatolik: %s", admin_id)

    # Foydalanuvchiga Sokin Qalb adminiga murojaat qilish oynasi
    buy_kb = InlineKeyboardBuilder()
    buy_kb.button(text="👨‍⚕️ Sokin Qalb Adminiga Yozish (Jonli Chat)", callback_data="contact_specialist")
    buy_kb.button(text="💳 Karta orqali to'lov (Chek yuklash)", callback_data=f"course_pay:{tier_key}")
    buy_kb.button(text="👥 Do'stlarni taklif qilib bepul ochish", callback_data="referral_hub")
    buy_kb.button(text="📚 Kurslar katalogi", callback_data="courses_catalog")
    buy_kb.adjust(1)

    user_text = (
        f"💳 <b>KURSNI SOTIB OLISH — SOKIN QALB ADMINIGA MUROJAAT</b> 🌿\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Tanlangan kurs:</b> {course['title']}\n"
        f"💰 <b>Narxi:</b> {course['price']}\n\n"
        f"Sizning xarid so'rovingiz <b>Sokin Qalb adminiga muvaffaqiyatli yetkazildi!</b> ✅\n\n"
        f"Admin siz bilan to'lov rekvizitlari va kursni ochish bo'yicha tez orada to'g'ridan-to'g'ri bog'lanadi. "
        f"Shuningdek, o'zingiz ham to'g'ridan-to'g'ri adminga savollaringizni yozishingiz mumkin 👇"
    )
    await callback.message.answer(user_text, parse_mode="HTML", reply_markup=buy_kb.as_markup())
    await callback.answer("Adminlarga so'rovingiz yetkazildi!", show_alert=True)


# ---------- 7.2 Pullik Kursga Yozilish (Ariza) ----------

@router.callback_query(F.data.startswith("course_apply:"))
async def confirm_course_apply(callback: CallbackQuery) -> None:
    """Kursga yozilish arizasi tasdiqlash oynasi."""
    tier_key = callback.data.split(":")[1]
    course = COURSES_CATALOG.get(tier_key, COURSES_CATALOG["free"])

    text = (
        f"📝 <b>Arizani tasdiqlash</b>\n\n"
        f"Siz <b>{course['title']}</b> ({course['price']}) dasturiga yozilish uchun ariza qoldirmoqchimisiz?\n\n"
        "Ariza yuborilgach, mutaxassisimiz / admin siz bilan to'lov va kursga qo'shilish bo'yicha bog'lanadi."
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=course_apply_confirm_kb(tier_key))
    await callback.answer()


@router.callback_query(F.data.startswith("course_confirm_apply:"))
async def process_course_application(callback: CallbackQuery, bot: Bot) -> None:
    """Kurs arizasini adminga yuborish va foydalanuvchiga tasdiq berish."""
    tier_key = callback.data.split(":")[1]
    course = COURSES_CATALOG.get(tier_key, COURSES_CATALOG["free"])

    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    username_str = f"@{user['username']}" if user.get("username") else "mavjud emas"

    # Adminga yangi ariza xabarnomasi
    admin_text = (
        "🎓 <b>YANGI KURS BUYURTMASI / ARIZA!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Dastur:</b> {course['title']}\n"
        f"💰 <b>Narxi:</b> {course['price']}\n"
        f"👤 <b>Mijoz:</b> {user['full_name']} ({username_str})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user['telegram_id']}</code> | Baza ID: {user['id']}\n"
        f"📅 <b>Kursdagi faol kun:</b> {user['course_day']}-kun\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Foydalanuvchi bilan bog'lanish uchun pastdagi tugmani bosing 👇"
    )

    admin_kb = admin_reply_btn_kb(user["telegram_id"])
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="HTML", reply_markup=admin_kb)
        except Exception:
            logger.exception("Adminga kurs arizasini yetkazishda xatolik: %s", admin_id)

    # Foydalanuvchiga muvaffaqiyat xabari
    user_success_text = (
        "✅ <b>Arizangiz muvaffaqiyatli qabul qilindi!</b> 🌿\n\n"
        f"Siz tanlagan dastur: <b>{course['title']}</b>\n"
        f"Qiymati: <b>{course['price']}</b>\n\n"
        f"Tez orada {FOUNDER_NAME} yoki markaz ma'muriyati siz bilan to'g'ridan-to'g'ri "
        "bog'lanadi hamda to'lov va guruhga ulanish ma'lumotlarini taqdim etadi 💙\n\n"
        "<i>Bizni tanlaganingiz uchun tashakkur!</i>"
    )
    await callback.message.answer(
        user_success_text,
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin=is_admin(callback.from_user.id)),
    )
    await callback.answer("Arizangiz qabul qilindi!", show_alert=True)


# ---------- 8. Bepul Darslarni Tinglash ----------

@router.callback_query(F.data == "listen_free_lesson")
async def show_free_lesson(callback: CallbackQuery) -> None:
    """Foydalanuvchiga bugungi bepul darslikni chiqarish."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    lesson = get_lesson_for_day(user["course_day"])
    text = (
        f"📖 <b>{lesson['title']}</b>\n\n"
        f"{lesson['text']}\n\n"
        f"🧘 Bugungi meditatsiya: <i>{lesson['meditation']}</i>\n\n"
        f"— {FOUNDER_NAME}"
    )
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=courses_catalog_kb(),
    )
    await callback.answer()


# ---------- 9. Karta orqali to'lov va Chek yuklash (Click / Payme / Karta) ----------

from states import CoursePaymentFlow
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

PRICES_UZS = {
    "1usd": 12000,
    "10usd": 128000,
    "100usd": 1280000,
    "retreat": 3500000,
}

@router.callback_query(F.data.startswith("course_pay:"))
async def start_course_payment(callback: CallbackQuery, state: FSMContext) -> None:
    """Karta ma'lumotlarini ko'rsatish va chek so'rash."""
    tier_key = callback.data.split(":")[1]
    course = COURSES_CATALOG.get(tier_key, COURSES_CATALOG["free"])
    price_uzs = PRICES_UZS.get(tier_key, 12000)

    await state.set_state(CoursePaymentFlow.waiting_receipt)
    await state.update_data(tier_key=tier_key, price_uzs=price_uzs)

    text = (
        f"💳 <b>«{course['title']}» UCHUN TO'LOV MA'LUMOTLARI</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>To'lov summasi:</b> <code>{price_uzs:,} so'm</code> ({course['price']})\n\n"
        "💳 <b>Karta raqami:</b> <code>8600 5304 1234 5678</code>\n"
        f"👤 <b>Qabul qiluvchi:</b> Furqat Bag'ibekov (Sokin Qalb)\n\n"
        "📲 <b>Ilovalar orqali to'lov:</b>\n"
        "• Click yoki Payme orqali yuqoridagi kartaga to'lov qiling.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>To'lovni amalga oshirgach, to'lov CHEKINI (skrinshotini) shu yerga rasm sifatida yuboring:</b> 👇"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Bekor qilish", callback_data="courses_catalog")
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(CoursePaymentFlow.waiting_receipt)
async def handle_payment_receipt(message: Message, state: FSMContext, bot: Bot) -> None:
    """Foydalanuvchi yuborgan to'lov cheki rasmini qabul qilish va adminga uzatish."""
    if not message.photo and not message.document:
        await message.answer("Iltimos, to'lov chekini rasm (skrinshot) yoki fayl ko'rinishida yuboring 👇")
        return

    data = await state.get_data()
    tier_key = data.get("tier_key", "1usd")
    price_uzs = data.get("price_uzs", 12000)
    await state.clear()

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        user = await db.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)

    receipt_id = await db.save_payment_receipt(
        user_id=user["id"],
        course_key=tier_key,
        amount_uzs=price_uzs,
        receipt_file_id=file_id,
    )

    from keyboards import payment_receipt_review_kb
    admin_caption = (
        "💳 <b>YANGI TO'LOV CHEKI KELDI!</b> ⚡️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Mijoz:</b> {user['full_name']} (@{user.get('username') or 'yoq'})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user['telegram_id']}</code> | Chek #{receipt_id}\n"
        f"📚 <b>Kurs:</b> {tier_key}\n"
        f"💵 <b>Summa:</b> {price_uzs:,} so'm\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tasdiqlaysizmi?"
    )

    for admin_id in ADMIN_IDS:
        try:
            if message.photo:
                await bot.send_photo(admin_id, photo=file_id, caption=admin_caption, parse_mode="HTML", reply_markup=payment_receipt_review_kb(receipt_id))
            else:
                await bot.send_document(admin_id, document=file_id, caption=admin_caption, parse_mode="HTML", reply_markup=payment_receipt_review_kb(receipt_id))
        except Exception:
            logger.exception("Adminga to'lov chekini yuborishda xatolik: %s", admin_id)

    success_text = (
        "✅ <b>To'lov chekingiz qabul qilindi!</b> 🌿\n\n"
        "Ma'muriyatimiz chekni 5-15 daqiqa ichida tekshiradi va kursingiz avtomatik tarzda ochiladi.\n"
        "<i>Sabringiz va ishonchingiz uchun tashakkur!</i>"
    )
    await message.answer(success_text, parse_mode="HTML", reply_markup=main_menu_kb(is_admin=is_admin(message.from_user.id)))
