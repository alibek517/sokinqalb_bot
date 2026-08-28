"""SOKIN QALB — Bizning Yutuqlar (Social Proof, Real Keyslar, Video Sharhlar va Statistika).

Ushbu modul markazning 12 yillik muvaffaqiyatli tajribasi, 15,400+ mijozlar natijalari,
jonli keyslar, video-sharhlar va ishonchli statistikani taqdim etadi.
Shuningdek, foydalanuvchining shaxsiy natijalari (Check-in dinamikasi) ham shu yerdan ochiladi.
"""
import logging
from typing import Optional, List, Dict, Any
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
import ai_service
from config import is_admin, FOUNDER_NAME
from keyboards import (
    our_achievements_kb,
    cases_list_kb,
    progress_hub_kb,
    sokin_qaydlar_hub_kb,
    four_pillars_scale_kb,
    dynamic_four_pillars_options_kb,
    main_menu_kb,
)
from states import FourPillarsFlow

router = Router(name="menu")
logger = logging.getLogger(__name__)


# =========================================================================
# 1. BIZNING YUTUQLAR BOSH SAHIFASI
# =========================================================================

@router.callback_query(F.data.in_(["our_achievements", "my_progress"]))
async def show_our_achievements(callback: CallbackQuery) -> None:
    """Bizning yutuqlar va ijtimoiy ishonch markazi bosh sahifasi."""
    text = (
        "🌟 <b>SOKIN QALB — BIZNING YUTUQLAR VA NOYOB METODIKA</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Psixoterapevt {FOUNDER_NAME}</b> rahbarligida 12 yillik klinik psixoterapiya "
        "va dunyoning eng ilg'or uskunalari orqali erishilgan natijalar:\n\n"
        "🔬 <b>Noyob Innovatsion Davolash Metodikasi:</b>\n"
        "• 💊 <b>Xitoy davolash Kapsulasi:</b> Tanadagi barcha psixosomatik bloklar va qisilishlarni chuqur yechish.\n"
        "• 💡 <b>Fransiya Neyro-Lampasi:</b> Ko'zga ritmik ta'sir orqali miyani alfa/teta to'lqiniga tushirib, ong osti bilan to'g'ridan-to'g'ri muloqot o'rnatish.\n"
        "• 🎶 <b>Neyro-Akustik Musiqa:</b> Ong ostidagi surunkali stress, qo'rquv, psixoz va tushkunlik ildizini bir zumda ochib davolash.\n\n"
        "📊 <b>Klinik Natijalarimiz:</b>\n"
        "👥 <b>15,400+</b> muvaffaqiyatli sog'lomlashtirilgan mijozlar\n"
        "📉 <b>89%</b> holatda 14 kunda vahima va xavotir to'liq to'xtatilgan\n"
        "😴 <b>94%</b> mijozlarda chuqur sifatli uyqu va kuch tiklangan\n"
        "⭐ <b>4.95 / 5.0</b> mijozlarimizning o'rtacha mamnuniyat bahosi\n\n"
        "<i>Har bir inson ichida xotirjam va baxtli yashash uchun barcha kuch mavjud — "
        "biz uning ildizini ochib, to'liq shifo beramiz 💙</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Quyidagi bo'limlardan birini tanlab, to'liq ma'lumotlar bilan tanishing 👇"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=our_achievements_kb())
    await callback.answer()


# =========================================================================
# 2. REAL MIJOZLAR KEYSLARI VA NATIJALARI
# =========================================================================

CASES_DATA = {
    "1": {
        "title": "Dilnoza M., 29 yosh — 2 yillik Panik Atakadan to'liq qutulish",
        "problem": "2 yil davomida to'satdan yurak urishi, nafas qisishi va o'lim qo'rquvi. Uydan yolg'iz chiqishga qo'rqardi.",
        "solution": "14 kunlik 'Sokinlik San'ati' kursi + Vagus nervi va diafragmal nafas mashqlari.",
        "result": "2-haftadayoq panik ataka xurujlari butunlay to'xtadi. Hozir erkin sayohat qilmoqda.",
        "metrics": "Stress darajasi: 9/10 dan -> 2/10 ga tushdi. Ichki xotirjamlik: 10/10.",
        "quote": "«Furqat aka menga dori-darmonsiz ham o'z ongimni boshqarish mumkinligini isbotladilar. Men hayotimni qaytarib oldim!»",
    },
    "2": {
        "title": "Jamshid R., 38 yosh (Tadbirkor) — 5 yillik Surunkali Uyqusizlik",
        "problem": "Kechalari uyquga ketolmaslik (kuniga 3-4 soat), doimiy asabiylik, bosh og'rig'i va biznesdagi zo'riqish.",
        "solution": "1 oylik VIP Shaxsiy Mentorlik + Somatik tana relaksatsiyasi va kechki raqamli detoks protokoli.",
        "result": "7-kundanoq 8 soatlik chuqur va tiniq uyqu tiklandi. Bosh og'riqlari yo'qoldi.",
        "metrics": "Uyqu sifati: 100% tiklandi. Kundalik quvvat: 3 barobar oshdi.",
        "quote": "«5 yil davomida uxlatuvchi dorilar ichdim. Faqat Sokin Qalb metodikasi ildizdagi sababni yo'qotdi. Rahmat!»",
    },
    "3": {
        "title": "Madina K., 34 yosh (Shifokor) — Emotsional Kuyish va Depressiya",
        "problem": "Ishdagi ortiqcha bosim, doimiy charchoq, hissizlik va kelajakka umidsizlik (Emotsional burnout).",
        "solution": "Chuqur diagnostika tahlili asosidagi individual psixologik xarita + Hissiy intellekt mashqlari.",
        "result": "Ichki tanqidchi to'xtatildi, o'ziga bo'lgan sevgi va kasbiga bo'lgan ilhom qaytdi.",
        "metrics": "Hayot quvvati: 3/10 dan -> 10/10 ga oshdi. Stress: 8/10 dan -> 1/10 ga tushdi.",
        "quote": "«O'zim shifokor bo'lsam-da, o'z hislarimni tushunmay qolgandim. Bu bot va Furqat akaning darslari menga najot bo'ldi.»",
    },
    "4": {
        "title": "Farrux va Nigora (Oila) — 3 Kunlik Tog' Retreati natijasi",
        "problem": "Ko'p yillik oilaviy tushunmovchiliklar, asabiylik va kundalik shahar shovqinidagi stress.",
        "solution": "Sokin Qalb VIP Oflayn Retreat dasturi (Tog' bag'ridagi jonli tana terapiyasi va raqamli detoks).",
        "result": "O'zaro mehr va ishonch qayta tiklandi, 1 yillik barcha charchoq 3 kunda yo'qoldi.",
        "metrics": "Oilaviy totuvlik va ichki xotirjamlik: 100% tiklandi.",
        "quote": "«Retreatda o'tgan 3 kun biz uchun yangi hayot boshlanishi bo'ldi. Hammaga jonli retreatni tavsiya qilamiz!»",
    },
}


@router.callback_query(F.data == "achievements_cases")
async def show_cases_menu(callback: CallbackQuery) -> None:
    """Mijozlarimiz keyslari katalogi."""
    text = (
        "🏆 <b>REAL MIJOZLARIMIZNING TRANSFORMATSIYA KEYSLARI</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Quyida og'ir ruhiy holatlardan to'liq forig' bo'lib, xotirjam hayotga qaytgan "
        "mijozlarimizning aniq natijalari va raqamlar keltirilgan:\n\n"
        "1️⃣ <b>Dilnoza (29 yosh):</b> 2 yillik Panik atakadan to'liq forig' bo'lish\n"
        "2️⃣ <b>Jamshid (38 yosh):</b> 5 yillik Uyqusizlik va surunkali bosh og'rig'i\n"
        "3️⃣ <b>Madina (34 yosh):</b> Emotsional kuyish va Depressiyadan chiqish\n"
        "4️⃣ <b>Farrux & Nigora:</b> Oila va Tog' Retreat mo'jizasi\n\n"
        "<i>Har bir keys bilan batafsil tanishish uchun quyidagi tugmalarni bosing 👇</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=cases_list_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("case_detail:"))
async def show_case_detail(callback: CallbackQuery) -> None:
    """Alohida bitta keys tafsilotlari."""
    case_id = callback.data.split(":")[1]
    case = CASES_DATA.get(case_id, CASES_DATA["1"])

    kb = InlineKeyboardBuilder()
    kb.button(text="🧠 Men ham tekshiruvdan o'tmoqchiman (Diagnostika)", callback_data="start_diagnostic")
    kb.button(text="📖 Kurslarni ko'rish", callback_data="courses_catalog")
    kb.button(text="🏆 Boshqa keyslarni ko'rish", callback_data="achievements_cases")
    kb.button(text="🔙 Bizning yutuqlar", callback_data="our_achievements")
    kb.adjust(1)

    text = (
        f"🏆 <b>TRANSFORMATSIYA KEYSI:</b>\n"
        f"<b>{case['title']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"❌ <b>Dastlabki muammo:</b>\n<i>{case['problem']}</i>\n\n"
        f"🛠 <b>Qo'llanilgan yechim:</b>\n<i>{case['solution']}</i>\n\n"
        f"✅ <b>Erishilgan natija:</b>\n<b>{case['result']}</b>\n\n"
        f"📊 <b>Ko'rsatkichlar o'zgarishi:</b>\n• {case['metrics']}\n\n"
        f"💬 <b>Mijoz fikri:</b>\n{case['quote']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Siz ham o'z muammoingizdan dori-darmonsiz xalos bo'la olasiz!</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


# =========================================================================
# 3. VIDEO VA AUDIO SHARHLAR
# =========================================================================

@router.callback_query(F.data == "achievements_videos")
async def show_video_reviews(callback: CallbackQuery) -> None:
    """Video va audio fikr-mulohazalar bo'limi."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🧠 Bepul Diagnostikadan o'tish", callback_data="start_diagnostic")
    kb.button(text="☎️ Mutaxassis bilan bog'lanish", callback_data="contact_specialist")
    kb.button(text="🔙 Bizning yutuqlar", callback_data="our_achievements")
    kb.adjust(1)

    text = (
        "🎥 <b>VIDEO VA AUDIO FIKR-MULOHAZALAR</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Mijozlarimizning samimiy audio va video minnatdorchiliklari:\n\n"
        "🎬 <b>1. «Panik ataka va qo'rquvni qanday yengdim?»</b>\n"
        "💬 <i>«Avvallari tez yordam chaqirish odat bo'lib qolgandi. Furqat akaning nafas mashqlarini qo'llaganimdan so'ng 1 yildan beri bitta ham xuruj bo'lmadi...»</i> — Nigora, 31 yosh.\n\n"
        "🎬 <b>2. «Uyqusizlik va doimiy asabiylikdan forig' bo'lish»</b>\n"
        "💬 <i>«Tadbirkorlikdagi stress tufayli oilamda ham janjal ko'paygandi. 14 kunlik darslar mening xarakterimni o'zgartirdi...»</i> — Akmal, 42 yosh.\n\n"
        "🎬 <b>3. «Tog'dagi jonli Retreat taassurotlari»</b>\n"
        "💬 <i>«Telefonlarsiz, tabiat qo'ynida o'tgan 3 kun hayotimdagi eng sokin va unutilmas damlar bo'ldi...»</i> — Umida, 27 yosh.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Barcha video va audio materiallar rasmiy kanalimizda muntazam e'lon qilib boriladi 🌿</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


# =========================================================================
# 4. MARKAZNING RASMIY STATISTIKASI VA METODIKASI
# =========================================================================

@router.callback_query(F.data == "achievements_stats")
async def show_center_stats(callback: CallbackQuery) -> None:
    """Markazning rasmiy statistikasi va ilmiy metodikalari."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🧠 Bepul Diagnostikani boshlash", callback_data="start_diagnostic")
    kb.button(text="📖 Mualliflik kurslari", callback_data="courses_catalog")
    kb.button(text="🔙 Bizning yutuqlar", callback_data="our_achievements")
    kb.adjust(1)

    text = (
        "📊 <b>SOKIN QALB MARKAZI RASMIY STATISTIKASI</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Markazimiz 12 yil davomida dunyoning eng ilg'or psixoterapiya "
        "yo'nalishlarini birlashtirgan holda faoliyat yuritadi:\n\n"
        "📈 <b>Raqamlarda bizning natijalarimiz:</b>\n"
        "• <b>15,400+</b> muvaffaqiyatli sog'lomlashtirilgan insonlar\n"
        "• <b>89%</b> mijozlarda 14 kunda xavotir va tushkunlikning yo'qolishi\n"
        "• <b>94%</b> mijozlarda sifatli uyqu va tetiklikning tiklanishi\n"
        "• <b>98.2%</b> ijobiy fikr va tavsiyalar\n\n"
        "🔬 <b>Biz qo'llaydigan ilmiy metodikalar:</b>\n"
        "1. <b>Kognitiv-xulqiy terapiya (CBT)</b> — salbiy fikr qoliplarini o'zgartirish\n"
        "2. <b>Tana-yo'naltirilgan somatik terapiya</b> — mushak va nerv qisilishlarini yechish\n"
        "3. <b>Mindfulness & Neyro-meditatsiya</b> — miyadagi xavotir markazini tinchlantirish\n"
        "4. <b>Individual Shaxsiy Yondashuv</b> — har bir insonga 24/7 doimiy ko'mak\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Siz ham o'z hayotingizni bugunoq ijobiy tomonga o'zgartiring!</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await callback.answer()


# =========================================================================
# 5. SOKIN QAYDLAR (SHAXSIY REYTING VA O'ZGARISHLAR DINAMIKASI)
# =========================================================================

def _render_pillars_card(current: dict, previous: Optional[dict] = None) -> str:
    fin = current.get("financial_score", 5)
    men = current.get("mental_score", 5)
    phys = current.get("physical_score", 5)
    rel = current.get("relationship_score", 5)

    def bar(val: int) -> str:
        v = max(1, min(10, val))
        return "█" * v + "░" * (10 - v)

    def diff_str(curr_val: int, prev_val: Optional[int]) -> str:
        if prev_val is None:
            return ""
        d = curr_val - prev_val
        if d > 0:
            return f" (↗️ +{d})"
        elif d < 0:
            return f" (↘️ {d})"
        return " (➡️ 0)"

    p_fin = previous.get("financial_score") if previous else None
    p_men = previous.get("mental_score") if previous else None
    p_phys = previous.get("physical_score") if previous else None
    p_rel = previous.get("relationship_score") if previous else None

    avg_score = (fin + men + phys + rel) / 4.0

    return (
        f"💰 <b>Moliyaviy:</b> <code>[{bar(fin)}]</code> <b>{fin}/10</b>{diff_str(fin, p_fin)}\n"
        f"🧘 <b>Ruhiy-emotsional:</b> <code>[{bar(men)}]</code> <b>{men}/10</b>{diff_str(men, p_men)}\n"
        f"🏃 <b>Jismoniy & Quvvat:</b> <code>[{bar(phys)}]</code> <b>{phys}/10</b>{diff_str(phys, p_phys)}\n"
        f"👥 <b>Munosabatlar & Oila:</b> <code>[{bar(rel)}]</code> <b>{rel}/10</b>{diff_str(rel, p_rel)}\n"
        f"⚖️ <b>Umumiy Balans:</b> <b>{avg_score:.1f} / 10</b> ({fin+men+phys+rel}/40 ball)"
    )


# =========================================================================
# 5. SOKIN QAYDLAR (SHAXSIY REYTING VA O'ZGARISHLAR DINAMIKASI)
# =========================================================================

@router.callback_query(F.data.in_(["sokin_qaydlar", "my_personal_progress", "my_progress"]))
async def show_personal_progress(callback: CallbackQuery) -> None:
    """Sokin Qaydlar — Foydalanuvchining shaxsiy dinamikasi, Sokinlik Reytingi va 4 ustun tahlili."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    diag = await db.get_first_diagnostic(user["id"])
    checkins_30 = await db.get_checkins_for_period(user["id"], days=30)
    checkins_total = await db.get_checkins_for_period(user["id"], days=365)
    today_checkin = await db.get_today_checkin(user["id"])
    latest_pillars = await db.get_latest_four_pillars(user["id"])
    prev_pillars = await db.get_previous_four_pillars(user["id"])

    # 1. Sokinlik Reytingi (0-100%) hisoblash
    rating_score = 45
    if diag:
        rating_score += 15
    checkin_count = len(checkins_30)
    rating_score += min(25, checkin_count * 3)

    avg_mood = 7.0
    avg_stress = 3.5
    if checkins_30:
        avg_mood = sum(c["mood_score"] for c in checkins_30) / len(checkins_30)
        avg_stress = sum(c["stress_score"] for c in checkins_30) / len(checkins_30)
        diff = (avg_mood - avg_stress) * 2.5
        rating_score = max(15, min(100, int(rating_score + diff)))
    else:
        rating_score = min(60, rating_score)

    filled_blocks = max(1, min(10, int(rating_score / 10)))
    progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)

    if rating_score >= 85:
        rating_badge = "🌟 Mukammal Xotirjamlik"
    elif rating_score >= 70:
        rating_badge = "🌿 Barqaror O'sish"
    elif rating_score >= 50:
        rating_badge = "⏳ Boshlang'ich Yengillik"
    else:
        rating_badge = "🔄 Shakllanish Bosqichi"

    # 2. 4 ta Hayotiy Ustun ko'rinishi
    if latest_pillars:
        pillars_text = _render_pillars_card(latest_pillars, prev_pillars)
    else:
        pillars_text = "<i>Hali 4 ta ustun baholanmadi. Pastdagi «⚖️ 4 ta Hayotiy Ustunni Baholash» tugmasi orqali o'ting.</i>"

    # 3. 1 oy oldin vs Hozir taqqoslovi
    if diag:
        baseline_summary = diag.get("ai_summary", "Diagnostikadan o'tilgan")
        if len(baseline_summary) > 130:
            baseline_summary = baseline_summary[:130] + "..."
        baseline_focus = ", ".join(diag.get("focus_areas", [])) or "Stress va ichki xavotir"
        baseline_info = (
            f"• <b>Boshlang'ich holat:</b> {baseline_summary}\n"
            f"• <b>Aniqlangan zaif nuqtalar:</b> <i>{baseline_focus}</i>"
        )
    else:
        baseline_info = "• <i>Hali dastlabki diagnostikadan o'tmadingiz. Boshlang'ich nuqtani belgilash uchun 'Sokin Diagnostika'dan o'ting.</i>"

    today_status = "✅ Bugungi holat qayd etilgan" if today_checkin else "⏳ Bugun hali qayd etilmadi"

    text = (
        "📝 <b>SOKIN QAYDLAR — SHAXSIY REYTING VA DINAMIKA</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Foydalanuvchi:</b> {user['full_name']}\n"
        f"📅 <b>Botdagi faol davr:</b> {user.get('course_day', 1)}-kun | Jami qaydlar: {len(checkins_total)} ta\n\n"
        f"🏆 <b>SIZNING SOKINLIK REYTINGINGIZ:</b>\n"
        f"<code>[{progress_bar}]</code> <b>{rating_score}%</b> — {rating_badge}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚖️ <b>4 ASOSIY HAYOTIY USTUN (REAL BAHOLAR):</b>\n"
        f"{pillars_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔄 <b>1 OY OLDIN VA HOZIR (TRANSFORMATSIYA):</b>\n"
        f"{baseline_info}\n\n"
        f"📌 <b>Bugungi check-in:</b> {today_status}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Haftalik tahlil va 10/10 ga chiqish rejasini ko'rish uchun quyidagi tugmalardan foydalaning 👇</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=sokin_qaydlar_hub_kb())
    await callback.answer()


# =========================================================================
# 6. 4 TA HAYOTIY USTUNNI BAHOLASH OQIMI (FSM)
# =========================================================================

# =========================================================================
# 6. 4 TA HAYOTIY USTUNNI BAHOLASH OQIMI (ADAPTIV PSIXOLOGIK MONITORING)
# =========================================================================

@router.callback_query(F.data == "start_four_pillars")
async def start_four_pillars(callback: CallbackQuery, state: FSMContext) -> None:
    """4 ta ustun bo'yicha adaptiv psixologik so'rovnomani boshlash."""
    await state.clear()
    await state.set_state(FourPillarsFlow.in_progress)

    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        user = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.full_name, callback.from_user.username
        )

    diag = await db.get_first_diagnostic(user["id"])
    checkins = await db.get_checkins_for_period(user["id"], days=30)

    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    step_data = await ai_service.generate_adaptive_four_pillars_step(
        history=[],
        user=user,
        diagnostic=diag,
        checkins=checkins,
        step_count=0,
    )

    q_text = step_data.get("question", "Oxirgi kunlardagi holatingiz haqida qanday xulosa qilasiz?")
    options = step_data.get("options", [
        "Barqaror va xotirjam",
        "Moddiy xavotir bor",
        "Charchoq va uyqusizlik",
        "Munosabatlarda tushunilmaslik",
    ])

    await state.update_data(
        fp_history=[],
        current_question=q_text,
        current_options=options,
        step_count=0,
    )

    text = (
        "⚖️ <b>SOKIN QAYDLAR — 4 TA HAYOTIY SOHANI CHUQUR MONITORING QILISH</b> 🌿\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Har bir sohaga (Moliya, Ruhiyat, Tana, Munosabatlar) 5 tadan (jami 20 ta) maxsus savollar "
        "orqali sizning imkoniyatlaringiz, o'zgarishlaringiz va to'siqlaringiz chuqur aniqlanadi.</i>\n\n"
        f"❓ <b>1-savol (Jami 20 tadan):</b>\n{q_text}"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=dynamic_four_pillars_options_kb(options))
    await callback.answer()


@router.callback_query(FourPillarsFlow.in_progress, F.data.startswith("fp_opt:"))
async def handle_four_pillars_option(callback: CallbackQuery, state: FSMContext) -> None:
    """Foydalanuvchi variant tugmasini tanlaganda."""
    data = callback.data
    state_data = await state.get_data()
    current_options = state_data.get("current_options", [])

    if data == "fp_opt:custom":
        await state.set_state(FourPillarsFlow.waiting_custom_text)
        await callback.message.answer(
            "✍️ <b>O'z fikringiz va aniq holatingizni erkin yozing:</b>\n\n"
            "<i>(Ushbu savol bo'yicha his-tuyg'ularingiz, hayotiy vaziyatingiz yoki muammongizni batafsil yozib yuboring...)</i> 👇",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    try:
        opt_idx = int(data.split(":")[1])
        answer_text = current_options[opt_idx]
    except Exception:
        answer_text = "Belgilandi"

    await _process_next_four_pillars_step(callback.message, state, callback.from_user, answer_text)
    await callback.answer()


@router.message(FourPillarsFlow.waiting_custom_text)
async def handle_four_pillars_custom_text(message: Message, state: FSMContext) -> None:
    """Foydalanuvchi erkin matn yuborganda."""
    raw_text = message.text.strip() if message.text else ""
    answer_text = raw_text[:600] if len(raw_text) > 600 else raw_text
    await state.set_state(FourPillarsFlow.in_progress)
    await _process_next_four_pillars_step(message, state, message.from_user, answer_text)


async def _process_next_four_pillars_step(message, state: FSMContext, from_user, answer_text: str) -> None:
    """Keyingi adaptiv savol yoki yakuniy xulosani tayyorlash."""
    state_data = await state.get_data()
    history = state_data.get("fp_history", [])
    current_question = state_data.get("current_question", "")
    step_count = state_data.get("step_count", 0) + 1

    history.append({
        "question": current_question,
        "answer": answer_text,
    })

    user = await db.get_user_by_telegram_id(from_user.id)
    if not user:
        user = await db.get_or_create_user(from_user.id, from_user.full_name, from_user.username)

    diag = await db.get_first_diagnostic(user["id"])
    checkins = await db.get_checkins_for_period(user["id"], days=30)

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    step_res = await ai_service.generate_adaptive_four_pillars_step(
        history=history,
        user=user,
        diagnostic=diag,
        checkins=checkins,
        step_count=step_count,
    )

    is_finished = (step_res.get("is_finished") and step_count >= 20) or step_count >= 20

    if not is_finished:
        next_q = step_res.get("question", "Keyingi holat bo'yicha hislaringiz:")
        next_options = step_res.get("options", [
            "Erkin va xotirjam",
            "Ichki xavotir va siqilish",
            "Ba'zan yaxshi, ba'zan qiyin",
            "Ichimga yutib jim turaman",
            "Qo'rquv va noaniqlik",
        ])
        await state.update_data(
            fp_history=history,
            current_question=next_q,
            current_options=next_options,
            step_count=step_count,
        )
        text = (
            f"✅ <i>Javobingiz tahlilga kiritildi.</i>\n\n"
            f"❓ <b>{step_count + 1}-savol (Jami 20 tadan):</b>\n{next_q}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=dynamic_four_pillars_options_kb(next_options))
    else:
        # Yakuniy hisob-kitob (AI o'zi aniqlagan ballar va tahlillar)
        fin = max(1, min(10, step_res.get("financial_score", 6)))
        men = max(1, min(10, step_res.get("mental_score", 7)))
        phys = max(1, min(10, step_res.get("physical_score", 6)))
        rel = max(1, min(10, step_res.get("relationship_score", 7)))

        prev_pillars = await db.get_latest_four_pillars(user["id"])
        current_pillars = await db.save_four_pillars_record(
            user_id=user["id"],
            financial_score=fin,
            mental_score=men,
            physical_score=phys,
            relationship_score=rel,
            ai_advice=step_res.get("overall_critique"),
        )
        await state.clear()

        pillars_card = _render_pillars_card(current_pillars, prev_pillars)

        fin_an = step_res.get("financial_analysis", "Moliyaviy soha imkoniyatlari va pulga munosabat shakllangan.")
        men_an = step_res.get("mental_analysis", "Ruhiy va emotsional barqarorlik, o'ziga ishonch tahlili.")
        phys_an = step_res.get("physical_analysis", "Tana quvvati, uyqu va asab tizimi imkoniyatlari tahlili.")
        rel_an = step_res.get("relationship_analysis", "Munosabatlar, oilaviy muhit va shaxsiy chegaralar tahlili.")
        critique = step_res.get("overall_critique", "20 ta savol tahlili asosida hayotiy sohalar uyg'unligi belgilandi.")

        roadmap = step_res.get("roadmap_to_10", [])
        roadmap_text = "\n".join(f"• {r}" for r in roadmap) if roadmap else "• Barcha jabhalarda kichik intizomiy qadamlar"

        response_text = (
            "⚖️ <b>4 TA HAYOTIY SOHANGIZNING 20 TA SAVOL ASOSIDAGI CHUQUR NATIJASI</b> 🌿\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{pillars_card}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔍 <b>4 TA SOHANING ALOHIDA CHUQUR TAHLILI VA IMKONIYATLARI:</b>\n\n"
            f"💰 <b>1. Moliyaviy Holat & Pul Imkoniyatlari (5 ta savol tahlili):</b>\n<i>{fin_an}</i>\n\n"
            f"🧘 <b>2. Ruhiy & Emotsional Holat, O'ziga Ishonch (5 ta savol tahlili):</b>\n<i>{men_an}</i>\n\n"
            f"🏃 <b>3. Jismoniy Salomatlik, Uyqu & Quvvat (5 ta savol tahlili):</b>\n<i>{phys_an}</i>\n\n"
            f"👥 <b>4. Munosabatlar, Oila & Chegaralar (5 ta savol tahlili):</b>\n<i>{rel_an}</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🧑‍⚕️ <b>Furqat Bag'ibekov Yordamchisi Shaxsiy Xulosasi:</b>\n{critique}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>10 DAN 10 GA CHIQARISH VA IMKONIYATLARNI OCHISH YO'L XARITASI:</b>\n"
            f"{roadmap_text}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Ushbu tashxis 4 ta sohaga berilgan 20 ta chuqur savollarga bergan javoblaringiz asosida tuzildi 🌿</i>"
        )
        await message.answer(response_text, parse_mode="HTML", reply_markup=sokin_qaydlar_hub_kb())


# ---------- Bugungi Kunlik Hisobot ----------

@router.callback_query(F.data == "progress_daily")
async def show_daily_report(callback: CallbackQuery) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    today_checkin = await db.get_today_checkin(user["id"])

    if not today_checkin:
        await callback.message.answer(
            "⏳ <b>Bugun hali kuzatuv qayd etilmadi.</b>\n\n"
            "Bugungi kayfiyatingiz, stress darajangiz, erishgan yutug'ingiz va qiyinchiliklaringizni "
            "yozish uchun pastdagi tugmani bosing 👇",
            parse_mode="HTML",
            reply_markup=sokin_qaydlar_hub_kb(),
        )
        await callback.answer()
        return

    mood = today_checkin.get("mood_score", 0)
    stress = today_checkin.get("stress_score", 0)
    achievements = today_checkin.get("achievements") or "Belgilanmagan"
    struggles = today_checkin.get("struggles") or "Belgilanmagan"
    note = today_checkin.get("note") or "Mavjud emas"

    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    ai_feedback = await ai_service.daily_checkin_feedback(
        mood=mood,
        stress=stress,
        achievements=achievements,
        struggles=struggles,
        note=today_checkin.get("note"),
    )

    text = (
        "📅 <b>BUGUNGI KUNLIK HISOBOT VA O'ZGARISHLAR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Kayfiyat darajasi:</b> {mood}/10\n"
        f"⚡️ <b>Stress darajasi:</b> {stress}/10\n"
        f"🏆 <b>Erishilgan yutuq:</b> {achievements}\n"
        f"⚠️ <b>Duch kelingan qiyinchilik:</b> {struggles}\n"
        f"💭 <b>Shaxsiy izoh:</b> {note}\n\n"
        f"🧑‍⚕️ <b>Furqat Bag'ibekov Yordamchisi Xulosasi:</b>\n{ai_feedback}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=sokin_qaydlar_hub_kb())
    await callback.answer()


# ---------- Haftalik Tahlil (7 kunlik & 10/10 Rejasi) ----------

@router.callback_query(F.data == "progress_weekly")
async def show_weekly_report(callback: CallbackQuery) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    checkins = await db.get_checkins_for_period(user["id"], days=7)
    baseline_diag = await db.get_first_diagnostic(user["id"])
    latest_pillars = await db.get_latest_four_pillars(user["id"])
    prev_pillars = await db.get_previous_four_pillars(user["id"])

    if not checkins and not latest_pillars:
        await callback.message.answer(
            "Haftalik tahlil uchun hali yetarli ma'lumot yo'q. "
            "Har kuni holatingizni qayd etib boring va 4 ta ustunni baholang — "
            "shunda haftalik o'zgarishlar va 10/10 rejasi shakllanadi 🌿",
            reply_markup=sokin_qaydlar_hub_kb(),
        )
        await callback.answer()
        return

    avg_mood = (sum(c["mood_score"] for c in checkins) / len(checkins)) if checkins else 7.0
    avg_stress = (sum(c["stress_score"] for c in checkins) / len(checkins)) if checkins else 3.5

    achievements_list = [c["achievements"] for c in checkins if c.get("achievements")]
    struggles_list = [c["struggles"] for c in checkins if c.get("struggles")]

    ach_text = "\n".join(f"• {a}" for a in achievements_list[-4:]) if achievements_list else "• O'z-o'zini muntazam kuzatish"
    strg_text = "\n".join(f"• {s}" for s in struggles_list[-4:]) if struggles_list else "• Kichik kundalik charchoqlar"

    pillars_summary = _render_pillars_card(latest_pillars, prev_pillars) if latest_pillars else "<i>4 ta ustun baholanmagan</i>"

    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    ai_weekly_review = await ai_service.generate_weekly_progress_review(user, checkins, baseline_diag)

    text = (
        "🗓 <b>7 KUNLIK HAFTALIK O'ZGARISHLAR VA 10/10 REJASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Kuzatuvlar soni:</b> {len(checkins)} ta kun\n"
        f"📈 <b>Haftalik o'rtacha kayfiyat:</b> {avg_mood:.1f}/10\n"
        f"⚡️ <b>Haftalik o'rtacha stress:</b> {avg_stress:.1f}/10\n\n"
        "⚖️ <b>4 ta Hayotiy Ustun Dinamikasi:</b>\n"
        f"{pillars_summary}\n\n"
        f"🏆 <b>Hafta davomida erishilgan yutuqlar:</b>\n{ach_text}\n\n"
        f"⚠️ <b>Duch kelingan asosiy kamchiliklar:</b>\n{strg_text}\n\n"
        f"🧑‍⚕️ <b>Furqat Bag'ibekov Yordamchisi Haftalik Tahlili:</b>\n{ai_weekly_review}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=sokin_qaydlar_hub_kb())
    await callback.answer()


# ---------- Oylik Dinamika (30 kunlik) ----------

@router.callback_query(F.data == "progress_monthly")
async def show_monthly_report(callback: CallbackQuery) -> None:
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    checkins_30d = await db.get_checkins_for_period(user["id"], days=30)
    baseline_diag = await db.get_first_diagnostic(user["id"])

    if not checkins_30d and not baseline_diag:
        await callback.message.answer(
            "Oylik tahlil uchun hali yetarli ma'lumot yo'q. "
            "Dastlab diagnostikadan o'ting va kunlik kuzatuvlarni davom ettiring 🌿",
            reply_markup=progress_hub_kb(),
        )
        await callback.answer()
        return

    baseline_text = "Mavjud emas"
    if baseline_diag:
        baseline_text = baseline_diag.get("ai_summary", "Diagnostika o'tkazilgan")

    avg_mood_30 = (sum(c["mood_score"] for c in checkins_30d) / len(checkins_30d)) if checkins_30d else 0
    avg_stress_30 = (sum(c["stress_score"] for c in checkins_30d) / len(checkins_30d)) if checkins_30d else 0

    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    ai_monthly_review = await ai_service.generate_monthly_progress_review(user, checkins_30d, baseline_diag)

    text = (
        "🌕 <b>30 KUNLIK OYLIK DINAMIKA VA TRANSFORMASIYA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Botdan foydalanish davri:</b> {user['course_day']}-kun\n"
        f"📝 <b>Qayd etilgan check-inlar:</b> {len(checkins_30d)} ta kun\n"
        f"📈 <b>Oylik o'rtacha kayfiyat:</b> {avg_mood_30:.1f}/10\n"
        f"⚡️ <b>Oylik o'rtacha stress:</b> {avg_stress_30:.1f}/10\n\n"
        f"🧠 <b>Dastlabki holatingiz (Baseline):</b>\n<i>{baseline_text}</i>\n\n"
        f"🌟 <b>Furqat Bag'ibekov Yordamchisi Oylik Tahlili:</b>\n{ai_monthly_review}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=sokin_qaydlar_hub_kb())
    await callback.answer()


# ---------- Navigatsiya ----------

@router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "Asosiy menyu 👇",
        reply_markup=main_menu_kb(is_admin=is_admin(callback.from_user.id)),
    )
    await callback.answer()
