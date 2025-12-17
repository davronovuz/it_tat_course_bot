"""
Admin States - FSM holatlari
============================
Admin panel uchun barcha state'lar
"""

from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminMainState(StatesGroup):
    """Admin asosiy holatlari"""
    menu = State()  # Admin menyusida


# ============================================================
#                    KURS STATES
# ============================================================

class CourseStates(StatesGroup):
    """Kurs qo'shish/tahrirlash holatlari"""

    # Kurs qo'shish
    add_name = State()  # Kurs nomini kiritish
    add_description = State()  # Kurs tavsifini kiritish
    add_price = State()  # Kurs narxini kiritish
    add_confirm = State()  # Tasdiqlash

    # Kurs tahrirlash
    edit_name = State()  # Nomni tahrirlash
    edit_description = State()  # Tavsifni tahrirlash
    edit_price = State()  # Narxni tahrirlash
    edit_order = State()  # Tartibni tahrirlash


# ============================================================
#                    MODUL STATES
# ============================================================

class ModuleStates(StatesGroup):
    """Modul qo'shish/tahrirlash holatlari"""

    # Modul qo'shish
    add_name = State()  # Modul nomini kiritish
    add_description = State()  # Modul tavsifini kiritish
    add_confirm = State()  # Tasdiqlash

    # Modul tahrirlash
    edit_name = State()  # Nomni tahrirlash
    edit_description = State()  # Tavsifni tahrirlash
    edit_order = State()  # Tartibni tahrirlash


# ============================================================
#                    DARS STATES
# ============================================================

class LessonStates(StatesGroup):
    """Dars qo'shish/tahrirlash holatlari"""

    # Dars qo'shish
    add_name = State()  # Dars nomini kiritish
    add_description = State()  # Dars tavsifini kiritish
    add_video = State()  # Video yuklash
    add_is_free = State()  # Bepul/Pullik tanlash
    add_confirm = State()  # Tasdiqlash

    # Dars tahrirlash
    edit_name = State()  # Nomni tahrirlash
    edit_description = State()  # Tavsifni tahrirlash
    edit_video = State()  # Videoni tahrirlash
    edit_order = State()  # Tartibni tahrirlash


# ============================================================
#                    MATERIAL STATES
# ============================================================

class MaterialStates(StatesGroup):
    """Material qo'shish/tahrirlash holatlari"""

    # Material qo'shish
    add_name = State()  # Material nomini kiritish
    add_file = State()  # Fayl yuklash
    add_description = State()  # Tavsif kiritish
    add_confirm = State()  # Tasdiqlash

    # Material tahrirlash
    edit_name = State()  # Nomni tahrirlash
    edit_description = State()  # Tavsifni tahrirlash


# ============================================================
#                    TEST STATES
# ============================================================

class TestStates(StatesGroup):
    """Test qo'shish/tahrirlash holatlari"""

    # Test yaratish
    create_name = State()  # Test nomini kiritish
    create_passing_score = State()  # O'tish balini kiritish

    # Test sozlamalari
    edit_passing_score = State()  # O'tish balini tahrirlash
    edit_time_limit = State()  # Vaqt chegarasini tahrirlash


class QuestionStates(StatesGroup):
    """Savol qo'shish/tahrirlash holatlari"""

    # Savol qo'shish (qo'lda)
    add_question = State()  # Savol matnini kiritish
    add_option_a = State()  # A variantini kiritish
    add_option_b = State()  # B variantini kiritish
    add_option_c = State()  # C variantini kiritish
    add_option_d = State()  # D variantini kiritish
    add_correct = State()  # To'g'ri javobni tanlash
    add_more = State()  # Yana savol qo'shish

    # Savol tahrirlash
    edit_question = State()  # Savol matnini tahrirlash
    edit_option_a = State()  # A variantini tahrirlash
    edit_option_b = State()  # B variantini tahrirlash
    edit_option_c = State()  # C variantini tahrirlash
    edit_option_d = State()  # D variantini tahrirlash
    edit_correct = State()  # To'g'ri javobni tahrirlash

    # Excel yuklash
    upload_excel = State()  # Excel faylni yuklash


# ============================================================
#                    FOYDALANUVCHI STATES
# ============================================================

class UserManageStates(StatesGroup):
    """Foydalanuvchi boshqaruvi holatlari"""

    # Qidirish
    search = State()  # Foydalanuvchi qidirish

    # Dostup berish
    access_reason = State()  # Dostup sababi

    # Xabar yuborish
    send_message = State()  # Xabar matni

    # Ball qo'shish
    add_score = State()  # Ball miqdori


# ============================================================
#                    TO'LOV STATES
# ============================================================

class PaymentStates(StatesGroup):
    """To'lov boshqaruvi holatlari"""

    # Rad etish
    reject_reason = State()  # Rad etish sababi


# ============================================================
#                    HISOBOT STATES
# ============================================================

class ReportStates(StatesGroup):
    """Hisobot holatlari"""

    # Maxsus davr
    custom_date_start = State()  # Boshlanish sanasi
    custom_date_end = State()  # Tugash sanasi


# ============================================================
#                    SOZLAMALAR STATES
# ============================================================

class SettingsStates(StatesGroup):
    feedback_score = State()
    test_passing_score = State()
    cert_gold = State()
    cert_silver = State()
    cert_bronze = State()
    card_number = State()
    card_holder = State()
    bot_name = State()
    bot_description = State()
    reminder_days = State()
    default_duration = State()


class AdminManageStates(StatesGroup):
    """Admin boshqaruvi holatlari"""

    # Admin qo'shish
    add_telegram_id = State()  # Admin telegram ID
    add_name = State()  # Admin ismi
    add_is_super = State()  # Super admin?


# ============================================================
#                    BROADCAST STATES
# ============================================================

class BroadcastStates(StatesGroup):
    """Ommaviy xabar holatlari (Mukammal tizim uchun)"""

    message_text = State()   # 1. Xabar matni va media
    buttons = State()        # 2. Tugmalar (URL)
    time = State()           # 3. Vaqtni tanlash (Hozir/Keyin)
    custom_time = State()    # 4. Aniq vaqtni kiritish (HH:MM)
    confirm = State()        # 5. Tasdiqlash