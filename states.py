"""SOKIN QALB — FSM holatlari (aiogram StatesGroup)."""
from aiogram.fsm.state import StatesGroup, State


class DiagnosticFlow(StatesGroup):
    in_progress = State()


class CheckinFlow(StatesGroup):
    in_progress = State()
    waiting_custom_text = State()


class FourPillarsFlow(StatesGroup):
    in_progress = State()
    waiting_custom_text = State()


class AIChatFlow(StatesGroup):
    chatting = State()


class SOSFlow(StatesGroup):
    waiting_custom_text = State()


class AdminBroadcast(StatesGroup):
    waiting_content = State()
    waiting_confirm = State()


class AdminUserSearch(StatesGroup):
    waiting_query = State()


class AdminDirectMessage(StatesGroup):
    waiting_text = State()


class AdminAIPost(StatesGroup):
    waiting_topic = State()


class LiveChatFlow(StatesGroup):
    waiting_user_message = State()


class AdminReplyToUser(StatesGroup):
    waiting_admin_reply = State()


class CoursePaymentFlow(StatesGroup):
    waiting_receipt = State()


class AdminCourseManagement(StatesGroup):
    waiting_lesson_title = State()
    waiting_lesson_description = State()
    waiting_media_upload = State()


class AdminTeamManagement(StatesGroup):
    waiting_name = State()
    waiting_title_exp = State()
    waiting_directions = State()
    waiting_methodology = State()
    waiting_achievements = State()
    waiting_photo = State()
    waiting_edit_text = State()


class AdminGiftManagement(StatesGroup):
    waiting_title = State()
    waiting_required_friends = State()
    waiting_description = State()
    waiting_content = State()
    waiting_photo = State()
    waiting_edit_text = State()


class AdminCourseEdit(StatesGroup):
    waiting_title = State()
    waiting_price = State()
    waiting_duration = State()
    waiting_description = State()
    waiting_features = State()
    waiting_photo = State()
    waiting_edit_text = State()
