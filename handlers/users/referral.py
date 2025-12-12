"""
Referal Handler
"""

from aiogram import types
from aiogram.dispatcher.filters import Command, Text

from loader import dp, bot, user_db


@dp.message_handler(Text(equals="👥 Taklif qilish"))
@dp.message_handler(Command("referral"))
async def show_referral(message: types.Message):
    """Referal sahifasi"""
    telegram_id = message.from_user.id

    ref_code = user_db.get_referral_code(telegram_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={ref_code}"

    cashback = user_db.get_setting('referral_cashback', '10')

    text = f"""
👥 <b>Do'stlaringizni taklif qiling va pul ishlang!</b>

Quyidagi havolani do'stlaringizga yuboring.
Do'stingiz kurs sotib olsa — <b>sizga {cashback}% qaytariladi!</b>

🔗 <b>Sizning havolangiz:</b>
<code>{ref_link}</code>

👆 Bosing va nusxalang!

💡 <i>Masalan: Kurs 500,000 so'm bo'lsa, sizga {int(500000 * int(cashback) / 100):,} so'm qaytariladi!</i>
"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        "📤 Do'stlarga yuborish",
        url=f"https://t.me/share/url?url={ref_link}&text=Ajoyib kurslarni ko'ring!"
    ))

    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(Text(equals="📚 Darslar"))
async def lessons_button(message: types.Message):
    """Darslar tugmasi"""
    user = user_db.get_user(message.from_user.id)

    if not user:
        await message.answer("❌ Avval /start bosing")
        return

    from handlers.users.start import show_lessons_list
    await show_lessons_list(message, user['id'])