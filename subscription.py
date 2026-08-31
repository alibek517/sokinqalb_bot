"""SOKIN QALB — Majburiy Obuna (Telegram kanal va Instagram) tizimi."""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.types import TelegramObject, Message, CallbackQuery

from config import (
    REQUIRED_CHANNEL_ID,
    REQUIRED_CHANNEL_URL,
    REQUIRED_INSTAGRAM_URL,
    REQUIRED_YOUTUBE_URL,
    is_admin,
)
from keyboards import subscription_required_kb

logger = logging.getLogger(__name__)

SUBSCRIPTION_REQUIRED_TEXT = (
    "🌿 <b>SOKIN QALB botiga xush kelibsiz!</b>\n\n"
    "Botdan to'liq foydalanish uchun quyidagi rasmiy sahifalarimizga a'zo bo'ling va <b>«✅ Tasdiqlash»</b> tugmasini bosing 👇"
)


async def check_channel_subscription(bot: Bot, user_id: int, channel_id: str) -> bool:
    """Foydalanuvchi Telegram kanalga a'zo ekanligini tekshiradi."""
    if not channel_id or not channel_id.strip():
        return True

    clean_channel = channel_id.strip()
    try:
        member = await bot.get_chat_member(chat_id=clean_channel, user_id=user_id)
        if member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        ):
            return True
        if member.status == ChatMemberStatus.RESTRICTED and getattr(member, "is_member", False):
            return True
        return False
    except Exception as e:
        logger.warning("Majburiy obuna tekshirishda xatolik (kanal: %s, user: %s): %s", clean_channel, user_id, e)
        # Agar bot kanalda admin qilinmagan bo'lsa yoki kanal topilmasa:
        return False


class SubscriptionMiddleware(BaseMiddleware):
    """Barcha xabarlar va callback'larda majburiy obunani tekshiruvchi middleware."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Agar kanal sozlanmagan bo'lsa
        if not REQUIRED_CHANNEL_ID:
            return await handler(event, data)

        bot: Bot = data.get("bot")

        # Obunani tekshirish tugmasi bo'lsa, handlerga o'tkazamiz
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        is_sub = await check_channel_subscription(bot, user.id, REQUIRED_CHANNEL_ID)
        if is_sub:
            return await handler(event, data)

        # Foydalanuvchi obuna bo'lmagan — kirishni to'xtatib, tugmalarni chiqaramiz
        kb = subscription_required_kb(REQUIRED_CHANNEL_URL, REQUIRED_INSTAGRAM_URL, REQUIRED_YOUTUBE_URL)

        if isinstance(event, Message):
            await event.answer(
                SUBSCRIPTION_REQUIRED_TEXT,
                parse_mode="HTML",
                reply_markup=kb,
                disable_web_page_preview=True,
            )
            return None
        elif isinstance(event, CallbackQuery):
            await event.answer(
                "⚠️ Iltimos, avval sahifalarimizga a'zo bo'ling!",
                show_alert=True,
            )
            try:
                await event.message.edit_text(
                    SUBSCRIPTION_REQUIRED_TEXT,
                    parse_mode="HTML",
                    reply_markup=kb,
                    disable_web_page_preview=True,
                )
            except Exception:
                await event.message.answer(
                    SUBSCRIPTION_REQUIRED_TEXT,
                    parse_mode="HTML",
                    reply_markup=kb,
                    disable_web_page_preview=True,
                )
            return None

        return None


REVIEW_REQUIRED_TEXT = (
    "⚠️ <b>Haftalik Majburiy Qayd (Monitoring) Vaqti Keldi!</b> 🌿\n\n"
    "Siz o'tgan haftalik 4 ta hayotiy ustun (Moliya, Ruhiyat, Tana, Munosabatlar) tahlilidan o'tishingiz kerak.\n\n"
    "<i>Botning boshqa barcha imkoniyatlaridan to'liq foydalanishni davom ettirish uchun pastdagi tugmani bosing va 2 daqiqalik haftalik qayddan o'ting 👇</i>"
)


class ReviewEnforcementMiddleware(BaseMiddleware):
    """Haftalik qayd topshirilmagan bo'lsa boshqa funksiyalarni bloklovchi middleware."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        import database as db
        db_user = await db.get_user_by_telegram_id(user.id)
        if not db_user or not db_user.get("diagnostic_done"):
            return await handler(event, data)

        # Haftalik qayd talab qilinadimi?
        is_due = await db.is_weekly_review_due(db_user["id"])
        if not is_due:
            return await handler(event, data)

        # Agar foydalanuvchi haftalik qayd oqimida bo'lsa — ruxsat beramiz
        state = data.get("state")
        fsm_state = await state.get_state() if state else None
        if fsm_state and "FourPillarsFlow" in fsm_state:
            return await handler(event, data)

        from keyboards import review_required_kb

        if isinstance(event, CallbackQuery):
            if (
                event.data
                and (
                    event.data.startswith("start_four_pillars")
                    or event.data.startswith("fp_opt:")
                    or event.data == "sokin_qaydlar"
                    or event.data == "check_subscription"
                )
            ):
                return await handler(event, data)

            await event.answer("⚠️ Avval haftalik qayddan o'ting!", show_alert=True)
            try:
                await event.message.edit_text(
                    REVIEW_REQUIRED_TEXT,
                    parse_mode="HTML",
                    reply_markup=review_required_kb(),
                )
            except Exception:
                await event.message.answer(
                    REVIEW_REQUIRED_TEXT,
                    parse_mode="HTML",
                    reply_markup=review_required_kb(),
                )
            return None

        elif isinstance(event, Message):
            await event.answer(
                REVIEW_REQUIRED_TEXT,
                parse_mode="HTML",
                reply_markup=review_required_kb(),
            )
            return None

        return None
