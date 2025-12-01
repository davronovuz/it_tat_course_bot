"""
Admin Courses Handler
=====================
Kurslarni qo'shish, tahrirlash, o'chirish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from loader import dp, bot, user_db
from keyboards.default.admin_keyboards import (
    courses_menu,
    courses_list,
    course_detail,
    course_edit_menu,
    confirm_action,
    back_button
)
from keyboards.default.admin_keyboards import (
    admin_cancel_button,
    admin_skip_button,
    admin_confirm_keyboard
)
from states.admin_states import CourseStates


# ============================================================
#                    KURSLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text="admin:course:list")
async def show_courses_list(call: types.CallbackQuery):
    """Kurslar ro'yxatini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    courses = user_db.get_all_courses(active_only=False)

    if not courses:
        text = """
📚 <b>Kurslar ro'yxati</b>

📭 Hozircha kurslar yo'q.

Yangi kurs qo'shish uchun tugmani bosing.
"""
    else:
        text = f"""
📚 <b>Kurslar ro'yxati</b>

📊 Jami: {len(courses)} ta kurs

✅ - Faol
❌ - Nofaol

⬇️ Kursni tanlang:
"""

    await call.message.edit_text(text, reply_markup=courses_list(courses))
    await call.answer()


# ============================================================
#                    KURS QO'SHISH
# ============================================================

@dp.callback_query_handler(text="admin:course:add")
async def add_course_start(call: types.CallbackQuery, state: FSMContext):
    """Yangi kurs qo'shishni boshlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    await call.message.edit_text(
        "📚 <b>Yangi kurs qo'shish</b>\n\n"
        "📝 Kurs nomini kiriting:\n\n"
        "<i>Masalan: Kompyuter savodxonligi</i>"
    )

    await call.message.answer(
        "⌨️ Kurs nomini yozing yoki bekor qiling:",
        reply_markup=admin_cancel_button()
    )

    await CourseStates.add_name.set()
    await call.answer()


@dp.message_handler(state=CourseStates.add_name)
async def add_course_name(message: types.Message, state: FSMContext):
    """Kurs nomini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    course_name = message.text.strip()

    if len(course_name) < 3:
        await message.answer("❌ Kurs nomi kamida 3 ta belgidan iborat bo'lishi kerak!")
        return

    if len(course_name) > 100:
        await message.answer("❌ Kurs nomi 100 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(name=course_name)

    await message.answer(
        f"✅ Kurs nomi: <b>{course_name}</b>\n\n"
        "📄 Endi kurs tavsifini kiriting:\n\n"
        "<i>Masalan: Bu kursda kompyuterning asosiy ishlash prinsplarini o'rganasiz...</i>",
        reply_markup=admin_skip_button()
    )

    await CourseStates.add_description.set()


@dp.message_handler(state=CourseStates.add_description)
async def add_course_description(message: types.Message, state: FSMContext):
    """Kurs tavsifini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        description = None
    else:
        description = message.text.strip()
        if len(description) > 1000:
            await message.answer("❌ Tavsif 1000 ta belgidan oshmasligi kerak!")
            return

    await state.update_data(description=description)

    await message.answer(
        "💰 Kurs narxini kiriting (so'mda):\n\n"
        "<i>Masalan: 200000</i>\n\n"
        "Bepul kurs uchun 0 kiriting.",
        reply_markup=admin_cancel_button()
    )

    await CourseStates.add_price.set()


@dp.message_handler(state=CourseStates.add_price)
async def add_course_price(message: types.Message, state: FSMContext):
    """Kurs narxini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    try:
        price = float(message.text.strip().replace(" ", "").replace(",", ""))
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting (masalan: 200000)")
        return

    await state.update_data(price=price)

    # Ma'lumotlarni ko'rsatish
    data = await state.get_data()

    text = f"""
📚 <b>Yangi kurs</b>

📝 Nom: <b>{data['name']}</b>
📄 Tavsif: {data.get('description') or '<i>Yo\'q</i>'}
💰 Narx: <b>{price:,.0f} so'm</b>

✅ Tasdiqlaysizmi?
"""

    await message.answer(text, reply_markup=admin_confirm_keyboard())
    await CourseStates.add_confirm.set()


@dp.message_handler(state=CourseStates.add_confirm)
async def add_course_confirm(message: types.Message, state: FSMContext):
    """Kurs qo'shishni tasdiqlash"""
    if message.text == "❌ Yo'q" or message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text != "✅ Ha":
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")
        return

    data = await state.get_data()

    # Kursni qo'shish
    course_id = user_db.add_course(
        name=data['name'],
        description=data.get('description'),
        price=data['price']
    )

    if course_id:
        await message.answer(
            f"✅ Kurs muvaffaqiyatli qo'shildi!\n\n"
            f"📚 <b>{data['name']}</b>\n"
            f"🆔 ID: {course_id}\n\n"
            f"Endi bu kursga modullar qo'shishingiz mumkin.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Kurs tafsilotlarini ko'rsatish
        await message.answer(
            "📚 Kurs tafsilotlari:",
            reply_markup=course_detail(course_id, is_active=True)
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.finish()


# ============================================================
#                    KURS KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:course:view:")
async def view_course(call: types.CallbackQuery):
    """Kurs tafsilotlarini ko'rish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])
    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    # Statistika
    stats = user_db.get_course_stats(course_id)
    modules = user_db.get_course_modules(course_id, active_only=False)

    status = "✅ Faol" if course['is_active'] else "❌ Nofaol"

    text = f"""
📚 <b>{course['name']}</b>

{status}

📄 <b>Tavsif:</b>
{course.get('description') or '<i>Tavsif yo\'q</i>'}

💰 <b>Narx:</b> {course['price']:,.0f} so'm

📊 <b>Statistika:</b>
├ 📁 Modullar: {stats.get('modules', 0)} ta
├ 📹 Darslar: {stats.get('lessons', 0)} ta
├ 👥 O'quvchilar: {stats.get('students', 0)} ta
└ 🎓 Tugatganlar: {stats.get('completed', 0)} ta

⬇️ Amal tanlang:
"""

    await call.message.edit_text(
        text,
        reply_markup=course_detail(course_id, course['is_active'])
    )
    await call.answer()


# ============================================================
#                    KURS TAHRIRLASH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:course:edit:")
async def edit_course_menu(call: types.CallbackQuery, state: FSMContext):
    """Kurs tahrirlash menyusi"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    parts = call.data.split(":")

    # admin:course:edit:field:id yoki admin:course:edit:id
    if len(parts) == 5:
        # Aniq maydonni tahrirlash
        field = parts[3]
        course_id = int(parts[4])

        await state.update_data(course_id=course_id)

        if field == "name":
            await call.message.edit_text(
                "📝 <b>Kurs nomini tahrirlash</b>\n\n"
                "Yangi nomni kiriting:"
            )
            await call.message.answer("⌨️ Yangi nom:", reply_markup=admin_cancel_button())
            await CourseStates.edit_name.set()

        elif field == "desc":
            await call.message.edit_text(
                "📄 <b>Kurs tavsifini tahrirlash</b>\n\n"
                "Yangi tavsifni kiriting:"
            )
            await call.message.answer("⌨️ Yangi tavsif:", reply_markup=admin_skip_button())
            await CourseStates.edit_description.set()

        elif field == "price":
            await call.message.edit_text(
                "💰 <b>Kurs narxini tahrirlash</b>\n\n"
                "Yangi narxni kiriting (so'mda):"
            )
            await call.message.answer("⌨️ Yangi narx:", reply_markup=admin_cancel_button())
            await CourseStates.edit_price.set()

        elif field == "order":
            await call.message.edit_text(
                "🔢 <b>Kurs tartibini tahrirlash</b>\n\n"
                "Yangi tartib raqamini kiriting:"
            )
            await call.message.answer("⌨️ Tartib raqami:", reply_markup=admin_cancel_button())
            await CourseStates.edit_order.set()

    else:
        # Tahrirlash menyusi
        course_id = int(parts[3])
        course = user_db.get_course(course_id)

        if not course:
            await call.answer("❌ Kurs topilmadi!", show_alert=True)
            return

        text = f"""
✏️ <b>Kursni tahrirlash</b>

📚 {course['name']}

Qaysi maydonni tahrirlamoqchisiz?
"""

        await call.message.edit_text(text, reply_markup=course_edit_menu(course_id))

    await call.answer()


@dp.message_handler(state=CourseStates.edit_name)
async def edit_course_name(message: types.Message, state: FSMContext):
    """Kurs nomini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    new_name = message.text.strip()

    if len(new_name) < 3 or len(new_name) > 100:
        await message.answer("❌ Nom 3-100 belgi orasida bo'lishi kerak!")
        return

    data = await state.get_data()
    course_id = data['course_id']

    if user_db.update_course(course_id, name=new_name):
        await message.answer(
            f"✅ Kurs nomi yangilandi!\n\n"
            f"📚 Yangi nom: <b>{new_name}</b>",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Kurs tafsilotlarini ko'rsatish
        course = user_db.get_course(course_id)
        await message.answer(
            "📚 Kurs:",
            reply_markup=course_detail(course_id, course['is_active'])
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=CourseStates.edit_description)
async def edit_course_description(message: types.Message, state: FSMContext):
    """Kurs tavsifini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        new_desc = None
    else:
        new_desc = message.text.strip()
        if len(new_desc) > 1000:
            await message.answer("❌ Tavsif 1000 belgidan oshmasligi kerak!")
            return

    data = await state.get_data()
    course_id = data['course_id']

    if user_db.update_course(course_id, description=new_desc):
        await message.answer(
            "✅ Kurs tavsifi yangilandi!",
            reply_markup=types.ReplyKeyboardRemove()
        )

        course = user_db.get_course(course_id)
        await message.answer(
            "📚 Kurs:",
            reply_markup=course_detail(course_id, course['is_active'])
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=CourseStates.edit_price)
async def edit_course_price(message: types.Message, state: FSMContext):
    """Kurs narxini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    try:
        new_price = float(message.text.strip().replace(" ", "").replace(",", ""))
        if new_price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting")
        return

    data = await state.get_data()
    course_id = data['course_id']

    if user_db.update_course(course_id, price=new_price):
        await message.answer(
            f"✅ Kurs narxi yangilandi!\n\n"
            f"💰 Yangi narx: <b>{new_price:,.0f} so'm</b>",
            reply_markup=types.ReplyKeyboardRemove()
        )

        course = user_db.get_course(course_id)
        await message.answer(
            "📚 Kurs:",
            reply_markup=course_detail(course_id, course['is_active'])
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=CourseStates.edit_order)
async def edit_course_order(message: types.Message, state: FSMContext):
    """Kurs tartibini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    try:
        new_order = int(message.text.strip())
        if new_order < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Musbat son kiriting")
        return

    data = await state.get_data()
    course_id = data['course_id']

    if user_db.update_course(course_id, order_num=new_order):
        await message.answer(
            f"✅ Kurs tartibi yangilandi!\n\n"
            f"🔢 Yangi tartib: <b>{new_order}</b>",
            reply_markup=types.ReplyKeyboardRemove()
        )

        course = user_db.get_course(course_id)
        await message.answer(
            "📚 Kurs:",
            reply_markup=course_detail(course_id, course['is_active'])
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


# ============================================================
#                    KURS AKTIVATSIYA/DEAKTIVATSIYA
# ============================================================

@dp.callback_query_handler(text_startswith="admin:course:activate:")
async def activate_course(call: types.CallbackQuery):
    """Kursni faollashtirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])

    if user_db.update_course(course_id, is_active=True):
        await call.answer("✅ Kurs faollashtirildi!", show_alert=True)

        # Sahifani yangilash
        course = user_db.get_course(course_id)
        stats = user_db.get_course_stats(course_id)

        text = f"""
📚 <b>{course['name']}</b>

✅ Faol

📄 <b>Tavsif:</b>
{course.get('description') or '<i>Tavsif yo\'q</i>'}

💰 <b>Narx:</b> {course['price']:,.0f} so'm

📊 <b>Statistika:</b>
├ 📁 Modullar: {stats.get('modules', 0)} ta
├ 📹 Darslar: {stats.get('lessons', 0)} ta
├ 👥 O'quvchilar: {stats.get('students', 0)} ta
└ 🎓 Tugatganlar: {stats.get('completed', 0)} ta
"""

        await call.message.edit_text(text, reply_markup=course_detail(course_id, True))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:course:deactivate:")
async def deactivate_course(call: types.CallbackQuery):
    """Kursni nofaol qilish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])

    if user_db.update_course(course_id, is_active=False):
        await call.answer("✅ Kurs nofaol qilindi!", show_alert=True)

        # Sahifani yangilash
        course = user_db.get_course(course_id)
        stats = user_db.get_course_stats(course_id)

        text = f"""
📚 <b>{course['name']}</b>

❌ Nofaol

📄 <b>Tavsif:</b>
{course.get('description') or '<i>Tavsif yo\'q</i>'}

💰 <b>Narx:</b> {course['price']:,.0f} so'm

📊 <b>Statistika:</b>
├ 📁 Modullar: {stats.get('modules', 0)} ta
├ 📹 Darslar: {stats.get('lessons', 0)} ta
├ 👥 O'quvchilar: {stats.get('students', 0)} ta
└ 🎓 Tugatganlar: {stats.get('completed', 0)} ta
"""

        await call.message.edit_text(text, reply_markup=course_detail(course_id, False))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


# ============================================================
#                    KURSNI O'CHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:course:delete:")
async def delete_course_confirm(call: types.CallbackQuery):
    """Kursni o'chirishni tasdiqlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])
    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    text = f"""
🗑 <b>Kursni o'chirish</b>

📚 {course['name']}

⚠️ Diqqat! Kurs o'chirilsa:
• Barcha modullar
• Barcha darslar
• Barcha testlar
• Barcha progresslar

ham o'chib ketadi!

❓ Rostdan ham o'chirmoqchimisiz?
"""

    await call.message.edit_text(
        text,
        reply_markup=confirm_action("course_delete", course_id)
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:confirm:course_delete:")
async def delete_course_execute(call: types.CallbackQuery):
    """Kursni o'chirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])

    if user_db.delete_course(course_id):
        await call.answer("✅ Kurs o'chirildi!", show_alert=True)

        # Kurslar ro'yxatiga qaytish
        courses = user_db.get_all_courses(active_only=False)

        text = f"""
📚 <b>Kurslar ro'yxati</b>

📊 Jami: {len(courses)} ta kurs

⬇️ Kursni tanlang:
"""

        await call.message.edit_text(text, reply_markup=courses_list(courses))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:cancel:course_delete:")
async def cancel_delete_course(call: types.CallbackQuery):
    """Kurs o'chirishni bekor qilish"""
    course_id = int(call.data.split(":")[-1])
    course = user_db.get_course(course_id)

    if course:
        stats = user_db.get_course_stats(course_id)

        text = f"""
📚 <b>{course['name']}</b>

{"✅ Faol" if course['is_active'] else "❌ Nofaol"}

📄 <b>Tavsif:</b>
{course.get('description') or '<i>Tavsif yo\'q</i>'}

💰 <b>Narx:</b> {course['price']:,.0f} so'm

📊 <b>Statistika:</b>
├ 📁 Modullar: {stats.get('modules', 0)} ta
├ 📹 Darslar: {stats.get('lessons', 0)} ta
├ 👥 O'quvchilar: {stats.get('students', 0)} ta
└ 🎓 Tugatganlar: {stats.get('completed', 0)} ta
"""

        await call.message.edit_text(text, reply_markup=course_detail(course_id, course['is_active']))

    await call.answer("❌ Bekor qilindi")


# ============================================================
#                    KURS STATISTIKASI
# ============================================================

@dp.callback_query_handler(text_startswith="admin:course:stats:")
async def show_course_stats(call: types.CallbackQuery):
    """Kurs statistikasini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])
    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    stats = user_db.get_course_stats(course_id)

    text = f"""
📊 <b>Kurs statistikasi</b>

📚 {course['name']}

📁 <b>Kontent:</b>
├ Modullar: {stats.get('modules', 0)} ta
└ Darslar: {stats.get('lessons', 0)} ta

👥 <b>O'quvchilar:</b>
├ Jami: {stats.get('students', 0)} ta
├ Tugatganlar: {stats.get('completed', 0)} ta
└ O'rtacha progress: {stats.get('avg_progress', 0):.1f}%

💰 <b>Moliya:</b>
├ Narx: {course['price']:,.0f} so'm
└ Taxminiy daromad: {course['price'] * stats.get('students', 0):,.0f} so'm
"""

    await call.message.edit_text(
        text,
        reply_markup=back_button(f"admin:course:view:{course_id}")
    )
    await call.answer()