"""SOKIN QALB — klaviaturalar (inline tugmalar)."""
from typing import Optional, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Asosiy menyu klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🧠 Sokin Diagnostika", callback_data="start_diagnostic")
    kb.button(text="💬 Sokin Suhbat", callback_data="open_ai_chat")
    kb.button(text="🎯 Orzular tomon bir qadam", callback_data="today_task")
    kb.button(text="📝 Sokin Qaydlar", callback_data="sokin_qaydlar")
    kb.button(text="📖 Kurslar & Retreatlar", callback_data="courses_catalog")
    kb.button(text="🎁 Sokin sovg'alar", callback_data="referral_hub")
    kb.button(text="🌟 Bizning yutuqlar", callback_data="our_achievements")
    kb.button(text="👥 Sokin Qalb jamoasi", callback_data="sokinqalb_team")
    if is_admin:
        kb.button(text="👑 Admin Panel", callback_data="open_admin_panel")
        kb.adjust(1, 2, 2, 2, 1, 1)
    else:
        kb.adjust(1, 2, 2, 2, 1)
    return kb.as_markup()


def subscription_required_kb(channel_url: str, instagram_url: str) -> InlineKeyboardMarkup:
    """Majburiy obuna (Telegram kanal va Instagram) klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 1. Telegram kanal", url=channel_url)
    kb.button(text="📸 2. Instagram sahifa", url=instagram_url)
    kb.button(text="✅ Tasdiqlash", callback_data="check_subscription")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Kurslar va Darslar Katalogi Klaviaturasi ----------

def courses_catalog_kb() -> InlineKeyboardMarkup:
    """Mualliflik kurslari, seanslar va retreatlar menyusi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🎁 Bepul Kirish Kursi (0$)", callback_data="course_view:free")
    kb.button(text="💎 1$ Kurs (1 ta darslik)", callback_data="course_view:1usd")
    kb.button(text="🌟 10$ Kurs (3 ta darslik)", callback_data="course_view:10usd")
    kb.button(text="💫 100$ Kurs (5 ta darslik + konsultatsiya)", callback_data="course_view:100usd")
    kb.button(text="🌿 1 Seans: Konsultatsiya + Kapsulaterapiya (150$)", callback_data="course_view:150usd_session")
    kb.button(text="🌿 3 Seans: 3 Konsultatsiya + 3 Kapsulaterapiya (350$)", callback_data="course_view:350usd_session")
    kb.button(text="👑 VIP Seans: VIP Konsultatsiya + Kapsulaterapiya (500$)", callback_data="course_view:500usd_vip_session")
    kb.button(text="🏔 Retreat O'zbekiston", callback_data="course_view:retreat_uzb")
    kb.button(text="🌴 Retreat Tailand", callback_data="course_view:retreat_thailand")
    kb.button(text="🎁 Sokin sovg'alar (Bepul ochish)", callback_data="referral_hub")
    kb.button(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def course_detail_kb(tier_key: str, is_unlocked: bool = False) -> InlineKeyboardMarkup:
    """Bitta kurs yoki xizmat tafsilotlari klaviaturasi."""
    kb = InlineKeyboardBuilder()
    if tier_key == "free":
        kb.button(text="🎧 Bepul darslarni tinglash", callback_data="listen_free_lesson")
    elif is_unlocked:
        kb.button(text="🎉 Kurs darslarini ochish (Sizga Bepul!)", callback_data=f"course_content:{tier_key}")
    else:
        btn_text = "💳 Xizmatga yozilish (Sokin Qalb Adminiga murojaat)" if ("session" in tier_key or "retreat" in tier_key) else "💳 Kursni sotib olish (Sokin Qalb Adminiga murojaat)"
        kb.button(text=btn_text, callback_data=f"course_buy_admin:{tier_key}")
        if tier_key in ("1usd", "10usd", "100usd"):
            kb.button(text="🎁 Sokin sovg'alar (Bepul ochish)", callback_data="referral_hub")
    kb.button(text="📚 Kurslar & Xizmatlar katalogi", callback_data="courses_catalog")
    kb.button(text="🔙 Asosiy menyu", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def course_apply_confirm_kb(tier_key: str) -> InlineKeyboardMarkup:
    """Kursga yozilishni tasdiqlash klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, arizani yuborish", callback_data=f"course_confirm_apply:{tier_key}")
    kb.button(text="❌ Bekor qilish", callback_data=f"course_view:{tier_key}")
    kb.adjust(1)
    return kb.as_markup()


def referral_hub_kb(share_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """Referral markazi klaviaturasi."""
    kb = InlineKeyboardBuilder()
    if share_url:
        kb.button(text="🔗 Do'stlarga ulashish (Share)", url=share_url)
    kb.button(text="🎁 Mening ochilgan kurslarim", callback_data="my_unlocked_courses")
    kb.button(text="📖 Kurslar katalogi", callback_data="courses_catalog")
    kb.button(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def scale_kb(prefix: str, low_label: str, high_label: str) -> InlineKeyboardMarkup:
    """1 dan 10 gacha bo'lgan baholash klaviaturasi (kayfiyat / stress uchun)."""
    kb = InlineKeyboardBuilder()
    for i in range(1, 11):
        kb.button(text=str(i), callback_data=f"{prefix}:{i}")
    kb.adjust(5, 5)
    return kb.as_markup()


def yes_no_kb(prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Ha", callback_data=f"{prefix}:yes")
    kb.button(text="Yo'q", callback_data=f"{prefix}:no")
    kb.adjust(2)
    return kb.as_markup()


def task_done_kb(task_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Bajardim", callback_data=f"task_toggle:{task_id}")
    kb.adjust(1)
    return kb.as_markup()


def daily_tasks_checklist_kb(tasks: list[dict]) -> InlineKeyboardMarkup:
    """Kunlik soatma-soat topshiriqlar interaktiv checklist klaviaturasi."""
    default_hours = ["07:00", "09:30", "13:30", "17:30", "21:30"]
    kb = InlineKeyboardBuilder()
    for i, t in enumerate(tasks):
        icon = "✅" if t.get("is_done") else "⬜️"
        t_time = t.get("scheduled_time") or default_hours[i % len(default_hours)]
        title = t.get("task_title") or t.get("task_text", f"Topshiriq {i+1}")
        short_title = title if len(title) <= 24 else title[:21] + "..."
        kb.button(text=f"[{t_time}] {icon} {short_title}", callback_data=f"task_toggle:{t['id']}")
    
    kb.button(text="✨ Kunlik Shaxsiy Motivatsiya", callback_data="get_dynamic_motivation")
    kb.button(text="🔄 Yangi reja tuzish (AI)", callback_data="refresh_ai_tasks")
    kb.button(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def task_reminder_prompt_kb(task_id: int) -> InlineKeyboardMarkup:
    """Soatlik eslatma bildirishnomasi klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, bajardim! (Tasdiqlash)", callback_data=f"task_confirm:{task_id}")
    kb.button(text="⏳ 15 daqiqadan so'ng eslat", callback_data=f"task_snooze:{task_id}")
    kb.button(text="🎯 Orzular tomon bir qadam", callback_data="today_task")
    kb.adjust(1)
    return kb.as_markup()


def diagnostic_answer_options_kb(prefix: str, options: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        kb.button(text=opt, callback_data=f"{prefix}:{i}")
    kb.adjust(1)
    return kb.as_markup()


def dynamic_diagnostic_options_kb(options: list[str]) -> InlineKeyboardMarkup:
    """AI tomonidan dinamik yaratilgan variantlar klaviaturasi (har bir tugma to'liq o'qiladi)."""
    kb = InlineKeyboardBuilder()
    digits = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
    for i, opt in enumerate(options):
        d = digits[i] if i < len(digits) else f"{i+1}."
        kb.button(text=f"{d} {opt}", callback_data=f"diag_opt:{i}")

    kb.button(text="✍️ O'zim yozib qoldiraman", callback_data="diag_opt:custom")
    kb.button(text="🔙 Bosh menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def diagnostic_result_choice_kb() -> InlineKeyboardMarkup:
    """Diagnostika yakunida yo'nalishlarni tanlash klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🎯 Orzular tomon bir qadam (Kundalik Reja)", callback_data="today_task")
    kb.button(text="💬 Sokin Suhbat (Furqat Bag'ibekov yordamchisi)", callback_data="open_ai_chat")
    kb.button(text="👨‍⚕️ Sokin Qalb Mutaxassisiga murojaat", callback_data="contact_specialist")
    kb.button(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def our_achievements_kb() -> InlineKeyboardMarkup:
    """Bizning yutuqlar va ijtimoiy ishonch markazi klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🏆 Real Mijozlarimiz Natijalari (Keyslar)", callback_data="achievements_cases")
    kb.button(text="🎥 Video va Audio Fikr-mulohazalar", callback_data="achievements_videos")
    kb.button(text="📊 Sokin Qalb Markazi Statistikasi", callback_data="achievements_stats")
    kb.button(text="📈 Mening Shaxsiy Natijalarim (Dinamika)", callback_data="my_personal_progress")
    kb.button(text="🧠 Men ham natijaga erishmoqchiman (Diagnostika)", callback_data="start_diagnostic")
    kb.button(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def cases_list_kb() -> InlineKeyboardMarkup:
    """Mijozlar keyslari ro'yxati."""
    kb = InlineKeyboardBuilder()
    kb.button(text="1️⃣ Dilnoza: 2 yillik Panik atakadan to'liq qutulish", callback_data="case_detail:1")
    kb.button(text="2️⃣ Jamshid: 5 yillik Uyqusizlik va Psixosomatika", callback_data="case_detail:2")
    kb.button(text="3️⃣ Madina: Emotsional kuyish va Depressiyadan chiqish", callback_data="case_detail:3")
    kb.button(text="4️⃣ Farrux & Nigora: Oila va Tog' Retreat mo'jizasi", callback_data="case_detail:4")
    kb.button(text="🌟 Bizning yutuqlar bosh sahifasi", callback_data="our_achievements")
    kb.button(text="🔙 Asosiy menyu", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def sokin_qaydlar_hub_kb() -> InlineKeyboardMarkup:
    """Sokin Qaydlar va Dinamika markazi klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="⚖️ 4 ta Hayotiy Ustunni Baholash (Moliya, Ruhiyat, Tana, Munosabat)", callback_data="start_four_pillars")
    kb.button(text="✍️ Bugungi holatni qayd etish (Check-in)", callback_data="start_checkin")
    kb.button(text="🗓 7 kunlik haftalik tahlil & 10/10 Rejasi", callback_data="progress_weekly")
    kb.button(text="🌕 30 kunlik katta transformatsiya (1 oy oldin vs hozir)", callback_data="progress_monthly")
    kb.button(text="🌟 Bizning yutuqlar", callback_data="our_achievements")
    kb.button(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def progress_hub_kb() -> InlineKeyboardMarkup:
    return sokin_qaydlar_hub_kb()


def four_pillars_scale_kb(pillar_key: str) -> InlineKeyboardMarkup:
    """4 ta ustun uchun 1 dan 10 gacha baholash tugmalari."""
    kb = InlineKeyboardBuilder()
    for i in range(1, 11):
        kb.button(text=str(i), callback_data=f"pillar_{pillar_key}:{i}")
    kb.button(text="🔙 Sokin Qaydlarga qaytish", callback_data="sokin_qaydlar")
    kb.adjust(5, 5, 1)
    return kb.as_markup()


def dynamic_four_pillars_options_kb(options: list[str]) -> InlineKeyboardMarkup:
    """AI tomonidan dinamik yaratilgan 4 ustun bilvosita variantlar klaviaturasi."""
    kb = InlineKeyboardBuilder()
    digits = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
    for i, opt in enumerate(options):
        d = digits[i] if i < len(digits) else f"{i+1}."
        kb.button(text=f"{d} {opt}", callback_data=f"fp_opt:{i}")

    kb.button(text="✍️ O'zim yozib qoldiraman", callback_data="fp_opt:custom")
    kb.button(text="🔙 Sokin Qaydlarga qaytish", callback_data="sokin_qaydlar")
    kb.adjust(1)
    return kb.as_markup()


def dynamic_checkin_options_kb(options: list[str]) -> InlineKeyboardMarkup:
    """AI tomonidan dinamik yaratilgan kunlik checkin variantlar klaviaturasi."""
    kb = InlineKeyboardBuilder()
    digits = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
    for i, opt in enumerate(options):
        d = digits[i] if i < len(digits) else f"{i+1}."
        kb.button(text=f"{d} {opt}", callback_data=f"checkin_opt:{i}")

    kb.button(text="✍️ O'zim yozib qoldiraman", callback_data="checkin_opt:custom")
    kb.button(text="🔙 Sokin Qaydlarga qaytish", callback_data="sokin_qaydlar")
    kb.adjust(1)
    return kb.as_markup()


def review_required_kb() -> InlineKeyboardMarkup:
    """Haftalik yoki oylik majburiy qayd talab qilinganda chiquvchi klaviatura."""
    kb = InlineKeyboardBuilder()
    kb.button(text="⚖️ Haftalik 4 ta Ustun Qaydidan O'tish", callback_data="start_four_pillars")
    kb.adjust(1)
    return kb.as_markup()


def checkin_achievements_kb() -> InlineKeyboardMarkup:
    """Bugungi erishilgan yutuqlar tezkor tugmalari."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🌿 Ichki xotirjamlik his qildim", callback_data="achieve:xotirjamlik")
    kb.button(text="😴 Uyqum yaxshiroq bo'ldi", callback_data="achieve:uyqu")
    kb.button(text="🫁 Nafas/tana mashqi yordam berdi", callback_data="achieve:mashq")
    kb.button(text="🧠 Salbiy fikrlarni to'xtata oldim", callback_data="achieve:fikr")
    kb.button(text="✍️ O'zim yozib qoldiraman", callback_data="achieve:custom")
    kb.button(text="⏭ O'tkazib yuborish", callback_data="achieve:skip")
    kb.adjust(1)
    return kb.as_markup()


def checkin_struggles_kb() -> InlineKeyboardMarkup:
    """Bugungi qiyinchiliklar va kamchiliklar tezkor tugmalari."""
    kb = InlineKeyboardBuilder()
    kb.button(text="⚡️ Ish/o'qishda asabiylashdim", callback_data="struggle:ish")
    kb.button(text="💭 Xavotir va salbiy fikrlar bo'ldi", callback_data="struggle:xavotir")
    kb.button(text="🥱 Charchoq va quvvatsizlik sezdim", callback_data="struggle:charchoq")
    kb.button(text="🤐 Tuyg'ularimni ichga yutdim", callback_data="struggle:ichga_yutish")
    kb.button(text="✍️ O'zim yozib qoldiraman", callback_data="struggle:custom")
    kb.button(text="⏭ O'tkazib yuborish", callback_data="struggle:skip")
    kb.adjust(1)
    return kb.as_markup()


# ---------- AI Chat & SOS Klaviaturasi ----------

def ai_chat_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🧹 Suhbat tarixini tozalash", callback_data="clear_ai_chat")
    kb.button(text="🔙 Bosh menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def sos_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🫁 Vahima / Kuchli xavotir", callback_data="sos:panic")
    kb.button(text="🌙 Uyqusizlik / Xayollar", callback_data="sos:insomnia")
    kb.button(text="⚡️ Asabiylik & G'azab", callback_data="sos:anger")
    kb.button(text="💭 Salbiy fikrlar girdobi", callback_data="sos:overthinking")
    kb.button(text="✍️ O'z holatingizni yozish", callback_data="sos:custom")
    kb.button(text="🔙 Bosh menyu", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def back_to_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Bosh menyuga qaytish", callback_data="back_to_main")
    return kb.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Jonli Dashboard", callback_data="admin_stats")
    kb.button(text="🎁 Sokin Sovg'alar", callback_data="admin_gifts")
    kb.button(text="📚 Kurslar & Retreatlar", callback_data="admin_courses")
    kb.button(text="👥 Sokin Qalb Jamoasi", callback_data="admin_team")
    kb.button(text="💳 To'lov Cheklari", callback_data="admin_receipts")
    kb.button(text="⚠️ Xavfli Holatlar", callback_data="admin_risk_cases")
    kb.button(text="👥 Foydalanuvchilar", callback_data="admin_users:1")
    kb.button(text="🔍 Foydalanuvchi Qidirish", callback_data="admin_search_user")
    kb.button(text="📢 Xabar Tarqatish", callback_data="admin_broadcast")
    kb.button(text="🤖 AI Post Generator", callback_data="admin_ai_post")
    kb.button(text="🧠 Auditoriya Tahlili", callback_data="admin_ai_audience")
    kb.button(text="🔙 Bosh menyuga qaytish", callback_data="back_to_main")
    kb.adjust(2, 2, 2, 2, 2, 1, 1)
    return kb.as_markup()


def admin_team_list_kb(members: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in members:
        photo_mark = "📸" if m.get("photo_file_id") else "⚪️ (Rasmsiz)"
        kb.button(text=f"{m.get('avatar_icon', '👨‍⚕️')} {m['name']} {photo_mark}", callback_data=f"adm_team_view:{m['id']}")
    kb.button(text="➕ Yangi Mutaxassis Qo'shish", callback_data="adm_add_team_member")
    kb.button(text="🔙 Admin menyusi", callback_data="open_admin_panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_team_member_manage_kb(member_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📸 Rasm Yuklash / Yangilash", callback_data=f"adm_team_photo:{member_id}")
    kb.button(text="✏️ Ism va Lavozimni Tahrirlash", callback_data=f"adm_team_edit_name:{member_id}")
    kb.button(text="✏️ Tajriba va Yo'nalishlarni Tahrirlash", callback_data=f"adm_team_edit_exp:{member_id}")
    kb.button(text="✏️ Metodika va Yutuqlarni Tahrirlash", callback_data=f"adm_team_edit_meth:{member_id}")
    kb.button(text="🗑 Mutaxassisni O'chirish", callback_data=f"adm_team_del:{member_id}")
    kb.button(text="🔙 Jamoa Ro'yxatiga Qaytish", callback_data="admin_team")
    kb.adjust(1)
    return kb.as_markup()


def admin_courses_list_kb(courses: list[dict]) -> InlineKeyboardMarkup:
    """Admin uchun kurslarni tanlash klaviaturasi."""
    kb = InlineKeyboardBuilder()
    for c in courses:
        cat_icon = "💎" if c.get("category") == "course" else ("🌿" if c.get("category") == "session" else "🏔")
        price_tag = f"({c.get('price', '')})" if c.get('price') else ""
        short_title = c['title'] if len(c['title']) <= 28 else c['title'][:25] + "..."
        kb.button(text=f"{cat_icon} {short_title} {price_tag}", callback_data=f"adm_course_view:{c['id']}")
    kb.button(text="➕ Yangi Kurs / Seans Qo'shish", callback_data="adm_add_course")
    kb.button(text="🔙 Admin menyusi", callback_data="open_admin_panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_course_manage_kb(course_id: int, course_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📹 Darsliklar / Videolar Boshqaruvi", callback_data=f"adm_course_lessons:{course_key}")
    kb.button(text="📸 Kurs Rasmini Yuklash", callback_data=f"adm_course_photo:{course_id}")
    kb.button(text="✏️ Narx va Muddatni Tahrirlash", callback_data=f"adm_course_edit_price:{course_id}")
    kb.button(text="✏️ Nom va Tavsifni Tahrirlash", callback_data=f"adm_course_edit_desc:{course_id}")
    kb.button(text="🗑 Kursni O'chirish", callback_data=f"adm_course_del:{course_id}")
    kb.button(text="🔙 Kurslar Ro'yxatiga Qaytish", callback_data="admin_courses")
    kb.adjust(1)
    return kb.as_markup()


def admin_gifts_list_kb(gifts: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for g in gifts:
        short_title = g['title'] if len(g['title']) <= 26 else g['title'][:23] + "..."
        kb.button(text=f"🎁 {g['required_friends']} do'st: {short_title}", callback_data=f"adm_gift_view:{g['id']}")
    kb.button(text="➕ Yangi Sovg'a Qo'shish", callback_data="adm_add_gift")
    kb.button(text="🔙 Admin menyusi", callback_data="open_admin_panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_gift_manage_kb(gift_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📸 Sovg'a Rasmini Yuklash", callback_data=f"adm_gift_photo:{gift_id}")
    kb.button(text="✏️ Do'stlar Sonini Tahrirlash", callback_data=f"adm_gift_edit_friends:{gift_id}")
    kb.button(text="✏️ Nomi va Tavsifini Tahrirlash", callback_data=f"adm_gift_edit_desc:{gift_id}")
    kb.button(text="🗑 Sovg'ani O'chirish", callback_data=f"adm_gift_del:{gift_id}")
    kb.button(text="🔙 Sovg'alar Ro'yxatiga Qaytish", callback_data="admin_gifts")
    kb.adjust(1)
    return kb.as_markup()


def admin_course_lessons_kb(course_key: str, materials: list[dict]) -> InlineKeyboardMarkup:
    """Bitta kurs darslari va videolari ro'yxati klaviaturasi."""
    kb = InlineKeyboardBuilder()
    for mat in materials:
        icon = "🎥" if mat.get("media_type") == "video" else ("🎧" if mat.get("media_type") == "audio" else "📄")
        has_file = "✅" if mat.get("media_file_id") else "⚠️ (Faylsiz)"
        title = mat.get("title", f"Dars {mat.get('lesson_order')}")
        short_title = title if len(title) <= 24 else title[:22] + "..."
        kb.button(text=f"{icon} {short_title} {has_file}", callback_data=f"adm_mat:{mat['id']}")

    kb.button(text="➕ Yangi Dars / Video Qo'shish", callback_data=f"adm_add_mat:{course_key}")
    kb.button(text="🔙 Kurslar ro'yxatiga qaytish", callback_data="admin_courses")
    kb.adjust(1)
    return kb.as_markup()


def admin_material_manage_kb(material_id: int, course_key: str) -> InlineKeyboardMarkup:
    """Bitta darslikni boshqarish (video yuklash, o'chirish)."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📹 Video/Audio/Fayl Yuklash", callback_data=f"adm_upload_media:{material_id}")
    kb.button(text="🗑 Darslikni O'chirish", callback_data=f"adm_del_mat:{material_id}")
    kb.button(text="🔙 Darslar ro'yxatiga qaytish", callback_data=f"adm_course:{course_key}")
    kb.adjust(1)
    return kb.as_markup()


def payment_receipt_review_kb(receipt_id: int) -> InlineKeyboardMarkup:
    """Admin uchun to'lov chekini tasdiqlash yoki bekor qilish klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash va Ochish", callback_data=f"pay_approve:{receipt_id}")
    kb.button(text="❌ Bekor Qilish", callback_data=f"pay_reject:{receipt_id}")
    kb.button(text="🔙 To'lovlar ro'yxati", callback_data="admin_receipts")
    kb.adjust(2, 1)
    return kb.as_markup()


def course_checkout_kb(tier_key: str) -> InlineKeyboardMarkup:
    """Kursni sotib olish yoki referral orqali ochish klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Karta orqali to'lov (Chek yuklash)", callback_data=f"course_pay:{tier_key}")
    kb.button(text="👥 Do'stlarni taklif qilib bepul ochish", callback_data="referral_program")
    kb.button(text="🔙 Kurslar katalogiga qaytish", callback_data="courses_catalog")
    kb.adjust(1)
    return kb.as_markup()


def admin_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Xabarni Tarqatish", callback_data="broadcast_confirm")
    kb.button(text="❌ Bekor Qilish", callback_data="broadcast_cancel")
    kb.adjust(1)
    return kb.as_markup()


def admin_users_pagination_kb(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if current_page > 1:
        kb.button(text="⬅️ Oldingi", callback_data=f"admin_users:{current_page - 1}")
    kb.button(text=f"📄 {current_page}/{total_pages}", callback_data="noop")
    if current_page < total_pages:
        kb.button(text="Keyingi ➡️", callback_data=f"admin_users:{current_page + 1}")
    kb.button(text="🔙 Admin menyusi", callback_data="open_admin_panel")
    kb.adjust(3 if (current_page > 1 and current_page < total_pages) else 2, 1)
    return kb.as_markup()


def admin_user_card_kb(user_id: int, is_active: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✉️ Foydalanuvchiga yozish", callback_data=f"admin_dm:{user_id}")
    status_text = "🚫 Bloklash" if is_active else "✅ Faollashtirish"
    kb.button(text=status_text, callback_data=f"admin_toggle_active:{user_id}")
    kb.button(text="🔙 Foydalanuvchilar ro'yxati", callback_data="admin_users:1")
    kb.adjust(2, 1)
    return kb.as_markup()


def back_to_admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Admin Panelga qaytish", callback_data="open_admin_panel")
    return kb.as_markup()


# ---------- Jonli Muloqot (Live Chat) Klaviaturasi ----------

def live_chat_user_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Bosh menyuga qaytish", callback_data="back_to_main")
    return kb.as_markup()


def admin_reply_btn_kb(telegram_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Foydalanuvchiga javob yozish", callback_data=f"admin_reply:{telegram_id}")
    return kb.as_markup()


def user_after_admin_reply_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Yana xabar yozish", callback_data="contact_specialist")
    kb.button(text="🔙 Bosh menyu", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def team_hub_kb(members: Optional[list[dict]] = None) -> InlineKeyboardMarkup:
    """Sokin Qalb jamoasi bosh menyusi klaviaturasi (dinamik)."""
    kb = InlineKeyboardBuilder()
    if members:
        for m in members:
            icon = m.get('avatar_icon') or '👨‍⚕️'
            name = m.get('name', 'Mutaxassis')
            exp = f" ({m.get('experience', '')})" if m.get('experience') else ""
            key = m.get('member_key') or str(m.get('id'))
            kb.button(text=f"{icon} {name}{exp}", callback_data=f"team_member:{key}")
    else:
        kb.button(text="👨‍⚕️ Bag'ibekov Furqat (12 yillik tajriba)", callback_data="team_member:furqat")
        kb.button(text="👩‍⚕️ Muminova Dilfuza (15 yillik tajriba)", callback_data="team_member:dilfuza")
        kb.button(text="👨‍⚕️ Baydjanov Temur (10 yillik tajriba)", callback_data="team_member:temur")

    kb.button(text="📩 Markaz adminiga to'g'ridan-to'g'ri murojaat", callback_data="contact_specialist_direct")
    kb.button(text="🔙 Asosiy menyuga qaytish", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()


def team_member_detail_kb(member_key: str) -> InlineKeyboardMarkup:
    """Alohida mutaxassis kartochkasi klaviaturasi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📩 Konsultatsiyaga yozilish / Murojaat", callback_data=f"consult_with:{member_key}")
    kb.button(text="👥 Jamoaning boshqa mutaxassislari", callback_data="sokinqalb_team")
    kb.button(text="🔙 Asosiy menyu", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()
