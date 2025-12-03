"""
User Courses Handler
====================
Kurslarni ko'rish va sotib olish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    courses_list,
    course_detail,
    modules_list,
    payment_methods
)
from keyboards.default.user_keyboards import main_menu
from states.user_states import PurchaseStates


# ============================================================
#                    KURSLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text="user:courses")
async def show_all_courses(call: types.CallbackQuery):
    """Barcha kurslarni ko'rsatish"""
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    courses = user_db.get_all_courses(active_only=True)

    if not courses:
        await call.answer("📭 Hozircha kurslar yo'q", show_alert=True)
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
📚 <b>Barcha kurslar</b>

{len(courses)} ta kurs mavjud.

✅ - Sizda mavjud
🔒 - Sotib olish mumkin

⬇️ Kursni tanlang:
"""

    await call.message.edit_text(text, reply_markup=courses_list(courses_with_access, user_id))
    await call.answer()


# ============================================================
#                    KURS TAFSILOTLARI
# ============================================================

@dp.callback_query_handler(text_startswith="user:course:")
async def show_course_detail(call: types.CallbackQuery):
    """Kurs tafsilotlarini ko'rsatish"""
    parts = call.data.split(":")
    action = parts[2]

    if action == "view":
        course_id = int(parts[3])

        telegram_id = call.from_user.id
        user_id = user_db.get_user_id(telegram_id)

        course = user_db.get_course(course_id)

        if not course:
            await call.answer("❌ Kurs topilmadi!", show_alert=True)
            return

        # Dostup tekshirish
        has_access = user_db.has_course_access(user_id, course_id) if user_id else False

        # Kurs statistikasi
        stats = user_db.get_course_stats(course_id)

        # Bepul darslar soni
        free_lessons = user_db.execute(
            """SELECT COUNT(*) FROM Lessons l
               JOIN Modules m ON l.module_id = m.id
               WHERE m.course_id = ? AND l.is_free = TRUE AND l.is_active = TRUE""",
            parameters=(course_id,),
            fetchone=True
        )
        free_count = free_lessons[0] if free_lessons else 0

        # User progress (agar dostup bo'lsa)
        progress_text = ""
        if has_access and user_id:
            progress = user_db.get_user_course_progress(user_id, course_id)
            if progress:
                progress_text = f"\n\n📈 <b>Sizning progressingiz:</b> {progress.get('percentage', 0):.0f}%"

        access_status = "✅ Sizda mavjud" if has_access else f"💰 Narxi: {course['price']:,.0f} so'm"

        text = f"""
📚 <b>{course['name']}</b>

{access_status}

📄 <b>Tavsif:</b>
{course.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Kurs haqida:</b>
├ 📁 Modullar: {stats.get('modules', 0)} ta
├ 📹 Darslar: {stats.get('lessons', 0)} ta
├ 🆓 Bepul darslar: {free_count} ta
└ 👥 O'quvchilar: {stats.get('students', 0)} ta
{progress_text}

⬇️ Tanlang:
"""

        await call.message.edit_text(
            text,
            reply_markup=course_detail(course_id, has_access, free_count > 0)
        )

    await call.answer()


# ============================================================
#                    KURS MODULLARI
# ============================================================

@dp.callback_query_handler(text_startswith="user:modules:")
async def show_course_modules(call: types.CallbackQuery):
    """Kurs modullarini ko'rsatish"""
    course_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, course_id) if user_id else False

    if not has_access:
        await call.answer("🔒 Avval kursni sotib oling!", show_alert=True)
        return

    modules = user_db.get_course_modules(course_id, active_only=True)

    if not modules:
        await call.answer("📭 Bu kursda modullar yo'q", show_alert=True)
        return

    # Har bir modul uchun progress
    modules_with_progress = []
    for module in modules:
        # Modul darslarining progressi
        lessons = user_db.get_module_lessons(module['id'], active_only=True)
        completed = 0
        total = len(lessons)

        for lesson in lessons:
            status = user_db.get_lesson_status(user_id, lesson['id'])
            if status == 'completed':
                completed += 1

        modules_with_progress.append({
            **module,
            'completed': completed,
            'total': total
        })

    text = f"""
📁 <b>Modullar</b>

📚 Kurs: {course['name']}
📊 Jami: {len(modules)} ta modul

✅ - Tugagan
🔄 - Jarayonda
📁 - Boshlanmagan

⬇️ Modulni tanlang:
"""

    await call.message.edit_text(text, reply_markup=modules_list(course_id, modules_with_progress))
    await call.answer()


# ============================================================
#                    KURS SOTIB OLISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:buy:")
async def buy_course_start(call: types.CallbackQuery, state: FSMContext):
    """Kursni sotib olishni boshlash"""
    course_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    if not user_id:
        await call.answer("❌ Avval ro'yxatdan o'ting: /start", show_alert=True)
        return

    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    # Dostup tekshirish
    if user_db.has_course_access(user_id, course_id):
        await call.answer("✅ Sizda bu kurs allaqachon mavjud!", show_alert=True)
        return

    # Kutilayotgan to'lov bormi
    pending = user_db.execute(
        """SELECT id FROM Payments 
           WHERE user_id = ? AND course_id = ? AND status = 'pending'""",
        parameters=(user_id, course_id),
        fetchone=True
    )

    if pending:
        await call.answer(
            "⏳ Sizning to'lovingiz kutilmoqda. Admin tasdiqlashini kuting.",
            show_alert=True
        )
        return

    await state.update_data(course_id=course_id, course_name=course['name'], price=course['price'])

    text = f"""
💰 <b>Kurs sotib olish</b>

📚 Kurs: <b>{course['name']}</b>
💵 Narx: <b>{course['price']:,.0f} so'm</b>

📋 <b>To'lov qilish tartibi:</b>

1️⃣ Quyidagi karta raqamiga pul o'tkazing:

💳 <code>8600 1234 5678 9012</code>
👤 Aliyev Ali

2️⃣ To'lov chekini (screenshot) yuboring

3️⃣ Admin tasdiqlashini kuting (odatda 1-2 soat)

⚠️ <b>Diqqat:</b> Chekda summa va sana ko'rinishi kerak!

⬇️ Davom etish uchun tugmani bosing:
"""

    await call.message.edit_text(text, reply_markup=payment_methods(course_id))
    await call.answer()


@dp.callback_query_handler(text_startswith="user:pay:card:")
async def pay_by_card(call: types.CallbackQuery, state: FSMContext):
    """Karta orqali to'lash"""
    course_id = int(call.data.split(":")[-1])

    await state.update_data(course_id=course_id, payment_method='card')

    text = """
📸 <b>To'lov chekini yuboring</b>

To'lovni amalga oshirgandan so'ng, chek rasmini yuboring.

⚠️ Chekda quyidagilar ko'rinishi kerak:
• To'lov summasi
• Sana va vaqt
• Qabul qiluvchi

📎 Chek rasmini yuboring:
"""

    await call.message.edit_text(text)

    from keyboards.inline.user_keyboards import cancel_button
    await call.message.answer("📸 Chek rasmini yuboring:", reply_markup=cancel_button())

    await PurchaseStates.send_receipt.set()
    await call.answer()


@dp.message_handler(state=PurchaseStates.send_receipt, content_types=['photo'])
async def receive_receipt(message: types.Message, state: FSMContext):
    """To'lov chekini qabul qilish"""
    photo = message.photo[-1]  # Eng katta o'lcham

    data = await state.get_data()
    course_id = data['course_id']

    telegram_id = message.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    course = user_db.get_course(course_id)

    # To'lovni yaratish
    payment_id = user_db.create_payment(
        user_id=user_id,
        course_id=course_id,
        amount=course['price'],
        receipt_file_id=photo.file_id
    )

    if payment_id:
        await state.finish()

        text = f"""
✅ <b>To'lov yuborildi!</b>

📚 Kurs: {course['name']}
💰 Summa: {course['price']:,.0f} so'm
🆔 To'lov ID: #{payment_id}

⏳ Admin tasdiqlashini kuting.
Odatda 1-2 soat ichida tasdiqlanadi.

Sizga xabar yuboramiz!
"""

        await message.answer(text, reply_markup=main_menu())

        # Adminlarga xabar yuborish
        admins = user_db.get_all_admins()
        user = user_db.get_user(telegram_id)

        admin_text = f"""
💰 <b>Yangi to'lov!</b>

👤 Foydalanuvchi: {user.get('full_name', 'Nomalum')}
📱 Telefon: {user.get('phone', 'Nomalum')}
🆔 Telegram: @{message.from_user.username or message.from_user.id}

📚 Kurs: {course['name']}
💵 Summa: {course['price']:,.0f} so'm
🆔 To'lov ID: #{payment_id}

⬇️ Tasdiqlash uchun Admin panelga kiring.
"""

        for admin in admins:
            try:
                # Chekni yuborish
                await bot.send_photo(
                    admin['telegram_id'],
                    photo.file_id,
                    caption=admin_text
                )
            except Exception as e:
                print(f"Admin {admin['telegram_id']} ga xabar yuborib bo'lmadi: {e}")

    else:
        await message.answer(
            "❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.",
            reply_markup=main_menu()
        )
        await state.finish()


@dp.message_handler(state=PurchaseStates.send_receipt, content_types=['document'])
async def receive_receipt_document(message: types.Message, state: FSMContext):
    """Document sifatida chek"""
    document = message.document

    # Rasm formatimi tekshirish
    if document.mime_type and document.mime_type.startswith('image'):
        # Documentni photo kabi qabul qilish
        data = await state.get_data()
        course_id = data['course_id']

        telegram_id = message.from_user.id
        user_id = user_db.get_user_id(telegram_id)

        course = user_db.get_course(course_id)

        payment_id = user_db.create_payment(
            user_id=user_id,
            course_id=course_id,
            amount=course['price'],
            receipt_file_id=document.file_id
        )

        if payment_id:
            await state.finish()

            text = f"""
✅ <b>To'lov yuborildi!</b>

📚 Kurs: {course['name']}
💰 Summa: {course['price']:,.0f} so'm
🆔 To'lov ID: #{payment_id}

⏳ Admin tasdiqlashini kuting.
"""

            await message.answer(text, reply_markup=main_menu())
        else:
            await message.answer("❌ Xatolik yuz berdi!", reply_markup=main_menu())
            await state.finish()
    else:
        await message.answer("❌ Iltimos, rasm yuboring (screenshot)!")


@dp.message_handler(state=PurchaseStates.send_receipt)
async def receipt_wrong_format(message: types.Message):
    """Noto'g'ri format"""
    if message.text == "❌ Bekor qilish":
        from aiogram.dispatcher import FSMContext
        state = dp.current_state(user=message.from_user.id)
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=main_menu())
        return

    await message.answer("❌ Iltimos, to'lov chekining rasmini yuboring!")


# ============================================================
#                    BEPUL DARSLARNI KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:free_lessons:")
async def show_free_lessons(call: types.CallbackQuery):
    """Kursning bepul darslarini ko'rsatish"""
    course_id = int(call.data.split(":")[-1])

    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    # Bepul darslarni olish
    result = user_db.execute(
        """SELECT l.id, l.name, l.description, m.name as module_name
           FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           WHERE m.course_id = ? AND l.is_free = TRUE 
               AND l.is_active = TRUE AND m.is_active = TRUE
           ORDER BY m.order_num, l.order_num""",
        parameters=(course_id,),
        fetchall=True
    )

    if not result:
        await call.answer("📭 Bu kursda bepul darslar yo'q", show_alert=True)
        return

    lessons = []
    for row in result:
        lessons.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'module_name': row[3]
        })

    text = f"""
🆓 <b>Bepul darslar</b>

📚 Kurs: {course['name']}
📊 {len(lessons)} ta bepul dars

⬇️ Darsni tanlang:
"""

    from keyboards.inline.user_keyboards import free_lessons_in_course
    await call.message.edit_text(text, reply_markup=free_lessons_in_course(course_id, lessons))
    await call.answer()


# ============================================================
#                    TO'LOV STATUSI
# ============================================================

@dp.callback_query_handler(text_startswith="user:payment_status:")
async def check_payment_status(call: types.CallbackQuery):
    """To'lov statusini tekshirish"""
    course_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    payment = user_db.execute(
        """SELECT status, created_at FROM Payments 
           WHERE user_id = ? AND course_id = ? 
           ORDER BY created_at DESC LIMIT 1""",
        parameters=(user_id, course_id),
        fetchone=True
    )

    if not payment:
        await call.answer("❌ To'lov topilmadi", show_alert=True)
        return

    status_map = {
        'pending': '⏳ Kutilmoqda',
        'approved': '✅ Tasdiqlangan',
        'rejected': '❌ Rad etilgan'
    }

    status_text = status_map.get(payment[0], '❓ Noma\'lum')

    await call.answer(f"To'lov holati: {status_text}", show_alert=True)