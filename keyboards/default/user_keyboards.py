"""
User Default Keyboards
======================
Foydalanuvchi uchun barcha reply tugmalar
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ============================================================
#                    ASOSIY MENYU
# ============================================================

def main_menu() -> ReplyKeyboardMarkup:
    """Bosh menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("📚 Mening kurslarim"),
        KeyboardButton("🆓 Bepul darslar")
    )
    keyboard.add(
        KeyboardButton("🛒 Kurs sotib olish"),
        KeyboardButton("📊 Natijalarim")
    )
    keyboard.add(
        KeyboardButton("❓ Yordam")
    )

    return keyboard


# ============================================================
#                    RO'YXATDAN O'TISH
# ============================================================

def phone_request() -> ReplyKeyboardMarkup:
    """Telefon raqam so'rash"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    keyboard.add(
        KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
    )
    keyboard.add(
        KeyboardButton("❌ Bekor qilish")
    )

    return keyboard


def confirm_keyboard() -> ReplyKeyboardMarkup:
    """Tasdiqlash"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("✅ Ha"),
        KeyboardButton("❌ Yo'q")
    )

    return keyboard


# ============================================================
#                    NAVIGATSIYA
# ============================================================

def back_to_main() -> ReplyKeyboardMarkup:
    """Bosh menyuga qaytish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    keyboard.add(KeyboardButton("🏠 Bosh menyu"))

    return keyboard


def back_button() -> ReplyKeyboardMarkup:
    """Orqaga tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    keyboard.add(KeyboardButton("⬅️ Orqaga"))

    return keyboard


def cancel_button() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    keyboard.add(KeyboardButton("❌ Bekor qilish"))

    return keyboard


def skip_button() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("⏩ O'tkazib yuborish"),
        KeyboardButton("❌ Bekor qilish")
    )

    return keyboard


def back_and_cancel() -> ReplyKeyboardMarkup:
    """Orqaga va bekor qilish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("⬅️ Orqaga"),
        KeyboardButton("❌ Bekor qilish")
    )

    return keyboard


def back_and_main() -> ReplyKeyboardMarkup:
    """Orqaga va bosh menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("⬅️ Orqaga"),
        KeyboardButton("🏠 Bosh menyu")
    )

    return keyboard


# ============================================================
#                    TO'LOV
# ============================================================

def payment_cancel() -> ReplyKeyboardMarkup:
    """To'lovni bekor qilish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    keyboard.add(
        KeyboardButton("❌ Bekor qilish")
    )

    return keyboard


# ============================================================
#                    FIKR
# ============================================================

def feedback_skip() -> ReplyKeyboardMarkup:
    """Izohni o'tkazib yuborish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("⏩ O'tkazib yuborish"),
        KeyboardButton("❌ Bekor qilish")
    )

    return keyboard


# ============================================================
#                    PROFIL
# ============================================================

def profile_menu() -> ReplyKeyboardMarkup:
    """Profil menyusi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("👤 Ma'lumotlarim"),
        KeyboardButton("✏️ Tahrirlash")
    )
    keyboard.add(
        KeyboardButton("🏠 Bosh menyu")
    )

    return keyboard


def edit_profile_menu() -> ReplyKeyboardMarkup:
    """Profilni tahrirlash menyusi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("✏️ Ismni o'zgartirish"),
        KeyboardButton("📱 Telefonni o'zgartirish")
    )
    keyboard.add(
        KeyboardButton("⬅️ Orqaga")
    )

    return keyboard


# ============================================================
#                    ADMIN KIRISH
# ============================================================

def admin_access_button() -> ReplyKeyboardMarkup:
    """Admin panel kirish (faqat adminlar uchun ko'rinadi)"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("📚 Mening kurslarim"),
        KeyboardButton("🆓 Bepul darslar")
    )
    keyboard.add(
        KeyboardButton("🛒 Kurs sotib olish"),
        KeyboardButton("📊 Natijalarim")
    )
    keyboard.add(
        KeyboardButton("❓ Yordam"),
        KeyboardButton("👨‍💼 Admin panel")
    )

    return keyboard


# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def remove_keyboard():
    """Klaviaturani olib tashlash"""
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()


def yes_no() -> ReplyKeyboardMarkup:
    """Ha/Yo'q tugmalari"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("✅ Ha"),
        KeyboardButton("❌ Yo'q")
    )

    return keyboard


def contact_and_cancel() -> ReplyKeyboardMarkup:
    """Kontakt yuborish va bekor qilish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    keyboard.add(
        KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
    )
    keyboard.add(
        KeyboardButton("❌ Bekor qilish")
    )

    return keyboard