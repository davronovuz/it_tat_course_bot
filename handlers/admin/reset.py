"""
Admin Reset Handler
===================
Barcha user ma'lumotlarini tozalash (XAVFLI!)
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import dp, user_db


class ResetStates(StatesGroup):
    confirm = State()


# ============================================================
#                    RESET BUYRUG'I
# ============================================================

@dp.message_handler(commands=['reset_all_data_admin'])
async def reset_command(message: types.Message):
    """
    /reset_all_data - Barcha ma'lumotlarni tozalash
    """
    # Super admin tekshiruvi
    if not user_db.is_super_admin(message.from_user.id):
        await message.answer("❌ Faqat super admin ishlatishi mumkin!")
        return

    text = """
⚠️ <b>DIQQAT! XAVFLI AMAL!</b>

Siz barcha user ma'lumotlarini o'chirmoqchisiz:

🗑 O'chiriladigan:
- Barcha userlar (adminlardan tashqari)
- Barcha to'lovlar
- Barcha progress
- Barcha test natijalari
- Barcha sertifikatlar
- Barcha fikrlar
- Barcha referallar

✅ Saqlanadi:
- Kurslar
- Modullar
- Darslar
- Testlar va savollar
- Materiallar
- Adminlar

⚠️ <b>BU AMALNI QAYTARIB BO'LMAYDI!</b>

Tasdiqlash uchun <code>TASDIQLASH</code> so'zini yozing:
"""

    await message.answer(text)
    await ResetStates.confirm.set()


@dp.message_handler(state=ResetStates.confirm)
async def confirm_reset(message: types.Message, state: FSMContext):
    """
    Tasdiqlash
    """
    if message.text != "TASDIQLASH":
        await state.finish()
        await message.answer("❌ Bekor qilindi. To'g'ri yozilmadi.")
        return

    await message.answer("⏳ Tozalanmoqda...")

    # Reset qilish
    stats = user_db.reset_all_user_data()

    await state.finish()

    if stats.get('success'):
        text = f"""
✅ <b>Muvaffaqiyatli tozalandi!</b>

📊 <b>O'chirilgan ma'lumotlar:</b>

👥 Userlar: {stats.get('users', 0)} ta
💰 To'lovlar: {stats.get('payments', 0)} ta
📈 Progress: {stats.get('progress', 0)} ta
📝 Test natijalari: {stats.get('test_results', 0)} ta
🎓 Sertifikatlar: {stats.get('certificates', 0)} ta
💬 Fikrlar: {stats.get('feedbacks', 0)} ta
👥 Referallar: {stats.get('referrals', 0)} ta
🔑 Qo'lda dostuplar: {stats.get('manual_access', 0)} ta

✅ Darslar va testlar saqlandi!
"""
    else:
        text = f"❌ Xatolik: {stats.get('error', 'Nomalum')}"

    await message.answer(text)