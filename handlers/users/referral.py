"""
Referal Handler (Sodda)
"""

from aiogram import types
from aiogram.dispatcher.filters import Text

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import referral_menu, referral_back


@dp.message_handler(Text(equals="👥 Do'stlarni taklif qilish"))
async def show_referral(message: types.Message):
    """Referal sahifasi"""
    telegram_id = message.from_user.id

    # Statistika
    stats = user_db.get_referral_stats(telegram_id)

    # Havola
    bot_info = await bot.get_me()
    ref_code = stats.get('referral_code', '')
    ref_link = f"https://t.me/{bot_info.username}?start={ref_code}"

    # Bonuslar
    reg_bonus = user_db.get_setting('referral_bonus_register', '5')
    pay_bonus = user_db.get_setting('referral_bonus_payment', '20')

    text = f"""
👥 <b>Do'stlarni taklif qiling!</b>

🔗 Sizning havolangiz:
<code>{ref_link}</code>

━━━━━━━━━━━━━━━━━━━━

🎁 <b>Bonuslar:</b>
- Ro'yxatdan o'tsa: <b>+{reg_bonus} ball</b>
- Kurs sotib olsa: <b>+{pay_bonus} ball</b>

━━━━━━━━━━━━━━━━━━━━

📊 <b>Sizning natijangiz:</b>
👤 Taklif qilganlar: <b>{stats.get('total_referrals', 0)}</b>
🎁 Olingan bonus: <b>{stats.get('total_bonus', 0)} ball</b>
"""

    await message.answer(text, reply_markup=referral_menu(ref_link, stats))


@dp.callback_query_handler(text="referral:menu")
async def referral_menu_callback(call: types.CallbackQuery):
    """Referal sahifasiga qaytish"""
    telegram_id = call.from_user.id

    stats = user_db.get_referral_stats(telegram_id)
    bot_info = await bot.get_me()
    ref_code = stats.get('referral_code', '')
    ref_link = f"https://t.me/{bot_info.username}?start={ref_code}"

    reg_bonus = user_db.get_setting('referral_bonus_register', '5')
    pay_bonus = user_db.get_setting('referral_bonus_payment', '20')

    text = f"""
👥 <b>Do'stlarni taklif qiling!</b>

🔗 Sizning havolangiz:
<code>{ref_link}</code>

━━━━━━━━━━━━━━━━━━━━

🎁 <b>Bonuslar:</b>
- Ro'yxatdan o'tsa: <b>+{reg_bonus} ball</b>
- Kurs sotib olsa: <b>+{pay_bonus} ball</b>

━━━━━━━━━━━━━━━━━━━━

📊 <b>Sizning natijangiz:</b>
👤 Taklif qilganlar: <b>{stats.get('total_referrals', 0)}</b>
🎁 Olingan bonus: <b>{stats.get('total_bonus', 0)} ball</b>
"""

    await call.message.edit_text(text, reply_markup=referral_menu(ref_link, stats))
    await call.answer()


@dp.callback_query_handler(text="referral:list")
async def referral_list(call: types.CallbackQuery):
    """Taklif qilganlar ro'yxati"""
    telegram_id = call.from_user.id
    referrals = user_db.get_user_referrals(telegram_id)

    if not referrals:
        await call.answer("Hali hech kim yo'q", show_alert=True)
        return

    text = "👥 <b>Taklif qilganlaringiz:</b>\n\n"

    for i, ref in enumerate(referrals[:20], 1):
        name = ref.get('full_name') or ref.get('username') or 'Foydalanuvchi'
        status = "💰" if ref.get('status') == 'paid' else "👤"
        bonus = ref.get('bonus_given', 0)

        text += f"{i}. {status} {name} — +{bonus} ball\n"

    await call.message.edit_text(text, reply_markup=referral_back())
    await call.answer()