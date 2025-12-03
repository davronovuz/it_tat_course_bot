"""
User Start Handler
==================
/start buyrug'i va ro'yxatdan o'tish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text

from loader import dp, user_db
from keyboards.default.user_keyboards import (
    main_menu,
    phone_request,
    back_to_main,
    confirm_keyboard
)
from keyboards.inline.user_keyboards import (
    courses_list,
    main_menu_inline
)
from states.user_states import RegistrationStates


# ============================================================
#                    /START BUYRUG'I
# ============================================================

@dp.message_handler(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """/start buyrug'i"""
    await state.finish()

    telegram_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Foydalanuvchi mavjudligini tekshirish
    if user_db.user_exists(telegram_id):
        # Mavjud foydalanuvchi
        user = user_db.get_user(telegram_id)

        # So'nggi faollikni yangilash
        user_db.update_user(telegram_id, username=username)

        text = f"""
👋 <b>Xush kelibsiz, {user.get('full_name') or full_name}!</b>

📚 O'quv markazimizga qaytganingizdan xursandmiz!

Quyidagi menyudan kerakli bo'limni tanlang:
"""

        await message.answer(text, reply_markup=main_menu())

    else:
        # Yangi foydalanuvchi - ro'yxatdan o'tkazish
        text = f"""
👋 <b>Assalomu alaykum, {full_name}!</b>

📚 O'quv markazimizga xush kelibsiz!

Davom etish uchun ro'yxatdan o'ting.

📝 Iltimos, to'liq ismingizni kiriting:

<i>Masalan: Aliyev Ali</i>
"""

        # Foydalanuvchini bazaga qo'shish (asosiy ma'lumotlar bilan)
        user_db.add_user(telegram_id, username=username, full_name=full_name)

        await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        await RegistrationStates.full_name.set()


# ============================================================
#                    RO'YXATDAN O'TISH
# ============================================================

@dp.message_handler(state=RegistrationStates.full_name)
async def registration_full_name(message: types.Message, state: FSMContext):
    """To'liq ismni qabul qilish"""
    full_name = message.text.strip()

    # Validatsiya
    if len(full_name) < 3:
        await message.answer(
            "❌ Ism juda qisqa. Kamida 3 ta belgi kiriting.\n\n"
            "📝 To'liq ismingizni kiriting:"
        )
        return

    if len(full_name) > 100:
        await message.answer(
            "❌ Ism juda uzun. 100 ta belgidan oshmasin.\n\n"
            "📝 To'liq ismingizni kiriting:"
        )
        return

    # Faqat harflar va bo'shliq
    if not all(c.isalpha() or c.isspace() or c == "'" for c in full_name):
        await message.answer(
            "❌ Ismda faqat harflar bo'lishi kerak.\n\n"
            "📝 To'liq ismingizni kiriting:"
        )
        return

    await state.update_data(full_name=full_name)

    await message.answer(
        f"✅ Rahmat, <b>{full_name}</b>!\n\n"
        f"📱 Endi telefon raqamingizni yuboring.\n\n"
        f"Quyidagi tugmani bosing:",
        reply_markup=phone_request()
    )

    await RegistrationStates.phone.set()


@dp.message_handler(state=RegistrationStates.phone, content_types=['contact'])
async def registration_phone_contact(message: types.Message, state: FSMContext):
    """Telefon raqamni contact orqali qabul qilish"""
    phone = message.contact.phone_number

    # +998 bilan boshlanishini tekshirish
    if not phone.startswith('+'):
        phone = '+' + phone

    await state.update_data(phone=phone)

    data = await state.get_data()

    text = f"""
📋 <b>Ma'lumotlaringizni tasdiqlang:</b>

👤 Ism: <b>{data['full_name']}</b>
📱 Telefon: <b>{phone}</b>

✅ To'g'rimi?
"""

    await message.answer(text, reply_markup=confirm_keyboard())
    await RegistrationStates.confirm.set()


@dp.message_handler(state=RegistrationStates.phone)
async def registration_phone_text(message: types.Message, state: FSMContext):
    """Telefon raqamni matn orqali qabul qilish"""
    phone = message.text.strip()

    # Telefon raqamni tozalash
    phone_clean = ''.join(filter(str.isdigit, phone))

    # Validatsiya
    if len(phone_clean) < 9:
        await message.answer(
            "❌ Telefon raqam noto'g'ri.\n\n"
            "📱 Quyidagi tugmani bosing yoki raqamni kiriting:",
            reply_markup=phone_request()
        )
        return

    # +998 qo'shish
    if phone_clean.startswith('998'):
        phone = '+' + phone_clean
    elif phone_clean.startswith('9') and len(phone_clean) == 9:
        phone = '+998' + phone_clean
    else:
        phone = '+998' + phone_clean[-9:]

    await state.update_data(phone=phone)

    data = await state.get_data()

    text = f"""
📋 <b>Ma'lumotlaringizni tasdiqlang:</b>

👤 Ism: <b>{data['full_name']}</b>
📱 Telefon: <b>{phone}</b>

✅ To'g'rimi?
"""

    await message.answer(text, reply_markup=confirm_keyboard())
    await RegistrationStates.confirm.set()


@dp.message_handler(state=RegistrationStates.confirm)
async def registration_confirm(message: types.Message, state: FSMContext):
    """Ro'yxatdan o'tishni tasdiqlash"""

    if message.text == "✅ Ha":
        data = await state.get_data()

        # Foydalanuvchi ma'lumotlarini yangilash
        user_db.update_user(
            message.from_user.id,
            full_name=data['full_name'],
            phone=data['phone']
        )

        await state.finish()

        text = f"""
🎉 <b>Tabriklaymiz!</b>

Siz muvaffaqiyatli ro'yxatdan o'tdingiz!

👤 {data['full_name']}
📱 {data['phone']}

📚 Endi kurslarimizni ko'rishingiz mumkin.
"""

        await message.answer(text, reply_markup=main_menu())

    elif message.text == "❌ Yo'q":
        await state.finish()

        await message.answer(
            "📝 Qaytadan ro'yxatdan o'tish uchun ismingizni kiriting:",
            reply_markup=types.ReplyKeyboardRemove()
        )

        await RegistrationStates.full_name.set()

    else:
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")


# ============================================================
#                    BOSH MENYU HANDLERLARI
# ============================================================

@dp.message_handler(Text(equals="🏠 Bosh menyu"))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Bosh menyuga qaytish"""
    await state.finish()

    user = user_db.get_user(message.from_user.id)

    if user:
        text = f"""
👋 <b>{user.get('full_name', 'Foydalanuvchi')}</b>

📚 Quyidagi menyudan tanlang:
"""
    else:
        text = "📚 Quyidagi menyudan tanlang:"

    await message.answer(text, reply_markup=main_menu())


@dp.message_handler(Text(equals="⬅️ Orqaga"))
async def back_button(message: types.Message, state: FSMContext):
    """Orqaga tugmasi"""
    current_state = await state.get_state()

    if current_state:
        await state.finish()

    await message.answer("🏠 Bosh menyu", reply_markup=main_menu())


@dp.message_handler(Text(equals="❌ Bekor qilish"), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    """Bekor qilish"""
    current_state = await state.get_state()

    if current_state is None:
        return

    await state.finish()
    await message.answer("❌ Bekor qilindi", reply_markup=main_menu())


# ============================================================
#                    MENING KURSLARIM
# ============================================================

@dp.message_handler(Text(equals="📚 Mening kurslarim"))
async def my_courses(message: types.Message):
    """Mening kurslarim"""
    telegram_id = message.from_user.id

    # Foydalanuvchi dostup olgan kurslar
    user_id = user_db.get_user_id(telegram_id)

    if not user_id:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start")
        return

    # Dostup bor kurslarni olish
    result = user_db.execute(
        """SELECT DISTINCT c.id, c.name, c.description, c.price
           FROM Courses c
           LEFT JOIN Payments p ON c.id = p.course_id AND p.user_id = ? AND p.status = 'approved'
           LEFT JOIN ManualAccess ma ON c.id = ma.course_id AND ma.user_id = ? 
               AND (ma.expires_at IS NULL OR ma.expires_at > datetime('now'))
           WHERE c.is_active = TRUE 
               AND (p.id IS NOT NULL OR ma.id IS NOT NULL)
           ORDER BY c.order_num""",
        parameters=(user_id, user_id),
        fetchall=True
    )

    if not result:
        text = """
📚 <b>Mening kurslarim</b>

📭 Sizda hozircha kurslar yo'q.

Kurs sotib olish uchun "🛒 Kurs sotib olish" tugmasini bosing.
Yoki bepul darslarni ko'ring.
"""
        await message.answer(text, reply_markup=main_menu())
        return

    courses = []
    for row in result:
        courses.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': row[3],
            'has_access': True
        })

    text = f"""
📚 <b>Mening kurslarim</b>

Sizda {len(courses)} ta kurs mavjud.

⬇️ Davom etish uchun kursni tanlang:
"""

    await message.answer(text, reply_markup=courses_list(courses, user_id))


# ============================================================
#                    BEPUL DARSLAR
# ============================================================

@dp.message_handler(Text(equals="🆓 Bepul darslar"))
async def free_lessons(message: types.Message):
    """Bepul darslar"""

    # Bepul darslarni olish
    result = user_db.execute(
        """SELECT l.id, l.name, m.name as module_name, c.name as course_name
           FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE l.is_free = TRUE AND l.is_active = TRUE 
               AND m.is_active = TRUE AND c.is_active = TRUE
           ORDER BY c.order_num, m.order_num, l.order_num""",
        fetchall=True
    )

    if not result:
        text = """
🆓 <b>Bepul darslar</b>

📭 Hozircha bepul darslar yo'q.
"""
        await message.answer(text, reply_markup=main_menu())
        return

    lessons = []
    for row in result:
        lessons.append({
            'id': row[0],
            'name': row[1],
            'module_name': row[2],
            'course_name': row[3]
        })

    text = f"""
🆓 <b>Bepul darslar</b>

{len(lessons)} ta bepul dars mavjud.

⬇️ Darsni tanlang:
"""

    from keyboards.inline.user_keyboards import free_lessons_list
    await message.answer(text, reply_markup=free_lessons_list(lessons))


# ============================================================
#                    KURS SOTIB OLISH
# ============================================================

@dp.message_handler(Text(equals="🛒 Kurs sotib olish"))
async def buy_course(message: types.Message):
    """Kurs sotib olish"""
    telegram_id = message.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # Barcha faol kurslar
    courses = user_db.get_all_courses(active_only=True)

    if not courses:
        text = """
🛒 <b>Kurs sotib olish</b>

📭 Hozircha sotuvda kurslar yo'q.
"""
        await message.answer(text, reply_markup=main_menu())
        return

    # Har bir kurs uchun dostup tekshirish
    courses_with_access = []
    for course in courses:
        has_access = user_db.has_course_access(user_id, course['id']) if user_id else False
        courses_with_access.append({
            **course,
            'has_access': has_access
        })

    text = f"""
🛒 <b>Kurs sotib olish</b>

{len(courses)} ta kurs mavjud.

✅ - Sizda mavjud
🔒 - Sotib olish mumkin

⬇️ Kursni tanlang:
"""

    await message.answer(text, reply_markup=courses_list(courses_with_access, user_id))


# ============================================================
#                    NATIJALARIM
# ============================================================

@dp.message_handler(Text(equals="📊 Natijalarim"))
async def my_results(message: types.Message):
    """Natijalarim"""
    telegram_id = message.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start")
        return

    user_id = user['id']

    # Umumiy statistika
    total_score = user.get('total_score', 0)

    # Test natijalari
    test_results = user_db.execute(
        """SELECT COUNT(*), SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END)
           FROM TestResults WHERE user_id = ?""",
        parameters=(user_id,),
        fetchone=True
    )
    total_tests = test_results[0] if test_results else 0
    passed_tests = test_results[1] if test_results and test_results[1] else 0

    # Tugatilgan darslar
    completed_lessons = user_db.execute(
        """SELECT COUNT(*) FROM UserProgress 
           WHERE user_id = ? AND status = 'completed'""",
        parameters=(user_id,),
        fetchone=True
    )
    completed_count = completed_lessons[0] if completed_lessons else 0

    # Sertifikatlar
    certificates = user_db.execute(
        """SELECT COUNT(*) FROM Certificates WHERE user_id = ?""",
        parameters=(user_id,),
        fetchone=True
    )
    cert_count = certificates[0] if certificates else 0

    text = f"""
📊 <b>Mening natijalarim</b>

👤 {user.get('full_name', 'Foydalanuvchi')}

🏆 <b>Umumiy statistika:</b>
├ ⭐️ Jami ball: <b>{total_score}</b>
├ 📹 Tugatilgan darslar: <b>{completed_count}</b>
├ 📝 Yechilgan testlar: <b>{total_tests}</b>
├ ✅ Muvaffaqiyatli: <b>{passed_tests}</b>
└ 🎓 Sertifikatlar: <b>{cert_count}</b>

⬇️ Batafsil ko'rish uchun tanlang:
"""

    from keyboards.inline.user_keyboards import my_results_menu
    await message.answer(text, reply_markup=my_results_menu())


# ============================================================
#                    YORDAM
# ============================================================

@dp.message_handler(Text(equals="❓ Yordam"))
async def help_menu(message: types.Message):
    """Yordam"""
    text = """
❓ <b>Yordam</b>

📚 <b>Qanday ishlaydi?</b>
1. Kursni sotib oling yoki bepul darslarni ko'ring
2. Video darslarni ko'ring
3. Testlarni yeching
4. Fikr qoldiring
5. Sertifikat oling

💰 <b>To'lov qanday amalga oshiriladi?</b>
• Kursni tanlang
• Karta ma'lumotlariga pul o'tkazing
• Chekni yuboring
• Admin tasdiqlaydi

📝 <b>Testlar haqida:</b>
• Har bir darsda test bo'lishi mumkin
• Test topshirmasangiz keyingi darsga o'ta olmaysiz
• Qayta topshirish mumkin

🎓 <b>Sertifikat:</b>
• Kursni tugatgandan so'ng sertifikat olasiz
• Sertifikat darajasi ballingizga bog'liq

⬇️ Qo'shimcha yordam:
"""

    from keyboards.inline.user_keyboards import help_menu as help_kb
    await message.answer(text, reply_markup=help_kb())


# ============================================================
#                    CALLBACK: CLOSE
# ============================================================

@dp.callback_query_handler(text="user:close")
async def callback_close(call: types.CallbackQuery, state: FSMContext):
    """Xabarni o'chirish"""
    await state.finish()
    await call.message.delete()
    await call.answer()


@dp.callback_query_handler(text="user:main")
async def callback_main_menu(call: types.CallbackQuery, state: FSMContext):
    """Bosh menyuga qaytish (inline)"""
    await state.finish()

    user = user_db.get_user(call.from_user.id)

    text = f"""
👋 <b>{user.get('full_name', 'Foydalanuvchi') if user else 'Foydalanuvchi'}</b>

📚 Quyidagi menyudan tanlang:
"""

    await call.message.edit_text(text, reply_markup=main_menu_inline())
    await call.answer()