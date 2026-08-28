"""
SOKIN QALB — sun'iy intellekt xizmat qatlami (Google Gemini API).

Bu modul quyidagi barcha AI funksiyalarini boshqaradi:
1. Dastlabki psixologik diagnostika tahlili (analyze_diagnostic)
2. Har kungi check-in'da darhol shaxsiy iliq AI izohi va maslahat (daily_checkin_feedback)
3. AI Maslahatchi bilan jonli psixologik suhbat (ai_consultant_chat)
4. Tezkor SOS / Anti-stress / Vahima yordami (sos_emergency_relief)
5. Haftalik va chuqur progress tahlili (weekly_progress_note, generate_deep_progress_analysis)
6. Admin uchun AI Post generatsiyasi va auditoriya tahlili (admin_generate_post, admin_analyze_audience)
"""
import asyncio
import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, FOUNDER_NAME, CLINIC_CONTACT

logger = logging.getLogger(__name__)

# Google GenAI mijozini ishga tushirish
client = genai.Client(api_key=GEMINI_API_KEY)

# Eng tez va barqaror bepul Gemini modellari (navbat bilan)
CANDIDATE_MODELS = [
    GEMINI_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
]


async def _generate_content_robust(
    contents: str,
    system_instruction: str,
    max_output_tokens: int = 800,
    response_mime_type: Optional[str] = None,
    timeout_seconds: float = 30.0,
) -> str:
    """Gemini API ga mustahkam so'rov jo'natish (timeout va fallback modellari bilan)."""
    last_error = None
    # Modellarni takrorlarsiz saralash
    models_to_try = []
    for m in CANDIDATE_MODELS:
        if m and m not in models_to_try:
            models_to_try.append(m)

    for model_name in models_to_try:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=max_output_tokens,
                temperature=0.7,
            )
            if response_mime_type:
                config.response_mime_type = response_mime_type

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=model_name,
                    contents=contents,
                    config=config,
                ),
                timeout=timeout_seconds,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning("Model %s bilan xatolik: %s (%s). Keyingisiga urinib ko'rilmoqda...", model_name, type(e).__name__, e)
            last_error = e

    logger.error("Barcha Gemini modellari bilan ulanishda xatolik: %s (%s)", type(last_error).__name__ if last_error else 'Unknown', last_error)
    raise last_error or RuntimeError("Gemini API javob bermadi.")


# -------------------------------------------------------------
# 1. DINAMIK ADAPTIV AI DIAGNOSTIKA
# -------------------------------------------------------------

DYNAMIC_DIAGNOSTIC_SYSTEM_PROMPT = f"""Sen 12 yillik tajribaga ega yetakchi psixoterapevt "{FOUNDER_NAME}"ning shaxsiy yordamchisisan. \
Sen foydalanuvchi bilan xuddi haqiqiy inson yozayotgandek iliq, samimiy, tirik va professional tilda muloqot qilasan.

VAZIFANG:
Foydalanuvchi bilan jonli, bosqichma-bosqich, chuqur, shaxsiy va keng qamrovli psixologik diagnostika o'tkazish.
Diagnostika faqat stress bilan cheklanmay, inson hayotining BARCHA asosiy jabhalarini qamrab oladi:
1. 💰 Moliyaviy va moddiy holat (moliyaviy xavotir, pul yetishmovchiligi, pulga nisbatan ichki bloklar, kelajakdan qo'rquv).
2. 👥 Munosabatlar va oilaviy muhit (oiladagi tushunmovchiliklar, ajralish/xiyonat, yolg'izlik, chegaralar buzilishi).
3. 💎 O'ziga ishonch va o'z qadrini bilish (o'ziga past baho berish, aybdorlik, boshqalarga bog'liqlik, "yo'q" deya olmaslik).
4. 🧘 Ruhiy-emotsional & Tana (surunkali xavotir, uyqusizlik, hissiy charchoq, tanadagi psixosomatik qisilishlar).
5. 🎂 Tug'ilgan sana / yosh bosqichi (insonning yoshi va hayotiy bosqichidan kelib chiqib, uning KUCHLI (resursli) va KUCHSIZ (zaif/kamchilik) taraflarini aniqlash).

QOIDALAR:
1. Hech qachon bir xil, shablon savollar berma. Foydalanuvchining aytgan muammosi va yoshiga qarab aynan uning ildizini ochib beruvchi individual savollar tuz.
2. JUDA MUHIM TUGMA TALABI: Har bir variant matni qisqa, lo'nda, aniq va ixcham bo'lishi shart (ko'pi bilan 4-6 ta so'z, 30-35 ta belgi). \
   Hech qachon uzun gap yozma, toki Telegram tugmasida hech qanday '...' siz, 100% to'liq sig'sin va foydalanuvchi tugmaning o'zida to'liq o'qiy olsin!
3. Jarayon odatda 5 tadan 7 tagacha chuqur savoldan iborat bo'ladi:
   - 1-savol: Tug'ilgan sana/yosh va asosiy shikoyatni aniqlash.
   - 2-4-savollar: Oldingi javoblarga asoslanib moliya, munosabatlar, o'ziga ishonch yoki ruhiy holatdagi ildiz sabablarni chuqurlashtirib o'rganish.
   - 5-6/7-savollar: Yetarli ma'lumot to'plangach, "is_finished": true qilib yakuniy chuqur tashxis, KUCHLI va KUCHSIZ taraflar tahlilini berish.
4. Agar insonning javoblarida o'ziga yoki boshqalarga zarar yetkazish, suitsid belgilari sezilsa — darhol "risk_flag": true qilib yakunla.
5. Faqat va faqat quyidagi JSON formatida javob qaytar:

AGAR SAVOL-JAVOB DAVOM ETAYOTGAN BO'LSA ("is_finished": false):
{{
  "is_finished": false,
  "question_number": 2,
  "question": "Oldingi javobingizdan kelib chiqqan juda chuqur va aniq savol...",
  "options": [
    "Qisqa 1-variant (4-6 so'z)",
    "Qisqa 2-variant (4-6 so'z)",
    "Qisqa 3-variant (4-6 so'z)",
    "Qisqa 4-variant (4-6 so'z)"
  ]
}}

AGAR INSONNI TO'LIQ O'RGANIB BO'LIB, TASHXIS QO'YISH VAQTI KELSA ("is_finished": true):
{{
  "is_finished": true,
  "summary": "Insonning yoshi, psixologik portreti va ayni damdagi holatiga 3-4 gapdan iborat chuqur, samimiy va professional xulosa...",
  "strengths": [
    "🌟 1-kuchli tarafingiz (masalan: Yuqori mas'uliyat va ichki iroda kuchi)",
    "🌟 2-kuchli tarafingiz (masalan: Insonlarni tushunish va empatiya qobiliyati)",
    "🌟 3-kuchli tarafingiz (masalan: O'zgarishga va rivojlanishga intilish)"
  ],
  "identified_issues": [
    "⚠️ 1-zaif nuqta/kamchilik (masalan: Moliyaviy xavotir va pulga nisbatan ichki bloklar)",
    "⚠️ 2-zaif nuqta/kamchilik (masalan: O'ziga past baho berish va chegaralarni qo'ya olmaslik)",
    "⚠️ 3-zaif nuqta/kamchilik (masalan: Surunkali xavotir va tuyg'ularni ichga yutish)"
  ],
  "focus_areas": [
    "1-yo'nalish: O'z qadrini oshirish va ichki ishonchni tiklash",
    "2-yo'nalish: Moliyaviy xavotirlardan xalos bo'lish va kognitiv xotirjamlik",
    "3-yo'nalish: Tana relaksatsiyasi va his-tuyg'ularni erkin ifodalash"
  ],
  "course_outline": [
    {{"day": 1, "theme": "O'zini anglash va ichki resurslarni uyg'otish"}},
    {{"day": 2, "theme": "O'ziga ishonch va mustahkam chegaralar"}},
    {{"day": 3, "theme": "Moliyaviy xavotir va bloklarni yechish"}},
    {{"day": 4, "theme": "Munosabatlardagi og'riqlarni davolash"}},
    {{"day": 5, "theme": "Ichki xotirjamlik va yangi muvaffaqiyatlar"}}
  ],
  "risk_flag": false
}}
"""


import re


def _parse_json_safely(raw_text: str) -> dict:
    """JSON matnini turli format xatolaridan tozalab, xavfsiz o'qiydi."""
    if not raw_text:
        raise ValueError("Bo'sh matn")

    cleaned = raw_text.strip()
    # 1. ```json ... ``` olib tashlash
    if "```" in cleaned:
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # 2. Tashqi { ... } blokini ajratib olish
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]

    # 3. To'g'ridan-to'g'ri json.loads
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 4. Trailing comma (masalan: [..., ] yoki {..., }) larni tozalash
    cleaned_fixed = re.sub(r",\s*([\]}])", r"\1", cleaned)
    try:
        return json.loads(cleaned_fixed)
    except json.JSONDecodeError:
        pass

    # 5. Yangi qatorlarni tozalash
    cleaned_fixed = re.sub(r"[\r\n]+", " ", cleaned_fixed)
    return json.loads(cleaned_fixed)


async def generate_adaptive_diagnostic_step(
    history: list[dict],
    user_name: str,
    step_count: int,
) -> dict:
    """Foydalanuvchining oldingi javoblariga qarab keyingi individual savolni yoki yakuniy tashxisni generatsiya qiladi."""
    if not history:
        user_content = (
            f"Foydalanuvchi: {user_name}\n"
            "Bu ko'p qirrali chuqur diagnostikaning 1-qadami.\n"
            "Insonning yoshi/tug'ilgan sanasi va hozirda uni eng ko'p qiynayotgan hayotiy sohasini "
            "(Moliya, Munosabatlar, O'ziga ishonch, Ruhiy stress va tana) aniqlash uchun "
            "iliq, do'stona 1-savolni va unga mos 4 ta qisqa variantni ber."
        )
    else:
        history_lines = []
        for idx, item in enumerate(history, 1):
            history_lines.append(f"{idx}-savol: {item.get('question', '')}\nJavob: {item.get('answer', '')}")

        user_content = (
            f"Foydalanuvchi: {user_name}\n"
            f"Hozirgi qadam: {step_count + 1}-savol.\n\n"
            f"Savol-javoblar tarixi:\n" + "\n\n".join(history_lines) + "\n\n"
        )
        if step_count >= 5:
            user_content += (
                "Foydalanuvchi allaqachon 5+ ta savolga javob berdi. "
                "Insonning yoshi, moliyaviy, munosabatlar va o'ziga ishonch holatidan kelib chiqib, "
                "'is_finished': true qilib uning KUCHLI taraflari, KUCHSIZ taraflari va yakuniy tashxisini ber."
            )
        else:
            user_content += (
                "Foydalanuvchining so'nggi javobiga (moliya, munosabatlar, o'ziga ishonch, stress) chuqur e'tibor qaratib, "
                "uning muammosi ildizini aniqroq ochib beruvchi keyingi chuqur savol va 4 ta yangi qisqa variantni yarat ('is_finished': false)."
            )

    try:
        raw_text = await _generate_content_robust(
            contents=user_content,
            system_instruction=DYNAMIC_DIAGNOSTIC_SYSTEM_PROMPT,
            max_output_tokens=1000,
            response_mime_type="application/json",
            timeout_seconds=25.0,
        )
        data = _parse_json_safely(raw_text)
        if isinstance(data, dict) and ("question" in data or "summary" in data):
            return data
    except Exception:
        logger.exception("Dinamik adaptiv diagnostika qadami generatsiyasida xatolik")

    # Fallback agar Gemini vaqtincha javob bermasa
    if step_count == 0:
        return {
            "is_finished": False,
            "question_number": 1,
            "question": "Assalomu alaykum! Shaxsiy kuchli va kuchsiz taraflaringizni aniqlash uchun ayting-chi, ayni paytda sizni ko'proq qaysi soha qiynamoqda?",
            "options": [
                "Moliyaviy va moddiy qiyinchilik",
                "Oilaviy munosabatlar va ziddiyat",
                "O'ziga ishonchsizlik va qadrsizlik",
                "Kuchli stress, xavotir va uyqusizlik",
            ],
        }
    elif step_count < 5:
        return {
            "is_finished": False,
            "question_number": step_count + 1,
            "question": "Ushbu sohadagi qiyinchilik sizga qanday eng katta ta'sir ko'rsatmoqda?",
            "options": [
                "Kelajakdan qo'rquv va xavotir beradi",
                "O'zimga bo'lgan ishonchni so'ndiradi",
                "Yaqinlarim bilan munosabatni buzadi",
                "Jismoniy charchoq va uyquni oladi",
            ],
        }
    else:
        return {
            "is_finished": True,
            "summary": "Tahlil shuni ko'rsatmoqdaki, sizda yuqori mas'uliyat va o'zgarishga intilish bor, ammo moliyaviy xavotirlar, o'ziga nisbatan tanqid va tuyg'ularni ichga yutish ichki quvvatingizni so'ndirmoqda.",
            "strengths": [
                "Yuqori mas'uliyat va iroda kuchi",
                "Insonlarni tushunish va samimiylik",
                "O'z hayotini yaxshilashga intilish",
            ],
            "identified_issues": [
                "Moliyaviy xavotirlar va pulga nisbatan ichki bloklar",
                "O'ziga past baho berish va qadrsizlik hissi",
                "Tuyg'ularni ichga yutish va ortiqcha o'ylash",
            ],
            "focus_areas": [
                "O'z qadrini tiklash va ichki ishonchni oshirish",
                "Moliyaviy xavotirlarni kamaytirish",
                "Hissiyotlarni erkin ifodalash va xotirjamlik",
            ],
            "course_outline": [
                {"day": 1, "theme": "O'zini anglash va kuchli resurslarni ochish"},
                {"day": 2, "theme": "O'ziga ishonch va mustahkam chegaralar"},
                {"day": 3, "theme": "Moliyaviy bloklar va xavotirlarni yechish"},
                {"day": 4, "theme": "Munosabatlardagi og'riqlarni davolash"},
                {"day": 5, "theme": "To'liq xotirjamlik va yangi bosqich"},
            ],
            "risk_flag": False,
        }


async def analyze_diagnostic(answers: dict[str, str]) -> dict:
    """Eski muvofiqlik uchun tahlil funksiyasi."""
    return await generate_adaptive_diagnostic_step(
        history=[{"question": q, "answer": a} for q, a in answers.items()],
        user_name="Foydalanuvchi",
        step_count=len(answers),
    )


# -------------------------------------------------------------
# 2. KUNDALIK CHECK-IN DARHOL SHAXSIY AI IZOHI
# -------------------------------------------------------------

DAILY_CHECKIN_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt {FOUNDER_NAME}ning shaxsiy yordamchisisan. \
Sen foydalanuvchiga xuddi haqiqiy tirik inson yozayotgandek iliq, samimiy va dalda beruvchi tilda yozasan. Foydalanuvchi hozirgina bugungi holatini qayd etdi:
- Kayfiyat (1-10)
- Stress darajasi (1-10)
- Bugungi erishilgan yutuqlari/yengilliklari (achievements)
- Bugungi qiyinchiliklari/kamchiliklari (struggles)
- Shaxsiy izohi (note)

Vazifang:
1. Foydalanuvchining bugungi yutuqlarini (agar bo'lsa) samimiy e'tirof etib, quvvatlash.
2. Agar qiyinchilik yoki yuqori stress bo'lsa, uni tushunuvchi, dalda beruvchi va aynan bugun uchun 1 ta amaliy kichik psixologik maslahat berish.
3. Hajmi: 3-5 ta lo'nda, juda iliq va empatik jumla.
4. Til: sof o'zbek tili (lotin), mehrli va quvvatlovchi ohangda. Tashxis qo'yma."""


async def daily_checkin_feedback(
    mood: int,
    stress: int,
    achievements: Optional[str] = None,
    struggles: Optional[str] = None,
    note: Optional[str] = None,
) -> str:
    """Kunlik check-in dan so'ng foydalanuvchiga yutuqlari va kamchiliklari bo'yicha darhol shaxsiy javob beradi."""
    content = f"Kayfiyat: {mood}/10\nStress: {stress}/10\n"
    if achievements:
        content += f"Bugungi yutuqlar/yengilliklar: {achievements}\n"
    if struggles:
        content += f"Bugungi qiyinchiliklar/kamchiliklar: {struggles}\n"
    if note:
        content += f"Foydalanuvchi izohi: \"{note}\"\n"

    try:
        reply = await _generate_content_robust(
            contents=content,
            system_instruction=DAILY_CHECKIN_PROMPT,
            max_output_tokens=400,
        )
        return reply
    except Exception:
        logger.exception("Daily checkin feedback xatoligi")
        if stress >= 7:
            return "Bugungi qiyinchiliklarga qaramay, o'zingizni kuzatib qayd etganingiz — katta yutuq. Iltimos, o'zingizga biroz vaqt ajrating, chuqur nafas oling va yelkangizdagi taranglikni bo'shating. Siz yolg'iz emassiz 🌿"
        return "Bugungi yutuqlaringiz va holatingizni qayd etganingiz uchun rahmat! Har bir ongli qadam xotirjamlik sari yo'ldir 🌿"


# -------------------------------------------------------------
# 3. BAG'IBEKOV FURQAT YORDAMCHISI BILAN JONLI SUHBAT
# -------------------------------------------------------------

AI_CHAT_OPENING_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt {FOUNDER_NAME}ning shaxsiy yordamchisisan. \
Foydalanuvchi hozirgina diagnostikadan o'tib, senga yozmoqda.

VAZIFANG:
Foydalanuvchiga birinchi bo'lib o'zing samimiy, mehrli, haqiqiy insondek va professional xat yozib, jonli muloqotni boshlab berish:
1. Ismi bilan iliq salomlash (masalan: "Assalomu alaykum, {{user_name}}! 🌿 Men — {FOUNDER_NAME}ning shaxsiy yordamchisiman.").
2. Diagnostika natijalarini ko'rganingni va undagi aniqlangan holatlarni tushunarli bayon qil (masalan: "Men sizning diagnostika javoblaringizni chuqur o'rganib chiqdim. Sizda [aniqlangan kamchiliklar: xavotir, uyqu buzilishi, tana tarangligi] borligi ma'lum bo'ldi").
3. Insondan buni tasdiqlashini va his-tuyg'ularini so'ra: "Ayting-chi, haqiqatan ham ayni paytda sizni shu holatlar eng ko'p qiynayaptimi? Yoki ichingizda yana boshqa aytmoqchi bo'lgan og'riq yoki sabab bormi?"
4. Dalda berib, yordam berishga tayyorligingni ayt: "Keling, birgalikda buni bosqichma-bosqich bartaraf qilamiz. Menga bemalol xohlagancha yozing — men sizni eshitishga tayyorman 💙"

Hajmi: 3-5 ta lo'nda, samimiy va professional jumla. Sof o'zbek tilida (lotin)."""


async def generate_diagnostic_opening_message(user_name: str, diagnostic: Optional[dict]) -> str:
    """Diagnostikadan so'ng yordamchi foydalanuvchiga birinchi bo'lib yozadigan shaxsiy xabari."""
    diag_summary = diagnostic.get("ai_summary", "Ichki xavotir va tana tarangligi") if diagnostic else "Ichki xavotir va stress"
    focus_list = diagnostic.get("focus_areas", []) if diagnostic else []
    focus_str = ", ".join(focus_list) if focus_list else "Xotirjamlikni tiklash"

    content = (
        f"Foydalanuvchi ismi: {user_name}\n"
        f"Diagnostika xulosasi: {diag_summary}\n"
        f"Tiklanishi lozim bo'lgan sohalar: {focus_str}\n"
    )

    try:
        reply = await _generate_content_robust(
            contents=content,
            system_instruction=AI_CHAT_OPENING_PROMPT,
            max_output_tokens=450,
        )
        return reply
    except Exception:
        logger.exception("Opening message xatoligi")
        return (
            f"Assalomu alaykum, {user_name}! 🌿 Men — {FOUNDER_NAME}ning shaxsiy yordamchisiman. Sizning diagnostika natijalaringizni chuqur o'rganib chiqdim. "
            f"Sizda {diag_summary.lower()} belgilari kuzatilmoqda. Ayting-chi, haqiqatan ham ayni paytda sizni shu holatlar eng ko'p qiynayaptimi? "
            "Keling, birgalikda buni bosqichma-bosqich yechamiz. Menga bemalol ichki hislaringizni yozing — men sizni tinglayapman 💙"
        )


AI_CHAT_SYSTEM_PROMPT = f"""Sen 12 yillik tajribaga ega yetakchi psixoterapevt {FOUNDER_NAME}ning shaxsiy yordamchisisan. \
Sen foydalanuvchi bilan xuddi haqiqiy inson yozayotgandek iliq, samimiy, empatik, do'stona va professional tilda muloqot qilasan.

{FOUNDER_NAME}NING KLINIK DAVOLASH METODIKASI:
Psixoterapevt {FOUNDER_NAME} o'z amaliyotida eng ilg'or, noyob va jahon andozalaridagi uskunalar bilan kompleks davolashni olib boradi:
1. 👨‍⚕️ <b>Shaxsiy Psixoterapevtik Konsultatsiya:</b> Inson bilan yuzma-yuz chuqur muloqot va ruhiy ildizlarni aniqlash.
2. 💊 <b>Xitoydan keltirilgan maxsus Kapsula (Kapsulaterapiya):</b> Tanani chuqur somatik relaksatsiya holatiga keltiruvchi, barcha tana qisilishlari va psixosomatik bloklarni yechuvchi uskuna.
3. 💡 <b>Fransiyadan keltirilgan maxsus Ko'z Neyro-Lampasi (stroboskopik yorug'lik):</b> Ko'zga ritmik yonib-o'chib ta'sir qiluvchi, miya to'lqinlarini chuqur alfa va teta holatiga tushirib, ong osti bilan to'g'ridan-to'g'ri muloqot o'rnatishga yordam beruvchi innovatsion qurilma.
4. 🎶 <b>Maxsus Neyro-Akustik Musiqa:</b> Ong ostidagi surunkali stress, qo'rquv, psixoz, vahima va tushkunlik bloklarini tezkor ochuvchi terapevtik audio fon.
Ushbu metodika insonning ong ostiga bir zumda tushib, muammoni yuzaki emas, aynan ILDIZI bilan bartaraf etishga xizmat qiladi.

VAZIFANG:
Foydalanuvchiga hissiy yengillik, stress, xavotir, uyqusizlik, charchoq, moliyaviy yoki munosabatlardagi qiyinchiliklarda \
iliq, do'stona, professional va empatik tarzda psixologik yordam berish, {FOUNDER_NAME}ning metodikasi asosida tushuntirish va zarur bo'lganda ushbu jonli seanslarga yo'naltirish.

QOIDALAR:
1. Tibbiy dori vositalarini tavsiya qilma.
2. Foydalanuvchini diqqat bilan eshit, his-tuyg'ularini inkor qilma (validatsiya qil: "Sizni tushunaman, bu holatda shunday his qilish tabiiy...").
3. Amaliy, oson bajariladigan kognitiv-xulqiy yoki tana-yo'naltirilgan mashqlar taklif qil (nafas mashqi, ong osti bilan ishlash, diqqatni tanaga qaratish).
4. Agar foydalanuvchida chuqur psixosomatika, surunkali xavotir, psixoz yoki tushkunlik sezilsa, {FOUNDER_NAME}ning Xitoy kapsulaterapiyasi va Fransiya neyro-chirog'i asosidagi jonli seanslarini samimiy tavsiya qil.
5. Har doim o'zbek tilida (lotin alifbosida), juda chiroyli, muloyim va tushunarli yoz.
6. Javoblaring juda cho'zilib ketmasin (o'rtacha 3-6 jumla), foydalanuvchiga o'zini ifodalashi uchun joy qoldir."""


async def ai_consultant_chat(
    user_message: str,
    history: list[dict],
    user_info: Optional[dict] = None,
    diagnostic: Optional[dict] = None,
) -> str:
    """AI Maslahatchi suhbati (diagnostika konteksti bilan)."""
    # Suhbat kontekstini tayyorlash
    formatted_context = ""
    if user_info:
        formatted_context += f"[Foydalanuvchi: {user_info.get('full_name', 'Foydalanuvchi')}, Kurs kuni: {user_info.get('course_day', 0)}]\n"
    if diagnostic:
        formatted_context += f"[Diagnostika xulosasi: {diagnostic.get('ai_summary', '')}, Zaif sohalar: {', '.join(diagnostic.get('focus_areas', []))}]\n"

    for msg in history[-8:]:  # Oxirgi 8 ta xabar konteksti
        role_label = "Foydalanuvchi" if msg["role"] == "user" else "AI Maslahatchi"
        formatted_context += f"{role_label}: {msg['content']}\n"

    formatted_context += f"Foydalanuvchi: {user_message}\nAI Maslahatchi:"

    try:
        reply = await _generate_content_robust(
            contents=formatted_context,
            system_instruction=AI_CHAT_SYSTEM_PROMPT,
            max_output_tokens=600,
        )
        return reply
    except Exception:
        logger.exception("AI chat xatoligi")
        return (
            "Hozirda AI xizmatida kichik uzilish bo'lmoqda. Iltimos, chuqur nafas oling va bir necha daqiqadan so'ng qayta yozing. "
            f"Zarur bo'lsa, mutaxassisimiz bilan bog'lanishingiz mumkin: {CLINIC_CONTACT} 🌿"
        )


# -------------------------------------------------------------
# 4. TEZKOR SOS / ANTI-STRESS YORDAMI
# -------------------------------------------------------------

SOS_SYSTEM_PROMPT = f"""Sen "SOKIN QALB" markazining tezkor psixologik yordam (SOS) moduli hisoblanasan.
Foydalanuvchi hozir o'tkir stress, vahima (panika), kuchli xavotir, uyqusizlik yoki g'azab holatida turibdi.

VAZIFANG:
Aynan hozir, shu soniyada foydalanuvchini 1 daqiqa ichida tinchlantiruvchi, aniq qadam-baqadam ko'rsatma (mashq) berish:
- Bosqichma-bosqich (1, 2, 3) formatda
- Nafas olish texnikasi (masalan: 4-4-6 yoki 4-7-8)
- Tana va diqqatni yerga ulash (Grounding - masalan: atrofingizdagi 3 ta narsaga qarang...)
- Mutlaqo xotirjam, muloyim va ishonchli ohangda
- Faqat o'zbek tilida (lotin)."""


async def sos_emergency_relief(category: str, user_description: Optional[str] = None) -> str:
    """Foydalanuvchining holatiga mos tezkor tinchlantirish mashqi."""
    prompt_input = f"Holat toifasi: {category}\n"
    if user_description:
        prompt_input += f"Foydalanuvchi aytgan holat: \"{user_description}\"\n"

    try:
        reply = await _generate_content_robust(
            contents=prompt_input,
            system_instruction=SOS_SYSTEM_PROMPT,
            max_output_tokens=500,
        )
        return reply
    except Exception:
        logger.exception("SOS AI xatoligi")
        return (
            "🌿 <b>1 daqiqalik tezkor tinchlanish mashqi:</b>\n\n"
            "1. <b>Qulay o'tiring</b> va oyog'ingiz polga to'liq tegib turganini his qiling.\n"
            "2. <b>Nafas oling:</b> Burun orqali 4 soniya sekin chuqur nafas oling.\n"
            "3. <b>Ushlab turing:</b> Nafasni 4 soniya ichingizda ushlang.\n"
            "4. <b>Chiqaring:</b> Og'iz orqali 6 soniya davomida sekin puflab chiqaring.\n"
            "5. Buni 4 marta takrorlang. Siz xavfsizsiz, bu tuyg'u o'tib ketadi 💙"
        )


ADAPTIVE_CHECKIN_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt "{FOUNDER_NAME}"ning shaxsiy yordamchisisan. \
Sen foydalanuvchi bilan xuddi haqiqiy tirik inson yozayotgandek iliq, samimiy va professional tilda muloqot qilasan.

VAZIFANG:
Foydalanuvchidan quruq va bir xil savollar ("Kayfiyatingiz 1 dan 10 gacha necha?", "Stress necha?") so'ramasdan, \
har kuni turlicha, hayotiy, samimiy va psixologik qiziqarli KUNLIK KUZATUV (Check-in) savollarini berish.

QOIDALAR:
1. Birinchi savol: Bugungi kun qanday o'tgani, tanadagi umumiy his, kutilmagan vaziyatlar yoki ertalabdan kechgacha bo'lgan energiya haqida (4 ta qisqa, 4-6 so'zlik variantlar bilan).
2. Ikkinchi savol: Foydalanuvchining birinchi javobiga asoslanib, bugun unga yordam bergan narsa yoki aksincha qiynagan holat haqida nozik savol.
3. 2 ta savol-javobdan so'ng ("is_finished": true):
   Foydalanuvchining javoblarini tahlil qilib, O'ZING MUTAXASSIS SIFATIDA:
   - "mood_score" (1-10) — umumiy kayfiyat va qoniqish
   - "stress_score" (1-10) — stress va ichki taranglik
   - "achievements" — bugungi kunda erishilgan ijobiy yutuq yoki yengillik
   - "struggles" — bugungi qiynagan qiyinchilik yoki kamchilik
   - "ai_feedback" — bugungi holat bo'yicha 2-3 jumlalik individual iliq psixologik maslahat va dalda.

FORMAT (JSON):
Agar davom etayotgan bo'lsa ("is_finished": false):
{{
  "is_finished": false,
  "step": 1,
  "question": "Bugungi kuningiz asosan qanday o'tdi va tanangizda nimalarni ko'proq his qildingiz?",
  "options": [
    "Sokin va reja bo'yicha",
    "Asabiylashish va shoshqaloqlik",
    "Charchoq va quvvatsizlik",
    "Kutilmagan xursandchiliklar"
  ]
}}

Agar yakunlangan bo'lsa ("is_finished": true):
{{
  "is_finished": true,
  "mood_score": 7,
  "stress_score": 4,
  "achievements": "Ishdagi taranglikka qaramay xotirjamlikni saqlay oldi",
  "struggles": "Kechki paytda yelka mushaklarida charchoq",
  "ai_feedback": "Bugun siz juda yaxshi chidamlilik ko'rsatdingiz. Kechki uyqudan oldin 3 daqiqalik chuqur nafas mashqi orqali tanangizdagi ortiqcha yukni bo'shating 🌿"
}}
"""


async def generate_adaptive_daily_checkin_step(
    history: list[dict],
    user: dict,
    step_count: int = 0,
) -> dict:
    """Kunlik kuzatuv uchun har safar yangi, turlicha savollar va AI avtomatik baholashi."""
    content_lines = [
        f"Foydalanuvchi: {user.get('full_name', 'Foydalanuvchi')}, Kurs kuni: {user.get('course_day', 1)}-kun",
        f"Kuzatuv qadami: {step_count + 1}-savol.",
    ]
    if history:
        content_lines.append("\nHozirgi berilgan javoblar:")
        for idx, item in enumerate(history, 1):
            content_lines.append(f"{idx}-savol: {item.get('question', '')}\nJavob: {item.get('answer', '')}")

    if step_count >= 2:
        content_lines.append(
            "\nFoydalanuvchi 2 ta savolga javob berdi. "
            "'is_finished': true qilib mood_score, stress_score, achievements, struggles va ai_feedback ber."
        )
    else:
        content_lines.append(
            "\nFoydalanuvchiga qiziqarli, samimiy kunlik savol va 4 ta qisqa variant ber ('is_finished': false)."
        )

    try:
        raw_text = await _generate_content_robust(
            contents="\n".join(content_lines),
            system_instruction=ADAPTIVE_CHECKIN_PROMPT,
            max_output_tokens=700,
            response_mime_type="application/json",
            timeout_seconds=20.0,
        )
        data = _parse_json_safely(raw_text)
        if isinstance(data, dict) and ("question" in data or "mood_score" in data):
            return data
    except Exception:
        logger.exception("Dinamik kunlik checkin generatsiyasida xatolik")

    if step_count == 0:
        return {
            "is_finished": False,
            "step": 1,
            "question": "Bugungi kuningiz qanday o'tdi va o'zingizni ko'proq qanday his qildingiz?",
            "options": [
                "Xotirjam va yengil",
                "Ish bilan band va charchagan",
                "Asabiylashish va xavotir",
                "Kutilmagan quvonchli lahzalar",
            ],
        }
    elif step_count == 1:
        return {
            "is_finished": False,
            "step": 2,
            "question": "Bugun sizga eng ko'p kuch bergan yoki aksincha qiynagan asosiy holat nima bo'ldi?",
            "options": [
                "Sokin mashqlar yordam berdi",
                "Rejalashtirilgan ishlarim bitdi",
                "Ichki salbiy fikrlar qiynadi",
                "Vaqt yetishmasligi va shoshilish",
            ],
        }
    else:
        return {
            "is_finished": True,
            "mood_score": 7,
            "stress_score": 4,
            "achievements": "Kun davomida xotirjamlikka intilish bo'ldi",
            "struggles": "Kechki paytda yengil charchoq",
            "ai_feedback": "Bugungi kuningiz barqaror o'tdi. Kechqurun o'zingizga 5 daqiqa vaqt ajratib, chuqur sokin nafas mashqini bajaring 🌿",
        }


# -------------------------------------------------------------
# 5. KUNLIK, HAFTALIK VA OYLIK PROGRESS TAHLILLARI
# -------------------------------------------------------------

WEEKLY_REVIEW_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt {FOUNDER_NAME}ning shaxsiy yordamchisisan.
Foydalanuvchining so'nggi 7 kunlik kuzatuvlari (kayfiyat, stress, erishilgan yutuqlar va duch kelingan kamchiliklar) berilgan.

Vazifang:
Haftalik o'zgarishlarni chuqur va chiroyli tahlil qilib berish:
1. 🏆 <b>Haftalik yutuqlar va ijobiy o'zgarishlar:</b> Foydalanuvchi nimalarga erishdi va nimalarda yengillik sezdi.
2. ⚠️ <b>E'tibor qaratilishi lozim bo'lgan kamchiliklar:</b> Qaysi jihatlar (masalan: uyqu, stress yoki hislarni yutish) ustida ko'proq ishlash kerak.
3. 💡 <b>Keyingi haftaga 2 ta aniq psixologik tavsiya.</b>
Format: Telegram HTML (emojilar bilan, 4-6 jumla, samimiy va professional). O'zbek tilida."""


async def generate_weekly_progress_review(user: dict, checkins: list[dict], baseline_diag: Optional[dict]) -> str:
    """7 kunlik haftalik yutuq va kamchiliklar tahlili."""
    lines = [f"Foydalanuvchi: {user.get('full_name', '')}, Kurs kuni: {user.get('course_day', 0)}"]
    if baseline_diag:
        lines.append(f"Dastlabki holat xulosasi: {baseline_diag.get('ai_summary', '')}")
    for c in checkins:
        ach = f", Yutuq: {c.get('achievements')}" if c.get("achievements") else ""
        strg = f", Qiyinchilik: {c.get('struggles')}" if c.get("struggles") else ""
        lines.append(f"- {c['checkin_date']}: kayfiyat {c['mood_score']}/10, stress {c['stress_score']}/10{ach}{strg}")

    try:
        reply = await _generate_content_robust(
            contents="\n".join(lines),
            system_instruction=WEEKLY_REVIEW_PROMPT,
            max_output_tokens=600,
        )
        return reply
    except Exception:
        logger.exception("Haftalik progress tahlil xatoligi")
        return (
            "So'nggi 7 kunlik kuzatuvlaringiz sizda o'z-o'zingizni anglash va xotirjamlikni "
            "tiklash sari ijobiy intilish borligini ko'rsatmoqda. Kunlik mashqlarni davom ettiring! 🌿"
        )


MONTHLY_REVIEW_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt {FOUNDER_NAME}ning shaxsiy yordamchisisan.
Foydalanuvchining botga ilk qo'shilgandagi DASTLABKI HOLATI (Baseline diagnostikasi) hamda oxirgi 30 kunlik \
dinamikasi (o'rtacha kayfiyat, stress, yutuqlar va qiyinchiliklar tarixi) berilgan.

Vazifang:
Katta oylik transformatsion tahlil tayyorlash:
1. 📈 <b>Boshlang'ich holat vs Hozirgi natija:</b> Foydalanuvchi botga kelganidagi muammolar (masalan: boshlang'ich xavotir, uyqu, tana tarangligi) bilan bugungi holati solishtiriladi.
2. 🌟 <b>Erishilgan asosiy yutuqlar:</b> Qancha masofa bosib o'tildi, qaysi ijobiy odatlar shakllandi.
3. 🎯 <b>Keyingi bosqich maqsadlari:</b> Qaysi kamchiliklarni bartaraf etish ustida ishlash tavsiya etiladi.
Format: Telegram HTML, juda ilhomlantiruvchi, professional va chiroyli tartibda. O'zbek tilida."""


async def generate_monthly_progress_review(user: dict, checkins: list[dict], baseline_diag: Optional[dict]) -> str:
    """30 kunlik oylik katta dinamika tahlili (Boshlang'ich holat bilan solishtirish)."""
    lines = [f"Foydalanuvchi: {user.get('full_name', '')}, Botda: {user.get('course_day', 0)} kundan beri"]
    if baseline_diag:
        lines.append(f"Dastlabki diagnostika natijasi: {baseline_diag.get('ai_summary', '')}")
        lines.append(f"Boshlang'ich zaif nuqtalar: {', '.join(baseline_diag.get('focus_areas', []))}")
    if checkins:
        avg_m = sum(c["mood_score"] for c in checkins) / len(checkins)
        avg_s = sum(c["stress_score"] for c in checkins) / len(checkins)
        lines.append(f"30 kunlik jami kuzatuvlar soni: {len(checkins)}")
        lines.append(f"O'rtacha kayfiyat: {avg_m:.1f}/10, O'rtacha stress: {avg_s:.1f}/10")
        lines.append("Oxirgi kuzatuvlardan namunalar:")
        for c in checkins[-10:]:
            ach = f", Yutuq: {c.get('achievements')}" if c.get("achievements") else ""
            lines.append(f"- {c['checkin_date']}: kayfiyat {c['mood_score']}, stress {c['stress_score']}{ach}")

    try:
        reply = await _generate_content_robust(
            contents="\n".join(lines),
            system_instruction=MONTHLY_REVIEW_PROMPT,
            max_output_tokens=700,
        )
        return reply
    except Exception:
        logger.exception("Oylik progress tahlil xatoligi")
        return (
            "Sizning oylik dinamikangizda ichki barqarorlik va ongni boshqarish bo'yicha "
            "katta ijobiy o'zgarishlar kuzatilmoqda. Sabr va muntazamlik bilan davom eting! 🌿"
        )




ADAPTIVE_FOUR_PILLARS_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt "{FOUNDER_NAME}"ning shaxsiy yordamchisisan. \
Sen foydalanuvchi bilan xuddi haqiqiy tirik psixologik maslahatchi yozayotgandek iliq, nozik, samimiy va professional muloqot qilasan.

VAZIFANG:
Foydalanuvchining 4 ta asosiy hayotiy sohasini HAR BIRIGA AYNAN 5 TADAN CHUQUR SAVOL BERIB (Jami 20 ta savol orqali) \
uning haqiqiy imkoniyatlarini, o'zgarishlarini, o'sish dinamikasini va to'siqlarini TO'LIQ ANIKLASH.

4 TA SOHA VA 5 TADAN SAVOLLAR STRUKTURASI (JAMI 20 TA SAVOL):
1. 💰 1-SOHA: Moliyaviy Holat va Pul Psixologiyasi (1-savoldan 5-savolgacha):
   - 1/5: Xarid qilishdagi ichki hislar (xotirjamlik yoki siqilish, pul sarflashdagi erkinlik).
   - 2/5: Daromad va kelajakdagi moddiy xavfsizlikka bo'lgan ichki ishonch.
   - 3/5: O'ziga pul sarflashdagi munosabat (zavq yoki aybdorlik hissi).
   - 4/5: Kutilmagan xarajatlar va qarzlar oldidagi hissiy reaksiyalar.
   - 5/5: Daromadni oshirishdagi ichki to'siqlar va moliyaviy imkoniyatlar.

2. 🧘 2-SOHA: Ruhiy va Emotsional Holat (6-savoldan 10-savolgacha):
   - 1/5: Xatoga yo'l qo'yganda ichki tanqidchining ovozi va o'zini kechirish.
   - 2/5: Boshqalarning tanqidi oldida o'z qadrini bilish va ichki mustahkamlik.
   - 3/5: Kechki xayollar, overthinking (ortiqcha o'ylov) va emotsional yuk.
   - 4/5: Stressli vaziyatlarda his-tuyg'ularni boshqarish va chidamlilik.
   - 5/5: Ichki xotirjamlik, minnatdorlik va ruhiy quvvat imkoniyatlari.

3. 🏃 3-SOHA: Jismoniy Salomatlik va Quvvat (11-savoldan 15-savolgacha):
   - 1/5: Ertalabki uyg'onishdagi energiya, tetiklik va quvvat darajasi.
   - 2/5: Uyqu sifati, chuqurligi va uyquga to'yish holati.
   - 3/5: Tanadagi psixosomatik qisilishlar (bo'yin, yelka, bosh og'rig'i, nafas qisishi).
   - 4/5: Kun davomidagi jismoniy charchoq va asab tizimi barqarorligi.
   - 5/5: Tana bilan aloqa, sog'lom turmush tarzi va biologik imkoniyatlar.

4. 👥 4-SOHA: Munosabatlar va Shaxsiy Chegaralar (16-savoldan 20-savolgacha):
   - 1/5: Oila va yaqinlar bilan muloqotdagi samimiyat va tushunish darajasi.
   - 2/5: His-tuyg'ularni ochiq ifodalash yoki ichga yutib jim turish.
   - 3/5: Shaxsiy chegaralar va atrofdagilarga "Yo'q" deya olish qobiliyati.
   - 4/5: Xafagarchilik, gina-kudurat va kechira olish imkoniyatlari.
   - 5/5: Yaqinlar tomonidan qo'llab-quvvatlanish va munosabatlardagi uyg'unlik.

QAT'IY QOIDALAR:
1. FOYDALANUVCHINING O'Z SO'ZLARI BILAN YOZGAN MATNLARINI («✍️ O'zim yozib qoldiraman») CHUQUR TAHLILGA KIRIT:
   - Agar foydalanuvchi matn yozgan bo'lsa, keyingi savolda uning aytgan og'riqli yoki ijobiy so'zlarini inobatga ol!
2. SAVOLLARNING TAKRORLANISHINI 100% OLDINI OL:
   - Har bir yangi savol foydalanuvchining oldingi javobidan kelib chiqqan yangi qirra bo'lsin.
3. HAQQONIY, REAL BAHOLASH (FOYDALANUVCHI JAVOBIGA MOS):
   - Agar foydalanuvchi ijobiy javob bergan bo'lsa: 9-10/10 ball qo'y va uning imkoniyatlarini yuqori bahola!
   - Agar qiyinchilik yoki salbiy holatlarni aytgan bo'lsa: 2-5/10 ball qo'y va to'siqlarni aniq ko'rsat.
4. VARIANTLAR BOYLIGI: Har bir savolda kamida 4-5 ta qisqa, lo'nda variantlar bo'lsin (🟢 Ijobiy, 🔴 Salbiy, 🟡 O'rtacha, 🟣 Emotsional).
5. 20-SAVOLDAN SO'NG ("is_finished": true): Har bir soha bo'yicha ALOHIDA-ALOHIDA (imkoniyatlar, o'zgarishlar, to'siqlar) bo'yicha kamida 3-4 jumlalik mukammal tahlil chiqar.

FORMAT (JSON):
Agar 1 dan 19 gacha bo'lgan savollarda bo'lsa ("is_finished": false):
{{
  "is_finished": false,
  "step": 2,
  "question": "Foydalanuvchining javobidan kelib chiqqan yangi, takrorlanmas nozik savol...",
  "options": [
    "🟢 Ijobiy qisqa variant (4-6 so'z)",
    "🔴 Salbiy qisqa variant (4-6 so'z)",
    "🟡 O'rtacha qisqa variant (4-6 so'z)",
    "🟣 Emotsional qisqa variant (4-6 so'z)"
  ]
}}

Agar 20-savol yakunlanib, to'liq tahlil vaqti kelsa ("is_finished": true):
{{
  "is_finished": true,
  "financial_score": 9,
  "mental_score": 8,
  "physical_score": 9,
  "relationship_score": 9,
  "financial_analysis": "Moliyaviy soha (5 ta savol tahlili): Foydalanuvchining pulga nisbatan imkoniyatlari, o'zgarishlari va to'siqlari haqida 3-4 gaplik chuqur xulosa...",
  "mental_analysis": "Ruhiy & Emotsional soha (5 ta savol tahlili): Ichki xotirjamlik, o'ziga ishonch va emotsional imkoniyatlar haqida 3-4 gaplik chuqur xulosa...",
  "physical_analysis": "Jismoniy soha (5 ta savol tahlili): Tana quvvati, uyqu, psixosomatika va energiya imkoniyatlari haqida 3-4 gaplik chuqur xulosa...",
  "relationship_analysis": "Munosabatlar sohasi (5 ta savol tahlili): Oila, shaxsiy chegaralar va muloqot imkoniyatlari haqida 3-4 gaplik chuqur xulosa...",
  "overall_critique": "4 ta sohaning sintezi va foydalanuvchining real o'zgarishlari bo'yicha Furqat Bag'ibekov yordamchisi xulosasi...",
  "roadmap_to_10": [
    "💰 Moliya: Imkoniyatlarni 10/10 ga chiqarish bo'yicha 1-amaliy qadam",
    "🧘 Ruhiyat: Emotsional barqarorlikni 10/10 ga chiqarish bo'yicha 2-amaliy qadam",
    "🏃 Jismoniy: Tana quvvatini 10/10 ga chiqarish bo'yicha 3-amaliy qadam",
    "👥 Munosabatlar: Sog'lom chegaralarni 10/10 ga chiqarish bo'yicha 4-amaliy qadam"
  ]
}}
"""


async def generate_adaptive_four_pillars_step(
    history: list[dict],
    user: dict,
    diagnostic: Optional[dict] = None,
    checkins: Optional[list[dict]] = None,
    step_count: int = 0,
) -> dict:
    """Foydalanuvchining javoblariga qarab 4 ta sohaga 5 tadan (jami 20 ta) chuqur savol berish yoki 4 ustun tahlilini chiqarish."""
    # Qaysi soha va nechanchi savolligi
    if step_count < 5:
        pillar_name = f"💰 1-SOHA: MOLIYAVIY HOLAT ({step_count + 1}/5-savol | Jami {step_count + 1}/20)"
        pillar_focus = "Moliyaviy psixologiya va pul imkoniyatlari"
    elif step_count < 10:
        pillar_name = f"🧘 2-SOHA: RUHIYAT VA EMOTSIYALAR ({step_count - 4}/5-savol | Jami {step_count + 1}/20)"
        pillar_focus = "Ruhiy va emotsional barqarorlik, o'ziga ishonch"
    elif step_count < 15:
        pillar_name = f"🏃 3-SOHA: JISMONIY SALOMATLIK ({step_count - 9}/5-savol | Jami {step_count + 1}/20)"
        pillar_focus = "Tana quvvati, uyqu va psixosomatika"
    else:
        pillar_name = f"👥 4-SOHA: MUNOSABATLAR VA CHEGARALAR ({step_count - 14}/5-savol | Jami {step_count + 1}/20)"
        pillar_focus = "Munosabatlar, oila va shaxsiy chegaralar"

    content_lines = [
        f"Foydalanuvchi: {user.get('full_name', 'Foydalanuvchi')}, Botdagi faol davri: {user.get('course_day', 1)}-kun",
        f"Hozirgi qadam: {pillar_name}",
    ]
    if diagnostic:
        content_lines.append(f"Dastlabki diagnostika natijasi: {diagnostic.get('ai_summary', '')}")
        focus_val = diagnostic.get('focus_areas', [])
        focus_str = ", ".join(focus_val) if isinstance(focus_val, list) else str(focus_val)
        content_lines.append(f"Zaif nuqtalar: {focus_str}")

    if checkins:
        content_lines.append("Oxirgi kunlik qaydlar:")
        for c in checkins[-5:]:
            ach = f", Yutuq: {c.get('achievements')}" if c.get("achievements") else ""
            strg = f", Kamchilik: {c.get('struggles')}" if c.get("struggles") else ""
            content_lines.append(f"- {c['checkin_date']}: kayfiyat {c['mood_score']}/10, stress {c['stress_score']}/10{ach}{strg}")

    if history:
        content_lines.append("\nHozirgi so'rovnomada BERILGAN BARCHA SAVOLLAR VA JAVOBLAR (Bularni qayta takrorlama, foydalanuvchining o'z so'zlarini inobatga ol):")
        for idx, item in enumerate(history, 1):
            content_lines.append(f"{idx}-savol: {item.get('question', '')}\nJavob: {item.get('answer', '')}")

    if step_count >= 20:
        content_lines.append(
            "\nFoydalanuvchi 4 ta sohaning har biriga 5 tadan (jami 20 ta) savolga to'liq javob berdi. "
            "Barcha berilgan javoblarni (ayniqsa, o'zi yozgan matnlarini) chuqur tahlil qil. "
            "DIQQAT: Agar javoblar asosan ijobiy bo'lsa, ballarni 9-10/10 qilib qo'y va imkoniyatlarini yuksak bahola! "
            "Agar salbiy bo'lsa, mos pastroq ball qo'y. 'is_finished': true qilib 4 ta sohaning alohida tahlillarini qaytar."
        )
    else:
        content_lines.append(
            f"\nOldingi berilgan savollarni mutlaqo TAKRORLAMAY, foydalanuvchining so'nggi javobiga tayanib, "
            f"keyingi savolni aynan '{pillar_focus}' yo'nalishi bo'yicha tuz. "
            "Kamida 4-5 ta turli xil (ijobiy, salbiy, vaziyatli) qisqa variantlarni ber ('is_finished': false)."
        )

    try:
        raw_text = await _generate_content_robust(
            contents="\n".join(content_lines),
            system_instruction=ADAPTIVE_FOUR_PILLARS_PROMPT,
            max_output_tokens=1500,
            response_mime_type="application/json",
            timeout_seconds=30.0,
        )
        data = _parse_json_safely(raw_text)
        if isinstance(data, dict) and ("question" in data or "financial_score" in data):
            return data
    except Exception:
        logger.exception("Dinamik 4 ustun qadami generatsiyasida xatolik")

    # Smart Sentiment & Answers-based Dynamic Fallback (20 ta savol uchun)
    pos_keywords = ["xotirjam", "erkin", "mamnun", "ishonch", "zavq", "qo'llab", "tetik", "tiniq", "kelishamiz", "ha", "yaxshi", "barqaror", "to'liq", "sevimli", "mustahkam"]
    neg_keywords = ["xavotir", "siqilish", "qo'rquv", "aybdorlik", "yetishmovchilik", "ezilaman", "asabiylashaman", "tushkunlik", "charchagan", "og'irlik", "jahl", "rad etolmay", "yolg'iz", "og'riq"]

    answers_str = " ".join([h.get("answer", "").lower() for h in history])
    pos_matches = sum(1 for kw in pos_keywords if kw in answers_str)
    neg_matches = sum(1 for kw in neg_keywords if kw in answers_str)

    if pos_matches >= neg_matches:
        base_score = min(10, 8 + (pos_matches - neg_matches) // 3)
        fin_s = base_score
        men_s = base_score
        phys_s = max(8, base_score)
        rel_s = min(10, base_score + 1)
        fin_desc = "Moliyaviy soha (5 ta savol tahlili): Pulga nisbatan xotirjamlik, erkinlik va yuqori boshqaruv imkoniyatlari mavjud. Pul sarflashdagi aybdorlik hissi bartaraf etilgan."
        men_desc = "Ruhiy & Emotsional soha (5 ta savol tahlili): Ichki ishonch, o'z qadrini bilish va hissiy barqarorlik yuqori darajada. Qiyinchiliklar oldida ichki xotirjamlik saqlanadi."
        phys_desc = "Jismoniy soha (5 ta savol tahlili): Tana quvvati, uyqu sifati va ertalabki energiya a'lo darajada. Asab tizimi va tana o'rtasida sog'lom garmoniya shakllangan."
        rel_desc = "Munosabatlar sohasi (5 ta savol tahlili): Shaxsiy chegaralar mustahkam, yaqinlar bilan muloqotda samimiyat va erkin fikr bildirish ko'nikmasi to'liq rivojlangan."
        critique_desc = "Sizning barcha 4 ta sohangizda (20 ta savol natijasida) yuqori darajadagi onglilik va o'sish dinamikasi aniqlandi. Ushbu ajoyib imkoniyatlarni doimiy intizom bilan mustahkamlang!"
        roadmap = [
            "💰 Moliya: Moliyaviy rejalarni kengaytirish va yangi daromad marralarini belgilash",
            "🧘 Ruhiyat: Mindfulness va minnatdorlik amaliyotlarini davom ettirish",
            "🏃 Jismoniy: Quvvatni bir maromda ushlash uchun sevimli mashg'ulotlar",
            "👥 Munosabatlar: Yaqinlar bilan chuqur va mazmunli muloqotlarni rivojlantirish",
        ]
    else:
        fin_s = 5
        men_s = 5
        phys_s = 5
        rel_s = 6
        fin_desc = "Moliyaviy soha (5 ta savol tahlili): Kutilmagan to'lovlar paytida xavotir va tejamkorlik qo'rquvi kuzatilmoqda. Pul sarflashdagi aybdorlikni yechish talab etiladi."
        men_desc = "Ruhiy & Emotsional soha (5 ta savol tahlili): Ichki tanqidchining ovozi va kechki overthinking ba'zan quvvatingizni sarflamoqda. O'z qadrini oshirish zarur."
        phys_desc = "Jismoniy soha (5 ta savol tahlili): Tana energiyasida charchoq va uyqu sifatini yaxshilash ehtiyoji seziladi. Somatik relaksatsiya mashqlari lozim."
        rel_desc = "Munosabatlar sohasi (5 ta savol tahlili): Shaxsiy chegaralarni himoya qilish va 'yo'q' deya olish ko'nikmasini rivojlantirish zarur."
        critique_desc = "20 ta savol tahlili sizda o'zgarishlar uchun katta imkoniyat borligini ko'rsatdi. Asosiy e'tiborni his-tuyg'ularni ichga yutmaslikka qarating."
        roadmap = [
            "💰 Moliya: Oylik xarajatlarni aniq rejalashtirish va xarid xavotirini kamaytirish",
            "🧘 Ruhiyat: Ichki tanqidchini to'xtatish va kundalik 5 daqiqa nafas mashqi",
            "🏃 Jismoniy: Sifatli uyqu tartibini tiklash va tana muskullarini bo'shatish",
            "👥 Munosabatlar: Shaxsiy chegaralarni belgilash va hislarni ochiq ifodalash",
        ]

    # 20 ta boy va takrorlanmas savollar bazasi
    fallback_20_questions = [
        # 1-Soha: Moliya (1-5)
        ("💰 1-SOHA: MOLIYAVIY HOLAT (1/5 | Jami 1/20)\n\nKutilmagan zaruriy xarajat yoki to'lov qilishingiz kerak bo'lganda, ichingizda qanday birinchi his paydo bo'ladi?", [
            "Xotirjam va erkin to'layman", "Ichki qisilish va xavotir", "Ertangi kun haqida o'ylov", "Yetmay qolish qo'rquvi", "Pul sarflashda aybdorlik hissi"
        ]),
        ("💰 1-SOHA: MOLIYAVIY HOLAT (2/5 | Jami 2/20)\n\nOylik daromadingiz va kelajakdagi moddiy xavfsizligingiz haqida o'ylaganingizda, nimalarni ko'proq sezasiz?", [
            "O'z daromadimdan to'liq mamnunman", "Daromadni oshirishga ishonch bor", "Doimiy yetishmovchilik va xavotir", "Ertangi kunga noaniqlik va qo'rquv", "Qattiq mehnat qilaman, lekin samarasiz"
        ]),
        ("💰 1-SOHA: MOLIYAVIY HOLAT (3/5 | Jami 3/20)\n\nO'zingiz orzu qilgan qimmatroq narsani sotib olish yoki o'zingizga pul sarflash jarayoni sizda qanday kechadi?", [
            "O'zimga zavq bilan sarflayman", "Isrofgarchilik deb vijdonim qiynaladi", "Faqat boshqalarga sarflashga moyilman", "Qancha pulim bo'lsa ham siqilaman", "Reja asosida tejab xarid qilaman"
        ]),
        ("💰 1-SOHA: MOLIYAVIY HOLAT (4/5 | Jami 4/20)\n\nQarz berish yoki qarz olish vaziyatlariga tushganingizda, o'zingizni qanday his qilasiz?", [
            "Moliyaviy chegaram mustahkam", "Rad etolmay qarz berib siqilaman", "Qarz olishdan kuchli qo'rqaman", "Qarzlar tufayli doimiy tarangman", "Munosabatlarni puldan ustun qo'yaman"
        ]),
        ("💰 1-SOHA: MOLIYAVIY HOLAT (5/5 | Jami 5/20)\n\nMoliyaviy imkoniyatlaringizni kengaytirish va yangi daromad darajasiga chiqishga nima ko'proq to'sqinlik qilmoqda?", [
            "To'siq sezmayman, o'syapman", "Tavakkal qilishdan qo'rquv", "O'z bilim va kuchimga ishonchsizlik", "Vaqt va quvvat yetishmasligi", "Eski moliyaviy muvaffaqiyatsizliklar"
        ]),

        # 2-Soha: Ruhiyat va Emotsiyalar (6-10)
        ("🧘 2-SOHA: RUHIYAT VA EMOTSIYALAR (1/5 | Jami 6/20)\n\nXatoga yo'l qo'yganingizda yoki ishlar rejadagidek ketmaganda, ichki ovozingiz sizga qanday munosabatda bo'ladi?", [
            "O'zimni qo'llab, to'g'ri xulosa qilaman", "O'zimni ayblab, uzoq ezilaman", "Boshqalarga nisbatan asabiylashaman", "Tushkunlikka tushib, qo'lim ishga bormaydi", "Barchasini ichimga yutib, yashiraman"
        ]),
        ("🧘 2-SOHA: RUHIYAT VA EMOTSIYALAR (2/5 | Jami 7/20)\n\nBoshqalarning siz haqingizdagi fikri yoki tanqidi sizning ichki xotirjamligingizga qanday ta'sir qiladi?", [
            "O'z qadrimni bilaman, ta'sirlanmayman", "Kunlab shu gaplarni o'ylab siqilaman", "Tezda o'zimga ishonchim so'nadi", "Hamma narsani mukammal qilishga urinaman", "Noxush vaziyatlardan qochishni tanlayman"
        ]),
        ("🧘 2-SOHA: RUHIYAT VA EMOTSIYALAR (3/5 | Jami 8/20)\n\nKechasi yotishdan oldin yoki yolg'iz qolganingizda xayolingizdan ko'proq nimalar o'tadi?", [
            "Ichki xotirjamlik va minnatdorlik", "O'tmishdagi pushaymonliklar", "Kelajak haqidagi hadiksirashlar", "Miyada tinimsiz chalg'ituvchi fikrlar", "Hissiy bo'shliq va tushunarsiz g'amginlik"
        ]),
        ("🧘 2-SOHA: RUHIYAT VA EMOTSIYALAR (4/5 | Jami 9/20)\n\nKuchli stress yoki kutilmagan vaziyat yuz berganda, o'z his-tuyg'ularingizni qanday boshqarasiz?", [
            "Chuqur nafas olib, xotirjam yechim topaman", "Tez vahimaga tushib sarosimada qolaman", "Hissiyotlarimni jilovlay olmay portlayman", "Barchasini ichimga yutib, muzlab qolaman", "Muammodan qochib chalg'ishga urinaman"
        ]),
        ("🧘 2-SOHA: RUHIYAT VA EMOTSIYALAR (5/5 | Jami 10/20)\n\nUmuman olganda, o'zingizni baxtli, xotirjam va ichki uyg'unlikda his qilish darajangiz qanday?", [
            "Hayotimdan to'la baxtiyorman", "Ko'p vaqtim xotirjam o'tadi", "Ichimda doimiy qandaydir kemtiklik bor", "Tushkunlik va xavotir ko'proq", "O'zligimni yo'qotib qo'ygandekman"
        ]),

        # 3-Soha: Jismoniy Salomatlik va Quvvat (11-15)
        ("🏃 3-SOHA: JISMONIY SALOMATLIK (1/5 | Jami 11/20)\n\nErtalab uyg'onganingizda tanangiz va asab tizimingiz holati qanday bo'ladi?", [
            "Tetik, tiniq va kuchga to'la", "Ertalabdan og'ir va charchagan", "Tunda tez-tez uyg'onib chiqaman", "Uyquga to'ymay, quvvatsiz turaman", "Yurak bezovtaligi yoki hayajon bilan"
        ]),
        ("🏃 3-SOHA: JISMONIY SALOMATLIK (2/5 | Jami 12/20)\n\nKechasi uxlashga yotganingizda uyquga ketish jarayoni sizda qanday kechadi?", [
            "5-10 daqiqada chuqur uxlayman", "Miyadagi fikrlar tufayli 1-2 soat qiynalaman", "Tushlarim bezovta va og'ir", "Telefon titkilab kech uxlab qolaman", "Dori yoki maxsus vositalarsiz uxlay olmayman"
        ]),
        ("🏃 3-SOHA: JISMONIY SALOMATLIK (3/5 | Jami 13/20)\n\nAsabiylashganingizda yoki charchaganingizda tanangizning qaysi qismida og'irlik sezasiz?", [
            "Tanada jiddiy og'irlik sezmayman", "Yelka, bo'yin va boshda kuchli qisilish", "Yurak sohasida siqilish va nafas yetmasligi", "Oshqozon va qorin sohasida bezovtalik", "Umumiy quvvatsizlik va holsizlik"
        ]),
        ("🏃 3-SOHA: JISMONIY SALOMATLIK (4/5 | Jami 14/20)\n\nKun davomida energiyangiz va ishchanlik qobiliyatingiz qanday taqsimlanadi?", [
            "Kun bo'yi barqaror va tetikman", "Tushdan keyin kuchli holsizlik bosadi", "Kofe/energetik ichimliklarsiz turolmayman", "Juda tez charchab, asabiy bo'lib qolaman", "Doimiy surunkali charchoqdaman"
        ]),
        ("🏃 3-SOHA: JISMONIY SALOMATLIK (5/5 | Jami 15/20)\n\nO'z tanangizga g'amxo'rlik qilish, jismoniy mashq yoki toza havoda yurish sizda qay darajada yo'lga qo'yilgan?", [
            "Muntazam sport va tana parvarishi bor", "Vaqti-vaqti bilan piyoda yuraman", "Mashq qilishga umuman vaqtim yo'q", "Faqat og'riq paydo bo'lganda eslayman", "Tanaga befarqman, faqat ishlayman"
        ]),

        # 4-Soha: Munosabatlar va Chegaralar (16-20)
        ("👥 4-SOHA: MUNOSABATLAR VA CHEGARALAR (1/5 | Jami 16/20)\n\nYaqinlaringiz bilan kelishmovchilik bo'lganda yoki sizga nohaqlik qilinganda, odatda qanday yo'l tutasiz?", [
            "Xotirjam tushuntirib, chegaramni qo'yaman", "Ichimga yutib, jilmayib turaman", "Tez jahl qilib, qattiq gapirib yuboraman", "O'zimni kamsitilgan va yolg'iz his qilaman", "Barchasini unutish uchun uzoqlashaman"
        ]),
        ("👥 4-SOHA: MUNOSABATLAR VA CHEGARALAR (2/5 | Jami 17/20)\n\nOila va yaqinlaringizga o'z his-tuyg'ularingiz, xursandchilik yoki xafagarchiligingizni ochiq ayta olasizmi?", [
            "Erkin va samimiy ayta olaman", "Qisman, faqat ba'zi narsalarni", "Meni tushunishmaydi deb aytmayman", "Hissiyotlarimni ko'rsatishdan uyalaman", "Hamma dardimni ichimda saqlayman"
        ]),
        ("👥 4-SOHA: MUNOSABATLAR VA CHEGARALAR (3/5 | Jami 18/20)\n\nAtrofdagilar sizdan noqulay narsa so'raganda 'Yo'q' deb rad etish siz uchun qanchalik oson?", [
            "Erkin va muloyim 'yo'q' deya olaman", "Rad etolmay, o'z ziyonimga rozi bo'laman", "Rad etsam, kuchli aybdorlik his qilaman", "Boshqalar xafa bo'lishidan qo'rqaman", "Faqat majburiy holatlarda rad etaman"
        ]),
        ("👥 4-SOHA: MUNOSABATLAR VA CHEGARALAR (4/5 | Jami 19/20)\n\nO'tmishda sizni xafa qilgan insonlarni kechirish va gina-kuduratdan xalos bo'lish sizda qanday kechadi?", [
            "Oson kechirib, ko'nglimni ozod qilaman", "Kechirgandekman, lekin ichimda xotira qolgan", "Yillab unutolmay ezilaman", "Qasos yoki pushaymonlik hissi qiynaydi", "Insonlarga nisbatan ishonchim so'ngan"
        ]),
        ("👥 4-SOHA: MUNOSABATLAR VA CHEGARALAR (5/5 | Jami 20/20)\n\nAtrofdagilardan mehr, qo'llab-quvvatlash va iliqlikni qabul qilish siz uchun qay darajada tabiiy?", [
            "Mehr va yordamni minnatdorlik bilan olaman", "Yordam so'rashga uyalaman, o'zim qilaman", "Hech kimga yuk bo'lmaslikka urinaman", "O'zimni mehrga loyiq deb bilmayman", "Yaqinlarimdan doimiy sovuqlik sezaman"
        ]),
    ]

    if step_count < len(fallback_20_questions):
        q_text, opts = fallback_20_questions[step_count]
        return {
            "is_finished": False,
            "step": step_count + 1,
            "question": q_text,
            "options": opts,
        }

    return {
        "is_finished": True,
        "financial_score": fin_s,
        "mental_score": men_s,
        "physical_score": phys_s,
        "relationship_score": rel_s,
        "financial_analysis": fin_desc,
        "mental_analysis": men_desc,
        "physical_analysis": phys_desc,
        "relationship_analysis": rel_desc,
        "overall_critique": critique_desc,
        "roadmap_to_10": roadmap,
    }


async def generate_four_pillars_ai_analysis(
    user: dict,
    current: dict,
    previous: Optional[dict],
    diagnostic: Optional[dict] = None,
    checkins: Optional[list[dict]] = None,
) -> str:
    """4 ta ustun (Moliya, Ruhiyat, Jismoniy, Munosabatlar) bo'yicha chuqur tanqidiy va real AI tahlili."""
    content_lines = [
        f"Foydalanuvchi: {user.get('full_name', '')}, Botdan foydalanish davri: {user.get('course_day', 1)}-kun",
    ]
    if diagnostic:
        content_lines.append(f"Dastlabki diagnostika xulosasi: {diagnostic.get('ai_summary', '')}")
        content_lines.append(f"Dastlabki zaif nuqtalar: {', '.join(diagnostic.get('focus_areas', []))}")

    if checkins:
        content_lines.append("So'nggi kundalik qaydlar va yutuqlar:")
        for c in checkins[-5:]:
            ach = f", Yutuq: {c.get('achievements')}" if c.get("achievements") else ""
            strg = f", Qiyinchilik: {c.get('struggles')}" if c.get("struggles") else ""
            content_lines.append(f"- {c['checkin_date']}: kayfiyat {c['mood_score']}/10, stress {c['stress_score']}/10{ach}{strg}")

    content_lines.append(
        f"Hozirgi baholar (Bu hafta): Moliya {current.get('financial_score', 5)}/10, "
        f"Ruhiyat {current.get('mental_score', 5)}/10, "
        f"Jismoniy {current.get('physical_score', 5)}/10, "
        f"Munosabatlar {current.get('relationship_score', 5)}/10"
    )
    if previous:
        content_lines.append(
            f"Oldingi baholar (O'tgan hafta): Moliya {previous.get('financial_score', 5)}/10, "
            f"Ruhiyat {previous.get('mental_score', 5)}/10, "
            f"Jismoniy {previous.get('physical_score', 5)}/10, "
            f"Munosabatlar {previous.get('relationship_score', 5)}/10"
        )
    else:
        content_lines.append("Bu foydalanuvchining 1-marta 4 ustun bo'yicha baholanishi.")

    try:
        reply = await _generate_content_robust(
            contents="\n".join(content_lines),
            system_instruction=FOUR_PILLARS_ANALYSIS_PROMPT,
            max_output_tokens=700,
        )
        return reply
    except Exception:
        logger.exception("4 ta ustun AI tahlil xatoligi")
        return (
            "Sizning 4 ta hayotiy ustuningiz bo'yicha o'zgarishlar dinamikasi qayd etildi. "
            "Eng past ball olgan sohangizga kundalik mikro-odatlar orqali e'tibor qarating — "
            "bosqichma-bosqich barcha jabhalarda 10/10 natijaga erishish to'liq imkoningiz bor! 🌿"
        )


# -------------------------------------------------------------
# 6. SHAXSIY KUNLIK AI TOPSHIRIQLAR VA SOATMA-SOAT REJA
# -------------------------------------------------------------

DAILY_TASKS_SYSTEM_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt "{FOUNDER_NAME}"ning shaxsiy yordamchisisan.

VAZIFANG:
Foydalanuvchining psixologik diagnostika natijalari, 4 ta soha (moliya, ruhiyat, salomatlik, munosabatlar) va so'nggi holatidan kelib chiqib, \
bugungi kun uchun SOATMA-SOAT (aniq soatlarga taqsimlangan, 4-5 ta) amaliy, qiziqarli, o'zi bilan birgalikda ("Keling, buni birgalikda qilamiz!") \
bajariladigan, foydalanuvchini zeriktirmaydigan va rohatlanib bajaradigan KUNDALIK TOPSHIRIQLAR JADVALINI tuzish.

Soatlar:
- "07:00" — 🌅 Tongi tetiklik va iliq suv / chuqur nafas
- "09:30" — 🚀 Kunlik asosiy niyat va fokus amaliyoti
- "13:30" — 🧘 Tushlikdan so'ng 3 daqiqalik stressdan uzilish / psixosomatik yengillashish
- "17:00" — 🚶 Tana harakati / energiya yangilash
- "21:30" — 🌙 Sokin uyquga tayyorgarlik va minnatdorlik

FORMAT:
Faqat va faqat quyidagi JSON formatida javob ber:
{{
  "tasks": [
    {{
      "time": "07:00",
      "title": "🌅 1 stakan iliq suv va 4-4-6 minnatdorlik nafasi",
      "desc": "Keling, bugun birgalikda kuningizni tetik boshlaymiz! 1 stakan iliq suv ichib, 3 daqiqa chuqur nafas olamiz.",
      "benefit": "Miyaga kislorod yetkazadi, ertalabki xavotirni 40% pasaytiradi."
    }},
    {{
      "time": "13:30",
      "title": "🧘 3 daqiqalik yelka va tana relaksatsiyasi",
      "desc": "Keling, ozgina tanaffus qilamiz! Yelkalaringizni bo'shashtiring va ko'zingizni yumib, 1 daqiqa jimlikda dam oling.",
      "benefit": "Bo'yin va yelkadagi psixosomatik zo'riqishni yechadi."
    }},
    {{
      "time": "21:30",
      "title": "🌙 Raqamli sukunat va chuqur orom",
      "desc": "Keling, barcha telefonlarni bir chetga qo'yib, bugungi 3 ta yoqimli onni eslab, sokin uyquga ketamiz.",
      "benefit": "Melatonin gormonini oshiradi va to'laqonli chuqur uyquni kafolatlaydi."
    }}
  ]
}}
"""


async def generate_personalized_daily_tasks(
    user: dict,
    diagnostic: Optional[dict] = None,
    recent_checkins: Optional[list[dict]] = None,
) -> list[dict]:
    """Foydalanuvchining ruhiy holatiga moslashtirilgan soatma-soat shaxsiy topshiriqlar jadvalini yaratadi."""
    content = f"Foydalanuvchi: {user.get('full_name', 'Foydalanuvchi')}, Botdagi kuni: {user.get('course_day', 1)}\n"
    if diagnostic:
        content += f"Diagnostika xulosasi: {diagnostic.get('ai_summary', '')}\n"
        focus_val = diagnostic.get('focus_areas', [])
        focus_str = ", ".join(focus_val) if isinstance(focus_val, list) else str(focus_val)
        content += f"Zaif nuqtalar: {focus_str}\n"
    if recent_checkins:
        c = recent_checkins[0]
        content += f"So'nggi holat: Kayfiyat {c.get('mood_score')}/10, Stress {c.get('stress_score')}/10\n"

    try:
        raw_text = await _generate_content_robust(
            contents=content,
            system_instruction=DAILY_TASKS_SYSTEM_PROMPT,
            max_output_tokens=900,
            response_mime_type="application/json",
            timeout_seconds=25.0,
        )
        data = _parse_json_safely(raw_text)
        tasks = data.get("tasks", [])
        if tasks:
            default_hours = ["07:00", "09:30", "13:30", "17:30", "21:30"]
            for i, t in enumerate(tasks):
                if not t.get("time") and not t.get("scheduled_time"):
                    t["time"] = default_hours[i % len(default_hours)]
            return tasks
    except Exception:
        logger.exception("Shaxsiy kunlik topshiriqlar AI generatsiyasida xatolik")

    # Fallback soatma-soat topshiriqlar
    return [
        {
            "time": "07:00",
            "title": "🌅 Ertalabki iliq suv va 4-4-6 nafas amaliyoti",
            "desc": "Keling, bugun tongni birgalikda xotirjam boshlaymiz! 1 stakan iliq suv ichib, 3 daqiqa chuqur nafas oling.",
            "benefit": "Miyani uyg'otadi, qon aylanishini yaxshilaydi va ertalabki xavotirni bartaraf etadi.",
        },
        {
            "time": "13:30",
            "title": "🌿 Kunduzgi 3 daqiqalik tana va ong relaksatsiyasi",
            "desc": "Keling, ishlar orasida 3 daqiqa tanaffus qilamiz! Yelkalaringizni bo'shashtiring va o'zingizga iliq mehr bildiring.",
            "benefit": "Ishdagi zo'riqish va mushak qotishini darhol yengillashtiradi.",
        },
        {
            "time": "17:30",
            "title": "🚶 5 daqiqalik sokin ongli sayr (Mindful pause)",
            "desc": "Keling, toza havoga chiqib yoki deraza oldida atrof go'zalligini baholamasdan tomosha qilamiz.",
            "benefit": "Fikrlarni tozalaydi va kechki charchoqni yo'qotadi.",
        },
        {
            "time": "21:30",
            "title": "🌙 Kechki raqamli sukunat va minnatdorlik",
            "desc": "Keling, gadjetlarni bir chetga qo'yib, bugun yuz bergan 3 ta yaxshi voqeani eslaymiz va xotirjam uxlaymiz.",
            "benefit": "Asab tizimini tinchlantirib, chuqur va shirin uyquga zamin yaratadi.",
        },
    ]


DYNAMIC_MOTIVATION_PROMPT = f"""Sen 12 yillik tajribaga ega psixoterapevt {FOUNDER_NAME}ning shaxsiy yordamchisisan.

VAZIFANG:
Foydalanuvchini ruhlantiruvchi, uning qalbini quvvatlovchi, o'ziga bo'lgan ishonchini oshiruvchi va har qanday tushkunlikni tarqatuvchi \
juda go'zal, jozibali, she'riy-psixologik qisqa motivatsiya xabari (2-3 paragraf) yaratish.

Xabarda:
- Foydalanuvchining orzulari va imkoniyatlari ulkan ekani
- Har bir kichik qadam (orzular tomon bir qadam) katta yutuqlarga olib kelishi
- Tabiat, tog'lar, sokin dengiz va tonggi quyosh manzaralarining estetik ruhi aks etsin.
- Ohang: samimiy, mehrli, ishonch bag'ishlovchi.
- O'zbek tilida (lotin)."""


async def generate_dynamic_motivation(user: dict, completed_task_title: Optional[str] = None) -> str:
    """Foydalanuvchiga fotosurati yoki profiliga mos dinamik, doimiy o'zgaruvchan yangi AI motivatsiyasi."""
    user_name = user.get("full_name", "Qadrdonim")
    content = f"Foydalanuvchi ismi: {user_name}\n"
    if completed_task_title:
        content += f"Yangi bajargan topshirig'i: {completed_task_title}\n"
    content += "Foydalanuvchi uchun mutlaqo yangi, ilhomlantiruvchi va quvvat bag'ishlovchi motivatsiya yoz."

    try:
        reply = await _generate_content_robust(
            contents=content,
            system_instruction=DYNAMIC_MOTIVATION_PROMPT,
            max_output_tokens=500,
        )
        return reply
    except Exception:
        return (
            f"✨ <b>Har bir qadamingiz — buyuk orzularingiz sari ochilgan nurli yo'ldir, {user_name}!</b> 🌿\n\n"
            "Tog'lar qanchalik baland bo'lmasin, ularning cho'qqisiga kichik, ammo to'xtovsiz qadamlar bilan chiqiladi. "
            "Sizning ichki kuchingiz va xotirjamligingiz barcha qiyinchiliklardan ustun. "
            "O'zingizga ishoning, bugun o'zingiz uchun qilgan har bir amalingiz erta uchun eng katta sovg'adir! 💙\n\n"
            f"— {FOUNDER_NAME}"
        )


REMINDER_SYSTEM_PROMPT = f"""Sen "{FOUNDER_NAME}" nomidan "SOKIN QALB" foydalanuvchisiga uning soatlik topshirig'ini \
bajarish bo'yicha "Keling, buni birgalikda qilamiz!" ruhidagi juda samimiy, mehrli, qisqa (2-3 jumla) eslatma yozuvchi AI yordamchisisan.
Faqat o'zbek tilida."""


async def generate_task_reminder_message(
    user_name: str,
    completed: int,
    total: int,
    pending_tasks: list[str],
) -> str:
    """Foydalanuvchiga topshiriqlarni bajarish bo'yicha iliq AI eslatmasi."""
    content = f"Foydalanuvchi: {user_name}\nBajarilgan: {completed}/{total} ta ({int(completed/total*100 if total else 0)}%)\nBajarilmagan vazifalar: {', '.join(pending_tasks)}"
    try:
        reply = await _generate_content_robust(
            contents=content,
            system_instruction=REMINDER_SYSTEM_PROMPT,
            max_output_tokens=300,
        )
        return reply
    except Exception:
        return (
            f"Assalomu alaykum, {user_name}! 🌿 Kun yakunlanmoqda. "
            f"Bugun topshiriqlaringizning {int(completed/total*100 if total else 0)}% qismini bajardingiz. "
            "Keling, qolgan kichik mashqlarni ham bajarib, kuningizni xotirjam yakunlaymiz 💙"
        )


# -------------------------------------------------------------
# 7. ADMIN PANEL UCHUN AI VOSITALARI
# -------------------------------------------------------------

ADMIN_POST_PROMPT = f"""Sen "{FOUNDER_NAME}" (psixoterapevt) nomidan "SOKIN QALB" Telegram kanali va boti uchun \
postlar yozuvchi professional kopirayter va psixologsan.

Admin bergan mavzu yoki g'oya asosida ajoyib, yurakka yetib boruvchi, professional va amaliy Telegram posti yarat.
Post tuzilishi:
- Qiziqarli, diqqatni tortuvchi sarlavha (emojilar bilan)
- Muammoning chuqur psixologik mohiyati (sodda tilda)
- O'quvchi uchun darhol qo'llash mumkin bo'lgan 2-3 ta amaliy maslahat
- Ilhomlantiruvchi xulosa va {FOUNDER_NAME} imzosi.
- Til: jozibali o'zbek tili (lotin)."""


async def admin_generate_post(topic_or_idea: str) -> str:
    """Admin uchun AI orqali tayyor post yaratish."""
    try:
        reply = await _generate_content_robust(
            contents=f"Mavzu / g'oya: {topic_or_idea}",
            system_instruction=ADMIN_POST_PROMPT,
            max_output_tokens=900,
        )
        return reply
    except Exception as e:
        logger.exception("Admin post generatsiyasida xatolik")
        raise e


ADMIN_AUDIENCE_PROMPT = f"""Sen "SOKIN QALB" markazining bosh tahlilchisisan.
Admin uchun bot foydalanuvchilarining umumiy statistikasi berilgan.

Vazifang:
Auditoriyaning umumiy holati, ruhiy salomatlik tendensiyalari va admin (yoki mutaxassis {FOUNDER_NAME}) \
uchun foydali bo'lgan 3 ta strategik tavsiya beruvchi hisobot yozish (2-3 qisqa paragraf). O'zbek tilida."""


async def admin_analyze_audience(stats: dict) -> str:
    """Admin uchun auditoriya psixologik holatini umumlashtirish."""
    content = f"""
Jami foydalanuvchilar: {stats.get('total_users')}
Faol foydalanuvchilar: {stats.get('active_users')}
Diagnostika topshirganlar: {stats.get('diagnosed_users')}
Bugungi check-inlar: {stats.get('today_checkins')}
Xavf belgisi tushganlar soni: {stats.get('risk_cases_count')}
Oxirgi 7 kundagi o'rtacha kayfiyat: {stats.get('avg_mood_7d')}/10
Oxirgi 7 kundagi o'rtacha stress: {stats.get('avg_stress_7d')}/10
"""
    try:
        reply = await _generate_content_robust(
            contents=content,
            system_instruction=ADMIN_AUDIENCE_PROMPT,
            max_output_tokens=600,
        )
        return reply
    except Exception:
        logger.exception("Admin audience analysis xatoligi")
        return "Auditoriya tahlilini yuklashda vaqtinchalik xatolik yuz berdi."
