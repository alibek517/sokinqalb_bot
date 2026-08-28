from aiogram import Dispatcher

from . import start, admin, live_chat, ai_chat, sos, diagnostics, checkin, tasks, content, menu


def register_all_handlers(dp: Dispatcher) -> None:
    dp.include_router(admin.router)
    dp.include_router(live_chat.router)
    dp.include_router(start.router)
    dp.include_router(ai_chat.router)
    dp.include_router(sos.router)
    dp.include_router(diagnostics.router)
    dp.include_router(checkin.router)
    dp.include_router(tasks.router)
    dp.include_router(content.router)
    dp.include_router(menu.router)
