"""
SOKIN QALB — ma'lumotlar bazasi qatlami (aiosqlite ustida).
Barcha jadvallar shu yerda yaratiladi va CRUD funksiyalari shu yerda joylashgan.
"""
import json
from datetime import datetime, date
from typing import Optional, Any

import aiosqlite

from config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    full_name TEXT,
    username TEXT,
    created_at TEXT NOT NULL,
    diagnostic_done INTEGER NOT NULL DEFAULT 0,
    course_day INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    answers_json TEXT NOT NULL,
    ai_summary TEXT,
    focus_areas_json TEXT,
    course_outline_json TEXT,
    risk_flag INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    checkin_date TEXT NOT NULL,
    mood_score INTEGER,
    stress_score INTEGER,
    achievements TEXT,
    struggles TEXT,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_date TEXT NOT NULL,
    task_text TEXT NOT NULL,
    is_done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS content_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_date TEXT NOT NULL,
    lesson_title TEXT,
    meditation_title TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS four_pillars_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recorded_date TEXT NOT NULL,
    financial_score INTEGER NOT NULL DEFAULT 5,
    mental_score INTEGER NOT NULL DEFAULT 5,
    physical_score INTEGER NOT NULL DEFAULT 5,
    relationship_score INTEGER NOT NULL DEFAULT 5,
    ai_advice TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS unlocked_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_key TEXT NOT NULL,
    unlocked_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'payment',
    UNIQUE(user_id, course_key),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS payment_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_key TEXT NOT NULL,
    amount_uzs INTEGER,
    receipt_file_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    approved_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS course_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_key TEXT NOT NULL,
    lesson_order INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    media_type TEXT NOT NULL DEFAULT 'text',
    media_file_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    experience TEXT NOT NULL,
    avatar_icon TEXT DEFAULT '👨‍⚕️',
    directions_text TEXT,
    methodology_text TEXT,
    achievements_text TEXT,
    photo_file_id TEXT,
    order_num INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dynamic_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_key TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT DEFAULT 'course',
    author TEXT,
    price TEXT,
    duration TEXT,
    target TEXT,
    features_text TEXT,
    description TEXT,
    photo_file_id TEXT,
    order_num INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS referral_gifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gift_key TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    required_friends INTEGER NOT NULL,
    description TEXT,
    reward_type TEXT DEFAULT 'course',
    reward_content TEXT,
    photo_file_id TEXT,
    order_num INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # SQLite yuqori unumdorlik va qulfga qarshi rejim (WAL + 10s Timeout)
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA busy_timeout = 10000;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        await db.execute("PRAGMA cache_size = -64000;")
        
        await db.executescript(SCHEMA)
        # Ustunlar migratsiyasi (agar mavjud bo'lmasa)
        try:
            await db.execute("ALTER TABLE checkins ADD COLUMN achievements TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE checkins ADD COLUMN struggles TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN task_title TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN task_desc TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN task_benefit TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN referrals_count INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN photo_file_id TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN scheduled_time TEXT")
        except Exception:
            pass
        try:
            await db.execute("UPDATE tasks SET scheduled_time = '08:00' WHERE scheduled_time IS NULL")
            await db.commit()
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN reminder_sent_count INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
        except Exception:
            pass
            
        # Kurs materiallari bazasini boshlang'ich ma'lumotlar bilan to'ldirish (agar bo'sh bo'lsa)
        cur = await db.execute("SELECT COUNT(*) FROM course_materials")
        mat_count = (await cur.fetchone())[0]
        if mat_count == 0:
            now_iso = datetime.utcnow().isoformat()
            default_materials = [
                # 1$ Kurs: 1 ta video/audio
                ("1usd", 1, "🎥 1-Dars: Panik ataka va kuchli vahimani 3 daqiqada to'xtatish", "Muallif: Furqat Bag'ibekov. Vagus nervini faollashtirish va tana relaksatsiyasi amaliyoti.", "video", None, now_iso),
                
                # 10$ Kurs: 3 ta video/audio
                ("10usd", 1, "🎬 1-Dars: Ong osti xavotirlari va stress ildizini aniqlash", "Stress va ortiqcha xavotirning asl sabablari va ularni ongli jilovlash usullari.", "video", None, now_iso),
                ("10usd", 2, "🎬 2-Dars: Psixosomatik bloklarni tana mashqlari bilan yechish", "Bo'yin, yelka va nafas yo'llaridagi psixosomatik qisilishlarni bo'shatish mashqlari.", "video", None, now_iso),
                ("10usd", 3, "🎬 3-Dars: Hissiy intellekt va ichki xotirjamlikni mustahkamlash", "Ichki tanqidchini to'xtatish va doimiy emotsional barqarorlikka erishish.", "video", None, now_iso),
                
                # 100$ VIP Kurs: 5 ta video + Bepul konsultatsiya
                ("100usd", 1, "👑 1-Video: Chuqur ruhiy transformatsiya va ichki bloklarni sindirish", "12 yillik klinik psixoterapiya metodikasi asosida shaxsiy o'sish.", "video", None, now_iso),
                ("100usd", 2, "👑 2-Video: Moliyaviy psixologiya va pulga nisbatan ichki chegaralarni kengaytirish", "Moddiy xavotirlarni yengish va daromad potensialini ochish.", "video", None, now_iso),
                ("100usd", 3, "👑 3-Video: Psixosomatikani to'liq davolash va biologik quvvatni tiklash", "Tanadagi surunkali taranglik va charchoqni yo'qotish.", "video", None, now_iso),
                ("100usd", 4, "👑 4-Video: Toksik munosabatlardan xalos bo'lish va mustahkam shaxsiy chegaralar", "Yaqinlar bilan sog'lom munosabat qurish va erkin 'yo'q' deyish.", "video", None, now_iso),
                ("100usd", 5, "👑 5-Video: 1 Oylik shaxsiy mentorlik va doimiy xotirjamlik strategiyasi", "Kelajakdagi maqsadlar va barqaror psixologik immunitet.", "video", None, now_iso),
                ("100usd", 6, "🎁 6-Bonus: Bepul Shaxsiy Video-Konsultatsiya (1-on-1)", "Psixoterapevt Furqat Bag'ibekov bilan to'g'ridan-to'g'ri 45 daqiqalik shaxsiy seans vaqtingizni belgilang.", "text", None, now_iso),
            ]
            await db.executemany(
                """INSERT INTO course_materials (course_key, lesson_order, title, description, media_type, media_file_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                default_materials,
            )

        now_iso = datetime.utcnow().isoformat()
        # 1. Jamoa a'zolarini dastlabki to'ldirish (agar bo'sh bo'lsa)
        cur = await db.execute("SELECT COUNT(*) FROM team_members")
        team_count = (await cur.fetchone())[0]
        if team_count == 0:
            default_team = [
                (
                    "furqat",
                    "Bag'ibekov Furqat",
                    "Bosh Psixoterapevt, Sokin Qalb markazi asoschisi",
                    "12 yillik klinik tajriba",
                    "👨‍⚕️",
                    "• Kognitiv-xulq-atvor psixoterapiyasi va neyropsixologiya\n• Chuqur somatik tana terapiyasi va psixosomatika\n• Surunkali stress, vahima (panik ataka) va chuqur psixozlar\n• Ong osti psixologik travmalari va ildiz bloklarini yechish",
                    "• 💊 <b>Xitoy Davolash Kapsulasi (Kapsulaterapiya):</b> Tanani chuqur relaksatsiya qilish, barcha psixosomatik spazm va mushak qisilishlarini yechish.\n• 💡 <b>Fransiya Neyro-Lampasi (Ko'z uchun stroboskopik yorug'lik):</b> Miya to'lqinlarini alfa/teta darajasiga tushirib, inson ong osti bilan to'g'ridan-to'g'ri muloqot o'rnatish.\n• 🎶 <b>Maxsus Neyro-Akustik Musiqa:</b> Ong ostidagi stress va psixoz ildizini bir zumda ochish va to'liq davolash (lichina).",
                    "🏆 15,400+ muvaffaqiyatli sog'lomlashtirilgan mijozlar\n🏆 89% holatda 14 kunda vahima va xavotirdan to'liq xalos qilish\n🏆 94% mijozlarda sifatli uyqu va ruhiy immunitetni tiklash\n🏆 4.95 / 5.0 mijozlar mamnuniyat bahosi",
                    None,
                    1,
                    1,
                    now_iso,
                ),
                (
                    "dilfuza",
                    "Muminova Dilfuza",
                    "Yetakchi Psixoterapevt, Ayollar va Oilaviy Psixologiya Eksperti",
                    "15 yillik professional tajriba",
                    "👩‍⚕️",
                    "• Ayollar ruhiy salomatligi va ichki resurslarini qayta tiklash\n• Oilaviy munosabatlar inqirozi, ajralish va xiyonat og'riqlari\n• Tug'ruqdan keyingi depressiya va hissiy charchoq (burnout)\n• Bolalik travmalari, qo'rquvlar va o'ziga ishonchsizlik",
                    "• 🌿 <b>Gestalt va Tizimli Oilaviy Terapiya:</b> Oila a'zolari o'rtasidagi sovuqlik va ko'p yillik tushunmovchiliklarni ildizidan bartaraf etish.\n• 💎 <b>Hissiy Tozalash Texnikalari:</b> Ong ostida to'plangan aybdorlik, xafagarchilik va og'riqlarni xavfsiz bartaraf etish.\n• 🎨 <b>Integrativ Art-Terapiya:</b> Ayollarning nozik his-tuyg'ularini kashf qilish va yangi hayotiy quvvat bag'ishlash.",
                    "🏆 12,000+ muvaffaqiyatli individual va oilaviy konsultatsiyalar\n🏆 Minglab oilalarni ajralish yoqasidan saqlab qolish va totuvlikka qaytarish\n🏆 Ko'plab ayollarga o'z qadrini bilish va baxtli hayot qurishda yo'l ko'rsatish",
                    None,
                    2,
                    1,
                    now_iso,
                ),
                (
                    "temur",
                    "Baydjanov Temur",
                    "Yetakchi Psixoterapevt, Neyropsixologik Xulq-atvor Mutaxassisi",
                    "10 yillik klinik tajriba",
                    "👨‍⚕️",
                    "• Erkaklar psixologiyasi va yuqori mas'uliyatdagi hissiy bosim\n• Biznes, moliya va faoliyatdagi o'tkir stress va inqirozlar\n• Nevrozlar, fobiya, vahima (panika) va uyqusizlik\n• Agressiya, asabiylik va ichki zo'riqishni boshqarish",
                    "• 🧠 <b>Kognitiv-Xulq-atvor Terapiyasi (KXT / REBT):</b> Salbiy avtomatik fikrlar va ichki qo'rquvlarni mantiqiy qayta dasturlash.\n• 🫁 <b>Vagus Nervi va Nafas Neyro-Terapiyasi:</b> Tanani zudlik bilan tinchlantiruvchi somatik mashqlar.\n• 🛡 <b>Psixologik Immunitet:</b> Shaxsiy samaradorlik va bosim ostida xotirjam qaror qabul qilish ko'nikmalari.",
                    "🏆 8,500+ dori-darmonsiz sog'lomlashtirilgan mijozlar\n🏆 Rahbarlar va tadbirkorlarning hissiy quvvatini tiklash bo'yicha yuqori natijalar\n🏆 O'tkir nevroz va xavotirlarni qisqa muddatda bartaraf etish",
                    None,
                    3,
                    1,
                    now_iso,
                ),
            ]
            await db.executemany(
                """INSERT INTO team_members (member_key, name, title, experience, avatar_icon, directions_text, methodology_text, achievements_text, photo_file_id, order_num, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                default_team,
            )

        # 2. Kurslar va Retreatlarni dastlabki to'ldirish
        cur = await db.execute("SELECT COUNT(*) FROM dynamic_courses")
        course_count = (await cur.fetchone())[0]
        if course_count == 0:
            default_courses = [
                (
                    "free",
                    "🌿 Sokinlik Sari Ilk Qadam (Kirish Kursi)",
                    "course",
                    "Psixoterapevt Bagbekov Furqat",
                    "Bepul (0$)",
                    "1 kunlik kirish amaliyoti",
                    "Ichki xotirjamlikni his qilish va o'z ong osti bilan tanishishni xohlovchilar uchun.",
                    "• 3 ta audio-darslik\n• Vagus nervi relaksatsiya texnikasi\n• Dastlabki stress tahlili",
                    "Ushbu bepul kirish darsida siz ichki xavotir va stressdan 1 daqiqada qutulishning asosiy psixologik sirlarini o'rganasiz.",
                    None,
                    1,
                    1,
                    now_iso,
                ),
                (
                    "1usd",
                    "💎 1$ Kurs (1 ta darslik)",
                    "course",
                    "Psixoterapevt Bagbekov Furqat",
                    "1$ (~12 800 so'm)",
                    "1 ta eksklyuziv video-darslik",
                    "Panik ataka, vahima va to'satdan yurak qisilishini tezkor to'xtatmoqchi bo'lganlar uchun.",
                    "• 1 ta to'liq video-darslik\n• Nafas va tana mashqlari\n• Qo'rquvni ongli boshqarish protokoli",
                    "Tezkor psixoterapevtik texnika orqali o'tkir xavotir xurujini bir zumda to'xtatish metodikasi.",
                    None,
                    2,
                    1,
                    now_iso,
                ),
                (
                    "10usd",
                    "🌟 10$ Kurs (3 ta darslik)",
                    "course",
                    "Psixoterapevt Bagbekov Furqat",
                    "10$ (~128 000 so'm)",
                    "3 ta chuqur video-darslik",
                    "Surunkali xavotir, asabiylik va psixosomatik tana qisilishlarini bartaraf etmoqchi bo'lganlar uchun.",
                    "• 3 ta chuqur video-darslik\n• Ong osti xavotirlarini tozalash\n• Tana mushaklarini bo'shatish amaliyoti",
                    "3 bosqichli amaliy darsliklar orqali ichki tanqidchini to'xtatish va barqaror xotirjamlikka erishish kursi.",
                    None,
                    3,
                    1,
                    now_iso,
                ),
                (
                    "100usd",
                    "💫 100$ Kurs (5 ta darslik + konsultatsiya)",
                    "course",
                    "Psixoterapevt Bagbekov Furqat",
                    "100$ (~1 280 000 so'm)",
                    "5 ta to'liq video-darslik + 1 ta Bepul Konsultatsiya",
                    "Hayotida to'liq ruhiy transformatsiyaga erishish va dori-darmonsiz doimiy yashashni istovchilar uchun.",
                    "• 5 ta mualliflik video-darsliklari\n• Bepul shaxsiy 1-on-1 konsultatsiya\n• Moliyaviy va munosabatlar bloklarini yechish\n• 1 oylik mentorlik strategiyasi",
                    "To'liq psixologik transformatsiya kursi va Furqat Bag'ibekov bilan shaxsiy konsultatsiya.",
                    None,
                    4,
                    1,
                    now_iso,
                ),
                (
                    "150usd_session",
                    "🌿 1 Seans: Konsultatsiya + Kapsulaterapiya + Fransiya Neyro-Lampasi",
                    "session",
                    "Psixoterapevt Bagbekov Furqat",
                    "150$ (~1 920 000 so'm)",
                    "1 ta to'liq kompleks davolash seansi",
                    "Tezkor ruhiy yengillashish, ong ostidagi xavotir, qo'rquv, psixoz va tana bloklarini ildizi bilan bartaraf etmoqchi bo'lganlar uchun.",
                    "• Shaxsiy konsultatsiya va ildiz diagnostikasi\n• Xitoydan keltirilgan davolash Kapsulasi\n• Fransiyadan keltirilgan ko'z neyro-lampasi\n• Maxsus neyro-akustik musiqa",
                    "Ushbu seansda Furqat Bag'ibekovning 12 yillik amaliyoti, Xitoy kapsulaterapiyasi va Fransiya neyro-chirog'i uyg'unlashgan holda to'liq shifo beradi.",
                    None,
                    5,
                    1,
                    now_iso,
                ),
                (
                    "350usd_session",
                    "🌿 3 Seans: 3 ta Chuqur Terapiya (Konsultatsiya + Kapsula + Fransiya Lampasi)",
                    "session",
                    "Psixoterapevt Bagbekov Furqat",
                    "350$ (~4 480 000 so'm)",
                    "3 ta to'liq tizimli kompleks davolash seansi",
                    "Surunkali stress, uzoq yillik vahima (panika), psixoz, depressiv holat va psixosomatik kasalliklarni ildizi bilan to'liq davolash uchun.",
                    "• 3 ta individual psixoterapevtik konsultatsiya\n• 3 ta Xitoy Kapsulaterapiya seansi\n• 3 ta Fransiya neyro-lampasi seansi\n• Maxsus neyro-akustik musiqa",
                    "3 seanslik kompleks terapiya orqali barcha psixosomatik bloklar ildizi bilan yo'qotiladi.",
                    None,
                    6,
                    1,
                    now_iso,
                ),
                (
                    "500usd_vip_session",
                    "👑 VIP Seans: VIP Konsultatsiya + VIP Kapsulaterapiya & Neyro-Texnologiyalar",
                    "session",
                    "Psixoterapevt Bagbekov Furqat",
                    "500$ (~6 400 000 so'm)",
                    "VIP Individual Kompleks Dastur (To'liq Transformatsiya)",
                    "Maksimal individual yondashuv, katta hayotiy/biznes inqirozlardan tezkor chiqish va VIP darajadagi ruhiy erkinlikni xohlovchilar uchun.",
                    "• To'g'ridan-to'g'ri VIP Konsultatsiya\n• VIP Kapsulaterapiya va Fransiya neyro-yorug'lik protokoli\n• 24/7 shaxsiy aloqa va 1 oylik to'liq psixologik hamrohlik",
                    "VIP darajadagi ushbu individual dastur orqali shaxsiy, ruhiy va moddiy sohalardagi barcha to'siqlar butunlay bartaraf etiladi.",
                    None,
                    7,
                    1,
                    now_iso,
                ),
                (
                    "retreat_uzb",
                    "🏔 Retreat O'zbekiston (Tog' Bag'rida Qayta Yuklanish)",
                    "retreat",
                    "Psixoterapevt Bagbekov Furqat & Sokin Qalb jamoasi",
                    "Boshlanmoqchi bo'lgan vaqtda e'lon qilinadi",
                    "3 kun / 2 kecha (O'zbekiston Tog'larida Jonli)",
                    "Shahar shovqini va stressdan butunlay uzilib, go'zal O'zbekiston tabiatida ruhiy va jismoniy dam olmoqchi bo'lganlar uchun.",
                    "• Tog' bag'ridagi so'lim ekohotelda yashash\n• Jonli psixoterapiya va tana amaliyotlari\n• Raqamli detoks va meditatsiyalar",
                    "O'zbekistonning so'lim tog'larida 3 kunlik to'liq yangilanish retreati.",
                    None,
                    8,
                    1,
                    now_iso,
                ),
                (
                    "retreat_thailand",
                    "🌴 Retreat Tailand (Tropik Okean Sohilida Sokinlik)",
                    "retreat",
                    "Psixoterapevt Bagbekov Furqat & Xalqaro Ekspertlar",
                    "Boshlanmoqchi bo'lgan vaqtda e'lon qilinadi",
                    "7 kun / 6 kecha (Tailand Tropik Orolida)",
                    "Butunlay yangi muhitda o'z qalbini kashf qilish, okean energiyasi bilan to'yinish va hayotiy maqsadlarni yangilamoqchi bo'lganlar uchun.",
                    "• Okean bo'yidagi premium villa\n• Chuqur VIP psixoterapiya va meditatsiyalar\n• Ekzotik sayohatlar va tanani yoshartirish",
                    "Tailandning tropik orolida 7 kunlik unutilmas ruhiy va jismoniy transformatsiya sayohati.",
                    None,
                    9,
                    1,
                    now_iso,
                ),
            ]
            await db.executemany(
                """INSERT INTO dynamic_courses (course_key, title, category, author, price, duration, target, features_text, description, photo_file_id, order_num, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                default_courses,
            )

        # 3. Referral Sovg'alarini dastlabki to'ldirish
        cur = await db.execute("SELECT COUNT(*) FROM referral_gifts")
        gift_count = (await cur.fetchone())[0]
        if gift_count == 0:
            default_gifts = [
                (
                    "gift_1",
                    "🎁 1-Sovg'a: 1$ Kurs (1 ta darslik)",
                    1,
                    "1 ta do'stingizni taklif qiling va 1$ lik panik ataka va vahimaga qarshi to'liq darslikni bepul oching!",
                    "course",
                    "1usd",
                    None,
                    1,
                    1,
                    now_iso,
                ),
                (
                    "gift_2",
                    "🎁 2-Sovg'a: 10$ Kurs (3 ta darslik)",
                    3,
                    "3 ta do'stingizni taklif qiling va 10$ lik 3 bosqichli to'liq video-darsliklar kursini bepul oching!",
                    "course",
                    "10usd",
                    None,
                    2,
                    1,
                    now_iso,
                ),
                (
                    "gift_3",
                    "🎁 3-Sovg'a: 100$ Kurs (5 ta darslik + Bepul Konsultatsiya)",
                    10,
                    "10 ta do'stingizni taklif qiling va 100$ lik 5 ta video-darslik hamda Furqat Bag'ibekov bilan 1-on-1 bepul konsultatsiyani oching!",
                    "course",
                    "100usd",
                    None,
                    3,
                    1,
                    now_iso,
                ),
            ]
            await db.executemany(
                """INSERT INTO referral_gifts (gift_key, title, required_friends, description, reward_type, reward_content, photo_file_id, order_num, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                default_gifts,
            )

        await db.commit()


# ---------- Foydalanuvchilar va Referral Tizimi ----------

async def get_or_create_user(
    telegram_id: int,
    full_name: str,
    username: Optional[str],
    referrer_tg_id: Optional[int] = None,
    return_details: bool = False,
) -> Any:
    """Foydalanuvchini olish yoki yangisini yaratish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET full_name = ?, username = ? WHERE telegram_id = ?",
                (full_name, username, telegram_id),
            )
            await db.commit()
            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cur.fetchone()
            user_dict = dict(row)
            return (user_dict, False, None) if return_details else user_dict

        # Yangi foydalanuvchi yaratish
        referred_by_id = None
        referrer_user = None

        if referrer_tg_id and referrer_tg_id != telegram_id:
            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (referrer_tg_id,))
            ref_row = await cur.fetchone()
            if ref_row:
                referred_by_id = ref_row["id"]
                # Referrer hisobini 1 taga oshirish
                await db.execute(
                    "UPDATE users SET referrals_count = referrals_count + 1 WHERE id = ?",
                    (referred_by_id,),
                )
                await db.commit()
                cur = await db.execute("SELECT * FROM users WHERE id = ?", (referred_by_id,))
                referrer_user = dict(await cur.fetchone())

        await db.execute(
            """INSERT INTO users (telegram_id, full_name, username, created_at, referred_by, referrals_count)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (telegram_id, full_name, username, datetime.utcnow().isoformat(), referred_by_id),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        new_row = await cur.fetchone()
        new_user = dict(new_row)
        return (new_user, True, referrer_user) if return_details else new_user


async def get_referral_stats(user_id: int) -> dict:
    """Foydalanuvchining referral statistikasi va ochilgan kurslari (1$=1, 10$=3, 100$=10)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = await cur.fetchone()
        count = user["referrals_count"] if user and "referrals_count" in user.keys() and user["referrals_count"] else 0
        return {
            "count": count,
            "unlocked_1usd": count >= 1,
            "unlocked_10usd": count >= 3,
            "unlocked_100usd": count >= 10,
            "needed_1usd": max(0, 1 - count),
            "needed_10usd": max(0, 3 - count),
            "needed_100usd": max(0, 10 - count),
        }


async def get_user_referrals(user_id: int) -> list[dict]:
    """Foydalanuvchi taklif qilgan barcha do'stlar ro'yxati."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, telegram_id, full_name, username, created_at FROM users WHERE referred_by = ? ORDER BY id DESC",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_all_active_users() -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE is_active = 1")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_users() -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users ORDER BY id DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_user_telegram_ids() -> list[int]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT telegram_id FROM users WHERE is_active = 1")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def mark_diagnostic_done(user_id: int) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET diagnostic_done = 1 WHERE id = ?", (user_id,))
        await db.commit()


async def advance_course_day(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET course_day = course_day + 1 WHERE id = ?", (user_id,))
        await db.commit()
        cur = await db.execute("SELECT course_day FROM users WHERE id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0]


async def set_active(telegram_id: int, active: bool) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET is_active = ? WHERE telegram_id = ?", (1 if active else 0, telegram_id)
        )
        await db.commit()


async def toggle_user_active_by_id(user_id: int) -> bool:
    """Foydalanuvchi faolligini almashtiradi va yangi holatini qaytaradi."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            return False
        new_val = 0 if row["is_active"] else 1
        await db.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_val, user_id))
        await db.commit()
        return bool(new_val)


# ---------- Diagnostika ----------

async def save_diagnostic(
    user_id: int,
    answers: dict,
    ai_summary: str,
    focus_areas: list[str],
    course_outline: list[dict],
    risk_flag: bool,
) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO diagnostics
               (user_id, answers_json, ai_summary, focus_areas_json, course_outline_json, risk_flag, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                json.dumps(answers, ensure_ascii=False),
                ai_summary,
                json.dumps(focus_areas, ensure_ascii=False),
                json.dumps(course_outline, ensure_ascii=False),
                1 if risk_flag else 0,
                datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()


async def get_latest_diagnostic(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM diagnostics WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["answers"] = json.loads(d["answers_json"])
        d["focus_areas"] = json.loads(d["focus_areas_json"] or "[]")
        d["course_outline"] = json.loads(d["course_outline_json"] or "[]")
        return d


async def get_first_diagnostic(user_id: int) -> Optional[dict]:
    """Foydalanuvchining botga ilk qo'shilgandagi dastlabki diagnostika holati (Baseline)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM diagnostics WHERE user_id = ? ORDER BY id ASC LIMIT 1", (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["answers"] = json.loads(d["answers_json"])
        d["focus_areas"] = json.loads(d["focus_areas_json"] or "[]")
        d["course_outline"] = json.loads(d["course_outline_json"] or "[]")
        return d


# ---------- Kundalik kuzatuv (check-in) ----------

async def save_checkin(
    user_id: int,
    mood: int,
    stress: int,
    note: Optional[str] = None,
    achievements: Optional[str] = None,
    struggles: Optional[str] = None,
) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO checkins
               (user_id, checkin_date, mood_score, stress_score, achievements, struggles, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                date.today().isoformat(),
                mood,
                stress,
                achievements,
                struggles,
                note,
                datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()


async def get_today_checkin(user_id: int) -> Optional[dict]:
    """Foydalanuvchining bugungi check-in ma'lumotlarini olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM checkins WHERE user_id = ? AND checkin_date = ? ORDER BY id DESC LIMIT 1",
            (user_id, date.today().isoformat()),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_recent_checkins(user_id: int, limit: int = 7) -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM checkins WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_checkins_for_period(user_id: int, days: int = 7) -> list[dict]:
    """Muayyan kunlar oralig'idagi barcha check-inlarni sana tartibida olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM checkins
               WHERE user_id = ? AND checkin_date >= date('now', ?)
               ORDER BY checkin_date ASC""",
            (user_id, f"-{days} days"),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def has_checked_in_today(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM checkins WHERE user_id = ? AND checkin_date = ?",
            (user_id, date.today().isoformat()),
        )
        row = await cur.fetchone()
        return row[0] > 0


# ---------- Kunlik topshiriqlar (Tasks & Checklist) ----------

async def create_task(
    user_id: int,
    task_text: str,
    task_title: Optional[str] = None,
    task_desc: Optional[str] = None,
    task_benefit: Optional[str] = None,
) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """INSERT INTO tasks (user_id, task_date, task_text, task_title, task_desc, task_benefit, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                date.today().isoformat(),
                task_text,
                task_title or task_text,
                task_desc or "",
                task_benefit or "",
                datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def save_user_photo(user_id: int, photo_file_id: str) -> None:
    """Foydalanuvchining shaxsiy profil rasmini xavfsiz saqlash."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET photo_file_id = ? WHERE id = ?", (photo_file_id, user_id))
        await db.commit()


async def get_user_photo(user_id: int) -> Optional[str]:
    """Foydalanuvchining shaxsiy profil rasmining file_id sini olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT photo_file_id FROM users WHERE id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row and row[0] else None


async def save_daily_tasks(user_id: int, tasks: list[dict]) -> list[dict]:
    """Foydalanuvchi uchun bugungi barcha soatma-soat AI topshiriqlarini saqlaydi."""
    default_hours = ["07:00", "09:30", "13:30", "17:30", "21:30"]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        today_str = date.today().isoformat()
        # Oldingi bugungi topshiriqlarni tozalash (agar yangilansa)
        await db.execute("DELETE FROM tasks WHERE user_id = ? AND task_date = ?", (user_id, today_str))
        for i, t in enumerate(tasks):
            title = t.get("title") or t.get("task_title") or f"Topshiriq {i+1}"
            desc = t.get("desc") or t.get("task_desc") or ""
            benefit = t.get("benefit") or t.get("task_benefit") or ""
            sched_time = t.get("time") or t.get("scheduled_time") or default_hours[i % len(default_hours)]
            full_text = f"{title}: {desc}" if desc else title
            await db.execute(
                """INSERT INTO tasks (user_id, task_date, task_text, task_title, task_desc, task_benefit, scheduled_time, reminder_sent_count, is_done, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)""",
                (user_id, today_str, full_text, title, desc, benefit, sched_time, datetime.utcnow().isoformat()),
            )
        await db.commit()
    return await get_today_tasks(user_id)


async def get_today_tasks(user_id: int) -> list[dict]:
    """Bugungi barcha topshiriqlarni soat tartibida olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND task_date = ? ORDER BY scheduled_time ASC, id ASC",
            (user_id, date.today().isoformat()),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_pending_hourly_tasks(current_time_str: str) -> list[dict]:
    """Bajarilmagan va eslatma vaqti kelgan topshiriqlar ro'yxati."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        today_str = date.today().isoformat()
        cur = await db.execute(
            """SELECT t.*, u.telegram_id, u.full_name, u.photo_file_id 
               FROM tasks t
               JOIN users u ON t.user_id = u.id
               WHERE t.task_date = ? 
                 AND t.is_done = 0 
                 AND t.scheduled_time <= ?
                 AND t.reminder_sent_count < 4
                 AND u.is_active = 1
               ORDER BY t.scheduled_time ASC""",
            (today_str, current_time_str),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def increment_task_reminder(task_id: int) -> None:
    """Topshiriq eslatma yuborilganlar sonini 1 taga oshirish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE tasks SET reminder_sent_count = reminder_sent_count + 1 WHERE id = ?",
            (task_id,),
        )
        await db.commit()


async def get_today_task(user_id: int) -> Optional[dict]:
    """Eski muvofiqlik uchun bitta topshiriq qaytarish."""
    tasks = await get_today_tasks(user_id)
    return tasks[0] if tasks else None


async def toggle_task_done(task_id: int) -> tuple[bool, int, int, int]:
    """Topshiriq holatini o'zgartiradi (bajarildi / bajarilmadi) va (new_status, completed_count, total_count, percent) qaytaradi."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = await cur.fetchone()
        if not task:
            return False, 0, 0, 0
        new_is_done = 0 if task["is_done"] else 1
        comp_at = datetime.utcnow().isoformat() if new_is_done else None
        await db.execute("UPDATE tasks SET is_done = ?, completed_at = ? WHERE id = ?", (new_is_done, comp_at, task_id))
        await db.commit()

        # Bugungi umumiy statistika
        cur = await db.execute(
            "SELECT COUNT(*), SUM(is_done) FROM tasks WHERE user_id = ? AND task_date = ?",
            (task["user_id"], task["task_date"]),
        )
        row = await cur.fetchone()
        total = row[0] or 0
        completed = row[1] or 0
        percent = int((completed / total) * 100) if total > 0 else 0
        return bool(new_is_done), completed, total, percent


async def get_today_task_stats(user_id: int) -> dict:
    """Foydalanuvchining bugungi topshiriqlar statistikasi."""
    tasks = await get_today_tasks(user_id)
    total = len(tasks)
    completed = sum(1 for t in tasks if t["is_done"])
    percent = int((completed / total) * 100) if total > 0 else 0
    return {
        "tasks": tasks,
        "total": total,
        "completed": completed,
        "percent": percent,
    }


async def complete_task(task_id: int) -> Optional[dict]:
    """Topshiriqni 'Bajarildi' deb belgilash va topshiriq ma'lumotlarini qaytarish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = await cur.fetchone()
        if not task:
            return None
        now_iso = datetime.utcnow().isoformat()
        await db.execute("UPDATE tasks SET is_done = 1, completed_at = ? WHERE id = ?", (now_iso, task_id))
        await db.commit()
        cur = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return dict(await cur.fetchone())


async def get_users_with_pending_tasks_today() -> list[dict]:
    """Bugun topshiriqlari bor, ammo 100% bajarmagan foydalanuvchilar (eslatma uchun)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT users.id as user_id, users.telegram_id, users.full_name,
                      COUNT(tasks.id) as total_tasks,
                      SUM(tasks.is_done) as completed_tasks
               FROM users
               JOIN tasks ON tasks.user_id = users.id
               WHERE tasks.task_date = ? AND users.is_active = 1
               GROUP BY users.id
               HAVING completed_tasks < total_tasks""",
            (date.today().isoformat(),),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ---------- Kontent tarixi ----------

async def log_content_sent(user_id: int, lesson_title: str, meditation_title: str) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO content_log (user_id, content_date, lesson_title, meditation_title, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, date.today().isoformat(), lesson_title, meditation_title, datetime.utcnow().isoformat()),
        )
        await db.commit()


# ---------- AI Suhbatlar tarixi (AI Conversations) ----------

async def save_ai_message(user_id: int, role: str, content: str) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO ai_conversations (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_ai_history(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT role, content FROM ai_conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in reversed(rows)]


async def clear_ai_history(user_id: int) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM ai_conversations WHERE user_id = ?", (user_id,))
        await db.commit()


# ---------- Admin Panel uchun Funksiyalar ----------

async def get_bot_statistics() -> dict:
    """Admin panel uchun to'liq statistika."""
    today_str = date.today().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Total users
        cur = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cur.fetchone())[0]

        # Active users
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = (await cur.fetchone())[0]

        # Diagnostika topshirganlar
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE diagnostic_done = 1")
        diagnosed_users = (await cur.fetchone())[0]

        # Bugun qo'shilganlar
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (f"{today_str}%",))
        today_joined = (await cur.fetchone())[0]

        # Bugungi checkinlar
        cur = await db.execute("SELECT COUNT(*) FROM checkins WHERE checkin_date = ?", (today_str,))
        today_checkins = (await cur.fetchone())[0]

        # Bugun bajarilgan topshiriqlar
        cur = await db.execute("SELECT COUNT(*) FROM tasks WHERE task_date = ? AND is_done = 1", (today_str,))
        today_tasks_done = (await cur.fetchone())[0]

        # Risk flag soni
        cur = await db.execute("SELECT COUNT(DISTINCT user_id) FROM diagnostics WHERE risk_flag = 1")
        risk_cases_count = (await cur.fetchone())[0]

        # O'rtacha kayfiyat va stress (so'nggi 7 kun)
        cur = await db.execute(
            "SELECT AVG(mood_score), AVG(stress_score) FROM checkins WHERE checkin_date >= date('now', '-7 days')"
        )
        avg_row = await cur.fetchone()
        avg_mood = round(avg_row[0], 1) if avg_row and avg_row[0] is not None else 0.0
        avg_stress = round(avg_row[1], 1) if avg_row and avg_row[1] is not None else 0.0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": total_users - active_users,
            "diagnosed_users": diagnosed_users,
            "today_joined": today_joined,
            "today_checkins": today_checkins,
            "today_tasks_done": today_tasks_done,
            "risk_cases_count": risk_cases_count,
            "avg_mood_7d": avg_mood,
            "avg_stress_7d": avg_stress,
        }


async def get_users_paginated(page: int = 1, page_size: int = 8) -> tuple[list[dict], int]:
    """Sahifalangan foydalanuvchilar ro'yxati va umumiy sahifalar soni."""
    offset = (page - 1) * page_size
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) FROM users")
        total_count = (await cur.fetchone())[0]
        total_pages = max(1, (total_count + page_size - 1) // page_size)

        cur = await db.execute(
            "SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?",
            (page_size, offset),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows], total_pages


async def search_users(query: str) -> list[dict]:
    """Telegram ID, username yoki ism bo'yicha foydalanuvchilarni qidirish."""
    query = query.strip().lstrip("@")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if query.isdigit():
            cur = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ? OR id = ? LIMIT 10",
                (int(query), int(query)),
            )
        else:
            search_pattern = f"%{query}%"
            cur = await db.execute(
                "SELECT * FROM users WHERE username LIKE ? OR full_name LIKE ? ORDER BY id DESC LIMIT 10",
                (search_pattern, search_pattern),
            )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_risk_users() -> list[dict]:
    """Xavf belgisi (risk_flag = 1) tushgan foydalanuvchilar ro'yxati."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT users.id, users.telegram_id, users.full_name, users.username,
                      diagnostics.created_at as diag_date, diagnostics.ai_summary, diagnostics.answers_json
               FROM diagnostics
               JOIN users ON users.id = diagnostics.user_id
               WHERE diagnostics.risk_flag = 1
               ORDER BY diagnostics.id DESC"""
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_user_full_details(user_id: int) -> Optional[dict]:
    """Foydalanuvchining barcha tarixi va ma'lumotlarini olish."""
    user = await get_user_by_id(user_id)
    if not user:
        return None
    latest_diag = await get_latest_diagnostic(user_id)
    checkins = await get_recent_checkins(user_id, limit=7)
    today_task = await get_today_task(user_id)

    return {
        "user": user,
        "diagnostic": latest_diag,
        "checkins": checkins,
        "today_task": today_task,
    }


# =========================================================================
# 4 ASOSIY HAYOTIY USTUN (MOLIYA, RUHIYAT, JISMONIY, MUNOSABATLAR)
# =========================================================================

async def save_four_pillars_record(
    user_id: int,
    financial_score: int,
    mental_score: int,
    physical_score: int,
    relationship_score: int,
    ai_advice: Optional[str] = None,
) -> dict:
    """4 ta ustun (Moliya, Ruhiyat, Jismoniy, Munosabatlar) baholarini saqlash."""
    now_str = datetime.now().isoformat()
    today_str = date.today().isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """INSERT INTO four_pillars_records
               (user_id, recorded_date, financial_score, mental_score, physical_score, relationship_score, ai_advice, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                today_str,
                financial_score,
                mental_score,
                physical_score,
                relationship_score,
                ai_advice,
                now_str,
            ),
        )
        record_id = cur.lastrowid
        await db.commit()

        cur = await db.execute("SELECT * FROM four_pillars_records WHERE id = ?", (record_id,))
        row = await cur.fetchone()
        return dict(row) if row else {}


async def get_latest_four_pillars(user_id: int) -> Optional[dict]:
    """Foydalanuvchining eng oxirgi 4 ta ustun bahosi."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM four_pillars_records WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_previous_four_pillars(user_id: int) -> Optional[dict]:
    """Foydalanuvchining oldingi (o'tgan haftadagi) 4 ta ustun bahosi (taqqoslash uchun)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM four_pillars_records WHERE user_id = ? ORDER BY id DESC LIMIT 1 OFFSET 1",
            (user_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_four_pillars_history(user_id: int, limit: int = 10) -> list[dict]:
    """4 ta ustun baholari tarixi."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM four_pillars_records WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def is_weekly_review_due(user_id: int) -> bool:
    """Haftalik 4 ta ustun qaydi topshirilishi shartligini tekshiradi."""
    user = await get_user_by_id(user_id)
    if not user or not user.get("diagnostic_done"):
        return False

    latest = await get_latest_four_pillars(user_id)
    today = date.today()

    if not latest:
        # Agar foydalanuvchi botga kirganiga 7 kun bo'lgan bo'lsa yoki haftaning yakshanbasi bo'lsa
        course_day = user.get("course_day", 1)
        if course_day >= 7:
            return True
        created_str = user.get("created_at", "")
        if created_str:
            try:
                created_dt = datetime.fromisoformat(created_str).date()
                if (today - created_dt).days >= 7:
                    return True
            except Exception:
                pass
        # Agar yakshanba kuni bo'lsa va 1 ta ham haftalik qayd bo'lmasa
        if today.weekday() == 6:
            return True
        return False

    rec_date_str = latest.get("recorded_date", "")
    if not rec_date_str:
        return True

    try:
        rec_date = date.fromisoformat(rec_date_str)
        # Agar oxirgi qaydga 7 yoki undan ko'p kun bo'lgan bo'lsa
        if (today - rec_date).days >= 7:
            return True
        # Agar oxirgi qayd o'tgan haftaga tegishli bo'lsa va yangi hafta (dushanba-yakshanba) boshlangan bo'lsa
        if rec_date.isocalendar()[:2] < today.isocalendar()[:2]:
            return True
    except Exception:
        return False

    return False


async def is_monthly_review_due(user_id: int) -> bool:
    """Oylik katta transformatsiya qaydi topshirilishi shartligini tekshiradi."""
    user = await get_user_by_id(user_id)
    if not user or not user.get("diagnostic_done"):
        return False

    course_day = user.get("course_day", 1)
    if course_day < 30:
        return False

    # Check-inlar tarixi va oylik davr
    checkins = await get_checkins_for_period(user_id, days=30)
    if len(checkins) < 4:
        return False
    return False


# ---------- Kurslarni Ochish va To'lov Cheklari ----------

async def unlock_course(user_id: int, course_key: str, source: str = "payment") -> None:
    """Foydalanuvchiga pullik kursni ochib berish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO unlocked_courses (user_id, course_key, unlocked_at, source)
               VALUES (?, ?, ?, ?)""",
            (user_id, course_key, datetime.utcnow().isoformat(), source),
        )
        await db.commit()


async def is_course_unlocked(user_id: int, course_key: str) -> bool:
    """Foydalanuvchida ushbu kurs ochilganmi yoki yo'qligini tekshirish."""
    # Bepul 5 kunlik kurs hammaga ochiq
    if course_key in ("5day", "free"):
        return True
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM unlocked_courses WHERE user_id = ? AND course_key = ?",
            (user_id, course_key),
        )
        row = await cur.fetchone()
        if row:
            return True
        # Referral bo'yicha ham tekshiramiz
        cur = await db.execute("SELECT referrals_count FROM users WHERE id = ?", (user_id,))
        u = await cur.fetchone()
        count = u[0] if u and u[0] else 0
        if course_key == "1usd" and count >= 1:
            return True
        if course_key == "10usd" and count >= 3:
            return True
        if course_key == "100usd" and count >= 10:
            return True
        return False


# ---------- Kurs Materiallari (Video / Audio / Darslar) Boshqaruvi ----------

async def get_course_materials(course_key: str) -> list[dict]:
    """Kursga tegishli barcha darslar / video / audio materiallar."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM course_materials WHERE course_key = ? ORDER BY lesson_order ASC, id ASC",
            (course_key,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_course_material_by_id(material_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM course_materials WHERE id = ?", (material_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def add_course_material(
    course_key: str,
    lesson_order: int,
    title: str,
    description: str,
    media_type: str = "video",
    media_file_id: Optional[str] = None,
) -> int:
    """Admin tomonidan kursga yangi video/audio darslik qo'shish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """INSERT INTO course_materials (course_key, lesson_order, title, description, media_type, media_file_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (course_key, lesson_order, title, description, media_type, media_file_id, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def update_course_material_media(material_id: int, media_type: str, media_file_id: str) -> bool:
    """Darslikka yangi video/audio file_id biriktirish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE course_materials SET media_type = ?, media_file_id = ? WHERE id = ?",
            (media_type, media_file_id, material_id),
        )
        await db.commit()
        return True


async def delete_course_material(material_id: int) -> bool:
    """Kurs darsligini o'chirish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM course_materials WHERE id = ?", (material_id,))
        await db.commit()
        return True


async def save_payment_receipt(user_id: int, course_key: str, amount_uzs: int, receipt_file_id: str) -> int:
    """Foydalanuvchi yuborgan to'lov chekini saqlash."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            """INSERT INTO payment_receipts (user_id, course_key, amount_uzs, receipt_file_id, status, created_at)
               VALUES (?, ?, ?, ?, 'pending', ?)""",
            (user_id, course_key, amount_uzs, receipt_file_id, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_pending_receipts() -> list[dict]:
    """Tasdiqlash kutilayotgan barcha to'lov cheklari."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT p.*, u.full_name, u.username, u.telegram_id
               FROM payment_receipts p
               JOIN users u ON p.user_id = u.id
               WHERE p.status = 'pending'
               ORDER BY p.id DESC"""
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def approve_payment_receipt(receipt_id: int) -> Optional[dict]:
    """To'lov chekini tasdiqlash va kursni avtomatik ochish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payment_receipts WHERE id = ?", (receipt_id,))
        row = await cur.fetchone()
        if not row:
            return None
        receipt = dict(row)
        now_str = datetime.utcnow().isoformat()
        await db.execute(
            "UPDATE payment_receipts SET status = 'approved', approved_at = ? WHERE id = ?",
            (now_str, receipt_id),
        )
        await db.execute(
            """INSERT OR IGNORE INTO unlocked_courses (user_id, course_key, unlocked_at, source)
               VALUES (?, ?, ?, 'payment')""",
            (receipt["user_id"], receipt["course_key"], now_str),
        )
        await db.commit()
        receipt["status"] = "approved"
        receipt["approved_at"] = now_str
        return receipt


async def reject_payment_receipt(receipt_id: int) -> Optional[dict]:
    """To'lov chekini bekor qilish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payment_receipts WHERE id = ?", (receipt_id,))
        row = await cur.fetchone()
        if not row:
            return None
        receipt = dict(row)
        await db.execute(
            "UPDATE payment_receipts SET status = 'rejected' WHERE id = ?",
            (receipt_id,),
        )
        await db.commit()
        receipt["status"] = "rejected"
        return receipt


async def get_admin_dashboard_stats() -> dict:
    """Admin uchun chuqur vizual statistika va ko'rsatkichlar."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Jami foydalanuvchilar va faollar
        cur = await db.execute("SELECT COUNT(*) as total, SUM(is_active) as active, SUM(diagnostic_done) as diag FROM users")
        u_row = dict(await cur.fetchone())
        
        # Bugungi yangi foydalanuvchilar
        today_iso = date.today().isoformat()
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (f"{today_iso}%",))
        today_new = (await cur.fetchone())[0]
        
        # So'nggi 7 kunlik check-inlar soni va o'rtacha ballar
        cur = await db.execute("SELECT COUNT(*) as total_checkins, AVG(mood_score) as avg_mood, AVG(stress_score) as avg_stress FROM checkins")
        c_row = dict(await cur.fetchone())
        
        # 4 ta hayotiy ustun o'rtacha ko'rsatkichlari
        cur = await db.execute(
            """SELECT AVG(financial_score) as avg_fin,
                      AVG(mental_score) as avg_men,
                      AVG(physical_score) as avg_phys,
                      AVG(relationship_score) as avg_rel
               FROM four_pillars_records"""
        )
        p_row = dict(await cur.fetchone())
        
        # To'lovlar va daromad
        cur = await db.execute("SELECT COUNT(*) as total_sales, SUM(amount_uzs) as total_revenue FROM payment_receipts WHERE status = 'approved'")
        pay_row = dict(await cur.fetchone())
        
        # Xavf guruhidagi insonlar soni
        cur = await db.execute("SELECT COUNT(*) FROM diagnostics WHERE risk_flag = 1")
        risk_count = (await cur.fetchone())[0]

        return {
            "total_users": u_row["total"] or 0,
            "active_users": u_row["active"] or 0,
            "diag_done": u_row["diag"] or 0,
            "today_new": today_new or 0,
            "total_checkins": c_row["total_checkins"] or 0,
            "avg_mood": round(c_row["avg_mood"] or 7.0, 1),
            "avg_stress": round(c_row["avg_stress"] or 3.5, 1),
            "avg_fin": round(p_row["avg_fin"] or 6.0, 1),
            "avg_men": round(p_row["avg_men"] or 6.5, 1),
            "avg_phys": round(p_row["avg_phys"] or 6.0, 1),
            "avg_rel": round(p_row["avg_rel"] or 7.0, 1),
            "total_sales": pay_row["total_sales"] or 0,
            "total_revenue": pay_row["total_revenue"] or 0,
            "risk_count": risk_count or 0,
        }


# =========================================================================
# SOKIN QALB JAMOYASI CRUD
# =========================================================================

async def get_all_team_members(active_only: bool = True) -> list[dict]:
    """Barcha jamoa a'zolarini tartib bo'yicha olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM team_members"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY order_num ASC, id ASC"
        cur = await db.execute(query)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_team_member(member_key: str) -> Optional[dict]:
    """Bitta jamoa a'zosini member_key orqali olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM team_members WHERE member_key = ?", (member_key,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_team_member_by_id(member_id: int) -> Optional[dict]:
    """Bitta jamoa a'zosini ID orqali olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM team_members WHERE id = ?", (member_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def save_team_member(
    member_key: str,
    name: str,
    title: str,
    experience: str,
    avatar_icon: str = "👨‍⚕️",
    directions_text: str = "",
    methodology_text: str = "",
    achievements_text: str = "",
    photo_file_id: Optional[str] = None,
    order_num: int = 10,
) -> dict:
    """Yangi jamoa a'zosini qo'shish yoki yangilash."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        now_iso = datetime.utcnow().isoformat()
        cur = await db.execute("SELECT id FROM team_members WHERE member_key = ?", (member_key,))
        existing = await cur.fetchone()
        if existing:
            await db.execute(
                """UPDATE team_members
                   SET name = ?, title = ?, experience = ?, avatar_icon = ?, directions_text = ?,
                       methodology_text = ?, achievements_text = ?, photo_file_id = COALESCE(?, photo_file_id),
                       order_num = ?
                   WHERE id = ?""",
                (name, title, experience, avatar_icon, directions_text, methodology_text, achievements_text, photo_file_id, order_num, existing[0]),
            )
            member_id = existing[0]
        else:
            cur = await db.execute(
                """INSERT INTO team_members (member_key, name, title, experience, avatar_icon, directions_text, methodology_text, achievements_text, photo_file_id, order_num, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (member_key, name, title, experience, avatar_icon, directions_text, methodology_text, achievements_text, photo_file_id, order_num, now_iso),
            )
            member_id = cur.lastrowid
        await db.commit()
    return await get_team_member_by_id(member_id)


async def update_team_member_field(member_id: int, field: str, value: Any) -> None:
    """Jamoa a'zosining alohida maydonini yangilash."""
    allowed_fields = {"name", "title", "experience", "avatar_icon", "directions_text", "methodology_text", "achievements_text", "photo_file_id", "order_num", "is_active"}
    if field not in allowed_fields:
        raise ValueError(f"Ruxsat berilmagan maydon: {field}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE team_members SET {field} = ? WHERE id = ?", (value, member_id))
        await db.commit()


async def delete_team_member(member_id: int) -> None:
    """Jamoa a'zosini o'chirish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
        await db.commit()


# =========================================================================
# KURSLAR VA RETREATLAR CRUD
# =========================================================================

async def get_all_dynamic_courses(active_only: bool = True) -> list[dict]:
    """Barcha kurslar, seanslar va retreatlarni tartib bilan olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM dynamic_courses"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY order_num ASC, id ASC"
        cur = await db.execute(query)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_dynamic_course(course_key: str) -> Optional[dict]:
    """Bitta kursni course_key orqali olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM dynamic_courses WHERE course_key = ?", (course_key,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_dynamic_course_by_id(course_id: int) -> Optional[dict]:
    """Bitta kursni ID orqali olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM dynamic_courses WHERE id = ?", (course_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def save_dynamic_course(
    course_key: str,
    title: str,
    category: str = "course",
    author: str = "Psixoterapevt Bagbekov Furqat",
    price: str = "10$",
    duration: str = "3 ta dars",
    target: str = "",
    features_text: str = "",
    description: str = "",
    photo_file_id: Optional[str] = None,
    order_num: int = 10,
) -> dict:
    """Yangi kurs/seans qo'shish yoki yangilash."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        now_iso = datetime.utcnow().isoformat()
        cur = await db.execute("SELECT id FROM dynamic_courses WHERE course_key = ?", (course_key,))
        existing = await cur.fetchone()
        if existing:
            await db.execute(
                """UPDATE dynamic_courses
                   SET title = ?, category = ?, author = ?, price = ?, duration = ?, target = ?,
                       features_text = ?, description = ?, photo_file_id = COALESCE(?, photo_file_id),
                       order_num = ?
                   WHERE id = ?""",
                (title, category, author, price, duration, target, features_text, description, photo_file_id, order_num, existing[0]),
            )
            c_id = existing[0]
        else:
            cur = await db.execute(
                """INSERT INTO dynamic_courses (course_key, title, category, author, price, duration, target, features_text, description, photo_file_id, order_num, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (course_key, title, category, author, price, duration, target, features_text, description, photo_file_id, order_num, now_iso),
            )
            c_id = cur.lastrowid
        await db.commit()
    return await get_dynamic_course_by_id(c_id)


async def update_dynamic_course_field(course_id: int, field: str, value: Any) -> None:
    """Kursning alohida maydonini yangilash."""
    allowed_fields = {"title", "category", "author", "price", "duration", "target", "features_text", "description", "photo_file_id", "order_num", "is_active"}
    if field not in allowed_fields:
        raise ValueError(f"Ruxsat berilmagan maydon: {field}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE dynamic_courses SET {field} = ? WHERE id = ?", (value, course_id))
        await db.commit()


async def delete_dynamic_course(course_id: int) -> None:
    """Kursni o'chirish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM dynamic_courses WHERE id = ?", (course_id,))
        await db.commit()


# =========================================================================
# REFERRAL SOVG'ALARI CRUD
# =========================================================================

async def get_all_referral_gifts(active_only: bool = True) -> list[dict]:
    """Barcha referral sovg'alarini tartib bilan olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM referral_gifts"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY required_friends ASC, order_num ASC, id ASC"
        cur = await db.execute(query)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_referral_gift(gift_key: str) -> Optional[dict]:
    """Bitta sovg'ani gift_key orqali olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM referral_gifts WHERE gift_key = ?", (gift_key,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_referral_gift_by_id(gift_id: int) -> Optional[dict]:
    """Bitta sovg'ani ID orqali olish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM referral_gifts WHERE id = ?", (gift_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def save_referral_gift(
    gift_key: str,
    title: str,
    required_friends: int,
    description: str = "",
    reward_type: str = "course",
    reward_content: str = "",
    photo_file_id: Optional[str] = None,
    order_num: int = 10,
) -> dict:
    """Yangi referral sovg'asini qo'shish yoki yangilash."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        now_iso = datetime.utcnow().isoformat()
        cur = await db.execute("SELECT id FROM referral_gifts WHERE gift_key = ?", (gift_key,))
        existing = await cur.fetchone()
        if existing:
            await db.execute(
                """UPDATE referral_gifts
                   SET title = ?, required_friends = ?, description = ?, reward_type = ?,
                       reward_content = ?, photo_file_id = COALESCE(?, photo_file_id),
                       order_num = ?
                   WHERE id = ?""",
                (title, required_friends, description, reward_type, reward_content, photo_file_id, order_num, existing[0]),
            )
            g_id = existing[0]
        else:
            cur = await db.execute(
                """INSERT INTO referral_gifts (gift_key, title, required_friends, description, reward_type, reward_content, photo_file_id, order_num, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (gift_key, title, required_friends, description, reward_type, reward_content, photo_file_id, order_num, now_iso),
            )
            g_id = cur.lastrowid
        await db.commit()
    return await get_referral_gift_by_id(g_id)


async def update_referral_gift_field(gift_id: int, field: str, value: Any) -> None:
    """Sovg'aning alohida maydonini yangilash."""
    allowed_fields = {"title", "required_friends", "description", "reward_type", "reward_content", "photo_file_id", "order_num", "is_active"}
    if field not in allowed_fields:
        raise ValueError(f"Ruxsat berilmagan maydon: {field}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE referral_gifts SET {field} = ? WHERE id = ?", (value, gift_id))
        await db.commit()


async def delete_referral_gift(gift_id: int) -> None:
    """Sovg'ani o'chirish."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM referral_gifts WHERE id = ?", (gift_id,))
        await db.commit()
