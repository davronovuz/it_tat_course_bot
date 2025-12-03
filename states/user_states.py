"""
User States - FSM holatlari
===========================
Foydalanuvchi uchun barcha state'lar
"""

from aiogram.dispatcher.filters.state import State, StatesGroup


# ============================================================
#                    RO'YXATDAN O'TISH
# ============================================================

class RegistrationStates(StatesGroup):
    """Ro'yxatdan o'tish holatlari"""

    full_name = State()  # To'liq ismni kiritish
    phone = State()  # Telefon raqamni kiritish
    confirm = State()  # Tasdiqlash


# ============================================================
#                    KURS SOTIB OLISH
# ============================================================

class PurchaseStates(StatesGroup):
    """Kurs sotib olish holatlari"""

    select_method = State()  # To'lov usulini tanlash
    send_receipt = State()  # Chek yuborish
    confirm = State()  # Tasdiqlash


# ============================================================
#                    TEST YECHISH
# ============================================================

class TestStates(StatesGroup):
    """Test yechish holatlari"""

    in_progress = State()  # Test jarayonida
    answering = State()  # Javob berish
    finished = State()  # Test tugadi


# ============================================================
#                    FIKR QOLDIRISH
# ============================================================

class FeedbackStates(StatesGroup):
    """Fikr qoldirish holatlari"""

    rating = State()  # Baho berish (1-5)
    comment = State()  # Izoh yozish
    confirm = State()  # Tasdiqlash


# ============================================================
#                    YORDAM / BOG'LANISH
# ============================================================

class HelpStates(StatesGroup):
    """Yordam holatlari"""

    send_message = State()  # Adminga xabar yuborish


# ============================================================
#                    PROFIL TAHRIRLASH
# ============================================================

class ProfileStates(StatesGroup):
    """Profil tahrirlash holatlari"""

    edit_name = State()  # Ismni tahrirlash
    edit_phone = State()  # Telefonni tahrirlash