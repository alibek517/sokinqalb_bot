import logging
from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

import database as db
from config import (
    BRAND_NAME,
    FOUNDER_NAME,
    REQUIRED_CHANNEL_ID,
    REQUIRED_CHANNEL_URL,
    REQUIRED_INSTAGRAM_URL,
    REQUIRED_YOUTUBE_URL,
    is_admin,
)
from keyboards import main_menu_kb, referral_hub_kb, subscription_required_kb
from subscription import check_channel_subscription, SUBSCRIPTION_REQUIRED_TEXT

router = Router(name="start")
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    f"Assalomu alaykum va {BRAND_NAME}ga xush kelibsiz! 🌿\n\n"
    f"Men — <b>{FOUNDER_NAME}ning shaxsiy yordamchisiman</b>. "
    f"Vazifam — sizga moliyaviy xavotirlar, munosabatlar, o'ziga ishonch, stress va ichki taranglikni dori-darmonsiz, bosqichma-bosqich yengishga yordam berish.\n\n"
    f"Markazimiz asoschisi {FOUNDER_NAME} — 12 yillik tajribaga ega psixoterapevt. Siz quyidagi imkoniyatlardan foydalanishingiz mumkin:\n\n"
    f"🧠 <b>Sokin Diagnostika</b> — kuchli va kuchsiz taraflaringizni aniqlab, shaxsiy yechim olish\n"
    f"💬 <b>Sokin Suhbat</b> — o'z his-tuyg'ularingiz va muammolaringiz haqida 24/7 jonli psixologik suhbat\n"
    f"📅 <b>Bugungi topshiriq</b> — shaxsiy mikro-vazifalar va monitoring\n"
    f"📝 <b>Sokin Qaydlar</b> — shaxsiy Sokinlik Reytingingiz va o'zgarishlar dinamikasi (1 oy oldin vs hozir)\n"
    f"📖 <b>Kurslar & Retreatlar</b> — barcha pullik va bepul mualliflik dasturlari\n"
    f"👥 <b>Do'stlarni taklif qilish</b> — do'stlaringizni taklif qilib, pullik kurslarni tekinga ochish\n"
    f"🌟 <b>Bizning yutuqlar</b> — natijalar, keyslar va ijtimoiy ishonch markazi\n\n"
    f"Boshlash uchun quyidagi menyudan foydalaning 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    # 1. Majburiy obunani tekshirish (/start bosilishi bilan)
    is_sub = await check_channel_subscription(bot, message.from_user.id, REQUIRED_CHANNEL_ID)
    if not is_sub:
        kb = subscription_required_kb(REQUIRED_CHANNEL_URL, REQUIRED_INSTAGRAM_URL, REQUIRED_YOUTUBE_URL)
        await message.answer(
            SUBSCRIPTION_REQUIRED_TEXT,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True,
        )
        return

    # Referral parametrini tekshirish (/start ref_12345678)
    args = message.text.split(maxsplit=1)
    referrer_tg_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_tg_id = int(args[1].replace("ref_", "").strip())
        except ValueError:
            pass

    user, is_new_user, referrer = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        referrer_tg_id=referrer_tg_id,
        return_details=True,
    )

    # Agar yangi foydalanuvchi do'stining linki orqali kirgan bo'lsa — taklif qiluvchiga xabar beramiz
    if is_new_user and referrer:
        try:
            ref_stats = await db.get_referral_stats(referrer["id"])
            c = ref_stats["count"]
            status_1 = "✅ OCHILDI!" if ref_stats["unlocked_1usd"] else f"⏳ Yana {ref_stats['needed_1usd']} ta do'st"
            status_10 = "✅ OCHILDI!" if ref_stats["unlocked_10usd"] else f"⏳ Yana {ref_stats['needed_10usd']} ta do'st"
            status_100 = "✅ OCHILDI!" if ref_stats["unlocked_100usd"] else f"⏳ Yana {ref_stats['needed_100usd']} ta do'st"

            ref_notify_text = (
                "🎉 <b>Ajoyib yangilik! Yangi do'stingiz qo'shildi!</b> 🌿\n\n"
                f"Sizning taklif havolangiz orqali <b>{message.from_user.full_name}</b> botga kirdi.\n\n"
                f"👥 <b>Jami taklif qilgan do'stlaringiz:</b> {c} ta\n\n"
                f"🎁 <b>Bepul ochiladigan sovg'alar:</b>\n"
                f"• 💎 1$ Kurs (1 ta do'st): {status_1}\n"
                f"• 🌟 10$ Kurs (3 ta do'st): {status_10}\n"
                f"• 👑 100$ VIP Kurs (10 ta do'st): {status_100}\n\n"
                "<i>Do'stlaringizni taklif qilishda davom eting va barcha kurslarni mutlaqo tekinga qo'lga kiriting!</i>"
            )
            await bot.send_message(
                referrer["telegram_id"],
                ref_notify_text,
                parse_mode="HTML",
                reply_markup=referral_hub_kb(),
            )
        except Exception:
            logger.exception("Referrer %s ga xabar yuborishda xatolik", referrer.get("telegram_id"))

    user_is_admin = is_admin(message.from_user.id)
    await message.answer(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin=user_is_admin),
    )

    if not user["diagnostic_done"]:
        await message.answer(
            "💡 <b>Tavsiya:</b> Hali dastlabki diagnostikadan o'tmadingiz. "
            "Sizga mos shaxsiy dastur tuzishimiz uchun diagnostikadan boshlashni maslahat beramiz 🙂",
            parse_mode="HTML",
        )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot) -> None:
    """Foydalanuvchi obunani tekshirish tugmasini bosganda."""
    user_id = callback.from_user.id
    is_sub = await check_channel_subscription(bot, user_id, REQUIRED_CHANNEL_ID)
    if is_sub:
        await callback.answer("🎉 Obunangiz muvaffaqiyatli tasdiqlandi! Rahmat.", show_alert=False)
        user_is_admin = is_admin(user_id)
        user = await db.get_user_by_telegram_id(user_id)
        if not user:
            user = await db.get_or_create_user(
                telegram_id=user_id,
                full_name=callback.from_user.full_name,
                username=callback.from_user.username,
            )
        try:
            await callback.message.delete()
        except Exception:
            pass

        await callback.message.answer(
            WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu_kb(is_admin=user_is_admin),
        )
        if not user.get("diagnostic_done"):
            await callback.message.answer(
                "💡 <b>Tavsiya:</b> Hali dastlabki diagnostikadan o'tmadingiz. "
                "Sizga mos shaxsiy dastur tuzishimiz uchun diagnostikadan boshlashni maslahat beramiz 🙂",
                parse_mode="HTML",
            )
    else:
        await callback.answer(
            "⚠️ Iltimos, avval sahifalarimizga a'zo bo'ling!",
            show_alert=True,
        )
