"""
Admin Default Keyboards
=======================
Admin uchun barcha reply tugmalar
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ============================================================
#                    ASOSIY MENYU
# ============================================================
def admin_main_menu() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    keyboard.add(
        KeyboardButton("📚 Kurslar"),
        KeyboardButton("👥 Foydalanuvchilar")
    )
    keyboard.add(
        KeyboardButton("💰 To'lovlar"),
        KeyboardButton("📊 Hisobotlar")
    )
    keyboard.add(
        KeyboardButton("📢 Reklama")
    )
    keyboard.add(
        KeyboardButton("⚙️ Sozlamalar"),
        KeyboardButton("🏠 Bosh menyu")
    )

    return keyboard


def admin_back_button() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton("⬅️ Orqaga"))
    return keyboard


def admin_cancel_button() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def admin_skip_button() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("⏩ O'tkazib yuborish"),
        KeyboardButton("❌ Bekor qilish")
    )
    return keyboard


def admin_confirm_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("✅ Ha"),
        KeyboardButton("❌ Yo'q")
    )
    return keyboard


def admin_back_and_cancel() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("⬅️ Orqaga"),
        KeyboardButton("❌ Bekor qilish")
    )
    return keyboard


def remove_keyboard():
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()