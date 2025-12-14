"""
Referal Handler (YANGILANGAN)
"""

from aiogram import types
from aiogram.dispatcher.filters import Command, Text

from loader import dp, bot, user_db


@dp.message_handler(Text(equals="👥 Taklif qilish"))
@dp.message_handler(Command("referral"))
async def show_referral(message: types.Message):
    """Referal sahifasi va Statistika"""
    telegram_id = message.from_user.id

    # 1. Referal kod va havola
    ref_code = user_db.get_referral_code(telegram_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={ref_code}"

    # 2. Sozlamalarni olish
    cashback_percent = user_db.get_setting('referral_cashback', '10')

    # 3. Statistikani olish (Nechta odam chaqirdi, qancha pul ishladi)
    # get_referral_stats funksiyasi sizning UserDatabase da bor
    stats = user_db.get_referral_stats(telegram_id)

    total_invited = stats.get('total_referrals', 0)
    total_earned = stats.get('total_bonus', 0)

    earned_text = f"{total_earned:,.0f}".replace(",", " ")

    text = f"""
👥 <b>Hamkorlik Dasturi</b>

Do'stlaringizni taklif qiling va har bir xarid uchun <b>{cashback_percent}% cashback</b> oling!

🔗 <b>Sizning shaxsiy havolangiz:</b>
<code>{ref_link}</code>
(Ushbu havolani nusxalab, do'stlaringizga yuboring)

📊 <b>Sizning natijalaringiz:</b>
👥 Taklif qilinganlar: <b>{total_invited} ta</b>
💰 Ishlangan mablag': <b>{earned_text} so'm</b>

<i>💡 Adminlarimiz yig'ilgan mablag'ni kartangizga o'tkazib berishadi.</i>
"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        "📤 Do'stlarga ulashish",
        url=f"https://t.me/share/url?url={ref_link}&text=Salom! Men bu kursda o'qiyapman, senga ham tavsiya qilaman 👇"
    ))

    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(Text(equals="📚 Darslar"))
async def lessons_button(message: types.Message):
    """Darslar tugmasi"""
    user = user_db.get_user(message.from_user.id)

    if not user:
        await message.answer("❌ Avval /start bosing")
        return

    # Importni funksiya ichida qilish (cycle import oldini olish uchun)
    from handlers.users.start import show_lessons_list
    await show_lessons_list(message, user['id'])