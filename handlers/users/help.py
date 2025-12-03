"""
User Help Handler
=================
Yordam va bog'lanish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    help_topics,
    contact_options,
    back_button
)
from keyboards.default.user_keyboards import main_menu, cancel_button
from states.user_states import HelpStates


# ============================================================
#                    YORDAM MENYUSI
# ============================================================

@dp.callback_query_handler(text="user:help")
async def show_help_menu(call: types.CallbackQuery):
    """Yordam menyusi"""
    text = """
❓ <b>Yordam</b>

Quyidagi mavzulardan birini tanlang:

📚 <b>Kurslar</b> - Kurslar haqida
💰 <b>To'lov</b> - To'lov qilish tartibi
📝 <b>Testlar</b> - Testlar haqida
🎓 <b>Sertifikat</b> - Sertifikat olish
📞 <b>Bog'lanish</b> - Admin bilan bog'lanish

⬇️ Mavzuni tanlang:
"""

    await call.message.edit_text(text, reply_markup=help_topics())
    await call.answer()


# ============================================================
#                    YORDAM MAVZULARI
# ============================================================

@dp.callback_query_handler(text="user:help:courses")
async def help_courses(call: types.CallbackQuery):
    """Kurslar haqida yordam"""
    text = """
📚 <b>Kurslar haqida</b>

<b>Kurs nima?</b>
Kurs - bu ma'lum bir mavzu bo'yicha video darslar to'plami.

<b>Kurs tarkibi:</b>
• 📁 <b>Modullar</b> - Kurs bo'limlari
• 📹 <b>Darslar</b> - Video darslar
• 📎 <b>Materiallar</b> - Qo'shimcha fayllar (PDF, PPTX)
• 📝 <b>Testlar</b> - Bilimni tekshirish

<b>Qanday boshlash?</b>
1. "🛒 Kurs sotib olish" bo'limiga kiring
2. Kursni tanlang
3. To'lovni amalga oshiring
4. O'qishni boshlang!

<b>Bepul darslar:</b>
Ba'zi darslar bepul. Ularni "🆓 Bepul darslar" bo'limida ko'rishingiz mumkin.
"""

    await call.message.edit_text(text, reply_markup=back_button("user:help"))
    await call.answer()


@dp.callback_query_handler(text="user:help:payment")
async def help_payment(call: types.CallbackQuery):
    """To'lov haqida yordam"""
    text = """
💰 <b>To'lov qilish tartibi</b>

<b>1. Kursni tanlang</b>
"🛒 Kurs sotib olish" bo'limiga kirib, kerakli kursni tanlang.

<b>2. To'lovni amalga oshiring</b>
Ko'rsatilgan karta raqamiga pul o'tkazing:

💳 <code>8600 1234 5678 9012</code>
👤 Aliyev Ali

<b>3. Chekni yuboring</b>
To'lov chekini (screenshot) botga yuboring.

<b>4. Tasdiqlashni kuting</b>
Admin 1-2 soat ichida to'lovni tasdiqlaydi.

⚠️ <b>Muhim:</b>
• Chekda summa va sana ko'rinishi kerak
• Noto'g'ri summa yuborsangiz, rad etiladi
• Muammolar bo'lsa, admin bilan bog'laning
"""

    await call.message.edit_text(text, reply_markup=back_button("user:help"))
    await call.answer()


@dp.callback_query_handler(text="user:help:tests")
async def help_tests(call: types.CallbackQuery):
    """Testlar haqida yordam"""
    text = """
📝 <b>Testlar haqida</b>

<b>Test nima uchun kerak?</b>
Test bilimingizni tekshirish uchun. Testdan o'tmasangiz, keyingi darsga o'ta olmaysiz.

<b>Test qanday bo'ladi?</b>
• Har bir savolda 4 ta variant (A, B, C, D)
• Faqat bitta to'g'ri javob
• Qaytib o'zgartirish mumkin emas

<b>O'tish bali:</b>
Odatda 60% yoki undan yuqori ball kerak.

<b>Qayta topshirish:</b>
Testdan o'ta olmasangiz, qayta topshirishingiz mumkin.

<b>Ball tizimi:</b>
• Test natijasiga qarab ball olasiz
• Ballar umumiy hisobingizga qo'shiladi
• Ball sertifikat darajasiga ta'sir qiladi
"""

    await call.message.edit_text(text, reply_markup=back_button("user:help"))
    await call.answer()


@dp.callback_query_handler(text="user:help:certificate")
async def help_certificate(call: types.CallbackQuery):
    """Sertifikat haqida yordam"""
    text = """
🎓 <b>Sertifikat olish</b>

<b>Sertifikat olish uchun:</b>
1. Kursning barcha darslarini tugating
2. Barcha testlardan o'ting
3. "📊 Natijalarim" bo'limiga kirib sertifikat oling

<b>Sertifikat darajalari:</b>
🥇 <b>Oltin</b> - 90% va undan yuqori
🥈 <b>Kumush</b> - 75-89%
🥉 <b>Bronza</b> - 60-74%
📜 <b>Ishtirokchi</b> - 60% dan past

<b>Sertifikatda nima bo'ladi?</b>
• Sizning ismingiz
• Kurs nomi
• Daraja
• Sana
• Maxsus kod

<b>Sertifikatni yuklab olish:</b>
"📊 Natijalarim" → "🎓 Sertifikatlar" bo'limidan yuklab olishingiz mumkin.
"""

    await call.message.edit_text(text, reply_markup=back_button("user:help"))
    await call.answer()


# ============================================================
#                    BOG'LANISH
# ============================================================

@dp.callback_query_handler(text="user:help:contact")
async def help_contact(call: types.CallbackQuery):
    """Bog'lanish"""
    text = """
📞 <b>Bog'lanish</b>

Savollaringiz bo'lsa, admin bilan bog'laning.

<b>Qanday bog'lanish mumkin?</b>
• 💬 Bot orqali xabar yuborish
• 📞 Telefon qilish

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=contact_options())
    await call.answer()


@dp.callback_query_handler(text="user:contact:message")
async def send_message_to_admin(call: types.CallbackQuery, state: FSMContext):
    """Adminga xabar yuborish"""
    await call.message.edit_text(
        "💬 <b>Adminga xabar yuborish</b>\n\n"
        "Savolingizni yozing. Admin tez orada javob beradi.\n\n"
        "✍️ Xabaringizni yozing:"
    )

    await call.message.answer("✍️ Xabar yozing:", reply_markup=cancel_button())
    await HelpStates.send_message.set()
    await call.answer()


@dp.message_handler(state=HelpStates.send_message)
async def process_message_to_admin(message: types.Message, state: FSMContext):
    """Xabarni adminga yuborish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=main_menu())
        return

    user_message = message.text.strip()

    if len(user_message) < 5:
        await message.answer("❌ Xabar juda qisqa. Kamida 5 ta belgi kiriting.")
        return

    if len(user_message) > 1000:
        await message.answer("❌ Xabar juda uzun. 1000 belgidan oshmasin.")
        return

    user = user_db.get_user(message.from_user.id)

    # Adminlarga xabar yuborish
    admins = user_db.get_all_admins()

    admin_text = f"""
📩 <b>Yangi xabar!</b>

👤 <b>Foydalanuvchi:</b>
├ Ism: {user.get('full_name', 'Noma`lum')}
├ Telefon: {user.get('phone', 'Noma`lum')}
├ Username: @{message.from_user.username or 'yo`q'}
└ ID: <code>{message.from_user.id}</code>

💬 <b>Xabar:</b>
{user_message}
"""

    sent_count = 0
    for admin in admins:
        try:
            await bot.send_message(admin['telegram_id'], admin_text)
            sent_count += 1
        except Exception as e:
            print(f"Admin {admin['telegram_id']} ga xabar yuborib bo'lmadi: {e}")

    await state.finish()

    if sent_count > 0:
        await message.answer(
            "✅ <b>Xabaringiz yuborildi!</b>\n\n"
            "Admin tez orada javob beradi.\n"
            "Sabr qiling! 🙏",
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "❌ Xabar yuborishda xatolik. Keyinroq urinib ko'ring.",
            reply_markup=main_menu()
        )


@dp.callback_query_handler(text="user:contact:phone")
async def show_contact_phone(call: types.CallbackQuery):
    """Telefon raqamini ko'rsatish"""
    text = """
📞 <b>Telefon orqali bog'lanish</b>

Qo'ng'iroq qilish uchun:

📱 <code>+998 90 123 45 67</code>

⏰ <b>Ish vaqti:</b>
Dushanba - Juma: 9:00 - 18:00
Shanba: 10:00 - 15:00
Yakshanba: Dam olish kuni
"""

    await call.message.edit_text(text, reply_markup=back_button("user:help:contact"))
    await call.answer()


# ============================================================
#                    FAQ (KO'P BERILADIGAN SAVOLLAR)
# ============================================================

@dp.callback_query_handler(text="user:faq")
async def show_faq(call: types.CallbackQuery):
    """Ko'p beriladigan savollar"""
    text = """
❓ <b>Ko'p beriladigan savollar</b>

<b>❓ Kursni qancha muddatda tugatishim kerak?</b>
Muddat cheklanmagan. O'zingizga qulay vaqtda o'qishingiz mumkin.

<b>❓ Testdan o'ta olmasam nima bo'ladi?</b>
Qayta topshirishingiz mumkin. Urinishlar soni cheklanmagan.

<b>❓ Videolarni yuklab olsam bo'ladimi?</b>
Yo'q, videolar faqat bot orqali ko'riladi.

<b>❓ Pul qaytariladi?</b>
To'lovdan keyin pul qaytarilmaydi.

<b>❓ Bir necha kurs sotib olsam bo'ladimi?</b>
Ha, istalgancha kurs sotib olishingiz mumkin.

<b>❓ Sertifikat haqiqiymi?</b>
Ha, maxsus kod bilan tekshirish mumkin.
"""

    await call.message.edit_text(text, reply_markup=back_button("user:help"))
    await call.answer()