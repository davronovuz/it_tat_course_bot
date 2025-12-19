"""
User Default Keyboards (MINIMAL)
================================
Faqat zarur bo'lganda reply tugmalar
Asosan hammasi INLINE orqali
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def user_main_menu() -> ReplyKeyboardMarkup:
    """
    Asosiy menyu - kursga kirgan userlar uchun
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("📞 Admin bilan aloqa"),
        KeyboardButton("👥 Taklif qilish")
    )


    keyboard.add(
        KeyboardButton("📢 Telegram kanal"),
        KeyboardButton("📥 Dars rejasi")
    )

    return keyboard

def main_menu() -> ReplyKeyboardMarkup:
    """
    Asosiy menyu - ro'yxatdan o'tgan userlar uchun
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("📚 Darslar"))
    keyboard.add(KeyboardButton("👥 Do'stlarni taklif qilish"))
    keyboard.add(KeyboardButton("📊 Mening statistikam"))
    return keyboard

def phone_request() -> ReplyKeyboardMarkup:
    """
    Telefon raqam so'rash - bu kerak chunki
    request_contact faqat reply button orqali ishlaydi
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def cancel_button() -> ReplyKeyboardMarkup:
    """Bekor qilish (chek yuborishda)"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def remove_keyboard() -> ReplyKeyboardRemove:
    """Klaviaturani olib tashlash"""
    return ReplyKeyboardRemove()


# Admin panel uchun (faqat adminlarga ko'rinadi)
def admin_button() -> ReplyKeyboardMarkup:
    """Admin panel tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton("👨‍💼 Admin panel"))
    return keyboard