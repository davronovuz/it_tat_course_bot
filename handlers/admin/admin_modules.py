"""
Admin Modules Handler
=====================
Modullarni qo'shish, tahrirlash, o'chirish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, user_db
from keyboards.inline.admin_keyboards import (
    modules_list,
    module_detail,
    module_edit_menu,
    confirm_action
)
from keyboards.default.admin_keyboards import (
    admin_cancel_button,
    admin_skip_button,
    admin_confirm_keyboard
)
from states.admin_states import ModuleStates


# ============================================================
#                    MODULLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text_startswith="admin:module:list:")
async def show_modules_list(call: types.CallbackQuery):
    """Modullar ro'yxatini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])
    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    modules = user_db.get_course_modules(course_id, active_only=False)

    if not modules:
        text = f"""
📁 <b>Modullar</b>

📚 Kurs: {course['name']}

📭 Hozircha modullar yo'q.

Yangi modul qo'shish uchun tugmani bosing.
"""
    else:
        text = f"""
📁 <b>Modullar</b>

📚 Kurs: {course['name']}
📊 Jami: {len(modules)} ta modul

✅ - Faol
❌ - Nofaol

⬇️ Modulni tanlang:
"""

    await call.message.edit_text(text, reply_markup=modules_list(course_id, modules))
    await call.answer()


# ============================================================
#                    MODUL QO'SHISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:module:add:")
async def add_module_start(call: types.CallbackQuery, state: FSMContext):
    """Yangi modul qo'shishni boshlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    course_id = int(call.data.split(":")[-1])
    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    await state.update_data(course_id=course_id, course_name=course['name'])

    await call.message.edit_text(
        f"📁 <b>Yangi modul qo'shish</b>\n\n"
        f"📚 Kurs: {course['name']}\n\n"
        f"📝 Modul nomini kiriting:\n\n"
        f"<i>Masalan: Windows asoslari</i>"
    )

    await call.message.answer(
        "⌨️ Modul nomini yozing:",
        reply_markup=admin_cancel_button()
    )

    await ModuleStates.add_name.set()
    await call.answer()


@dp.message_handler(state=ModuleStates.add_name)
async def add_module_name(message: types.Message, state: FSMContext):
    """Modul nomini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    module_name = message.text.strip()

    if len(module_name) < 2:
        await message.answer("❌ Modul nomi kamida 2 ta belgidan iborat bo'lishi kerak!")
        return

    if len(module_name) > 100:
        await message.answer("❌ Modul nomi 100 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(name=module_name)

    await message.answer(
        f"✅ Modul nomi: <b>{module_name}</b>\n\n"
        f"📄 Endi modul tavsifini kiriting:\n\n"
        f"<i>Masalan: Bu modulda Windows operatsion tizimi asoslarini o'rganamiz</i>",
        reply_markup=admin_skip_button()
    )

    await ModuleStates.add_description.set()


@dp.message_handler(state=ModuleStates.add_description)
async def add_module_description(message: types.Message, state: FSMContext):
    """Modul tavsifini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        description = None
    else:
        description = message.text.strip()
        if len(description) > 500:
            await message.answer("❌ Tavsif 500 ta belgidan oshmasligi kerak!")
            return

    await state.update_data(description=description)

    # Ma'lumotlarni ko'rsatish
    data = await state.get_data()

    text = f"""
📁 <b>Yangi modul</b>

📚 Kurs: {data['course_name']}
📝 Nom: <b>{data['name']}</b>
📄 Tavsif: {description or '<i>Yoq</i>'}

✅ Tasdiqlaysizmi?
"""

    await message.answer(text, reply_markup=admin_confirm_keyboard())
    await ModuleStates.add_confirm.set()


@dp.message_handler(state=ModuleStates.add_confirm)
async def add_module_confirm(message: types.Message, state: FSMContext):
    """Modul qo'shishni tasdiqlash"""
    if message.text == "❌ Yo'q" or message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text != "✅ Ha":
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")
        return

    data = await state.get_data()

    # Modulni qo'shish
    module_id = user_db.add_module(
        course_id=data['course_id'],
        name=data['name'],
        description=data.get('description')
    )

    if module_id:
        await message.answer(
            f"✅ Modul muvaffaqiyatli qo'shildi!\n\n"
            f"📁 <b>{data['name']}</b>\n"
            f"🆔 ID: {module_id}\n\n"
            f"Endi bu modulga darslar qo'shishingiz mumkin.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Modul tafsilotlarini ko'rsatish
        await message.answer(
            "📁 Modul tafsilotlari:",
            reply_markup=module_detail(module_id, data['course_id'], is_active=True)
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.finish()


# ============================================================
#                    MODUL KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:module:view:")
async def view_module(call: types.CallbackQuery):
    """Modul tafsilotlarini ko'rish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    module_id = int(call.data.split(":")[-1])
    module = user_db.get_module(module_id)

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # Darslar soni
    lessons = user_db.get_module_lessons(module_id, active_only=False)
    lessons_count = len(lessons)

    status = "✅ Faol" if module['is_active'] else "❌ Nofaol"

    text = f"""
📁 <b>{module['name']}</b>

{status}
📚 Kurs: {module['course_name']}
🔢 Tartib: {module['order_num']}

📄 <b>Tavsif:</b>
{module.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Statistika:</b>
└ 📹 Darslar: {lessons_count} ta

⬇️ Amal tanlang:
"""

    await call.message.edit_text(
        text,
        reply_markup=module_detail(module_id, module['course_id'], module['is_active'])
    )
    await call.answer()


# ============================================================
#                    MODUL TAHRIRLASH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:module:edit:")
async def edit_module_menu(call: types.CallbackQuery, state: FSMContext):
    """Modul tahrirlash menyusi"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    parts = call.data.split(":")

    # admin:module:edit:field:id yoki admin:module:edit:id
    if len(parts) == 5:
        # Aniq maydonni tahrirlash
        field = parts[3]
        module_id = int(parts[4])

        module = user_db.get_module(module_id)
        if not module:
            await call.answer("❌ Modul topilmadi!", show_alert=True)
            return

        await state.update_data(module_id=module_id, course_id=module['course_id'])

        if field == "name":
            await call.message.edit_text(
                f"📝 <b>Modul nomini tahrirlash</b>\n\n"
                f"Hozirgi nom: {module['name']}\n\n"
                f"Yangi nomni kiriting:"
            )
            await call.message.answer("⌨️ Yangi nom:", reply_markup=admin_cancel_button())
            await ModuleStates.edit_name.set()

        elif field == "desc":
            await call.message.edit_text(
                f"📄 <b>Modul tavsifini tahrirlash</b>\n\n"
                f"Hozirgi tavsif: {module.get('description') or 'Yo`q'}\n\n"
                f"Yangi tavsifni kiriting:"
            )
            await call.message.answer("⌨️ Yangi tavsif:", reply_markup=admin_skip_button())
            await ModuleStates.edit_description.set()

        elif field == "order":
            await call.message.edit_text(
                f"🔢 <b>Modul tartibini tahrirlash</b>\n\n"
                f"Hozirgi tartib: {module['order_num']}\n\n"
                f"Yangi tartib raqamini kiriting:"
            )
            await call.message.answer("⌨️ Tartib raqami:", reply_markup=admin_cancel_button())
            await ModuleStates.edit_order.set()

    else:
        # Tahrirlash menyusi
        module_id = int(parts[3])
        module = user_db.get_module(module_id)

        if not module:
            await call.answer("❌ Modul topilmadi!", show_alert=True)
            return

        text = f"""
✏️ <b>Modulni tahrirlash</b>

📁 {module['name']}

Qaysi maydonni tahrirlamoqchisiz?
"""

        await call.message.edit_text(text, reply_markup=module_edit_menu(module_id))

    await call.answer()


@dp.message_handler(state=ModuleStates.edit_name)
async def edit_module_name(message: types.Message, state: FSMContext):
    """Modul nomini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    new_name = message.text.strip()

    if len(new_name) < 2 or len(new_name) > 100:
        await message.answer("❌ Nom 2-100 belgi orasida bo'lishi kerak!")
        return

    data = await state.get_data()
    module_id = data['module_id']

    if user_db.update_module(module_id, name=new_name):
        await message.answer(
            f"✅ Modul nomi yangilandi!\n\n"
            f"📁 Yangi nom: <b>{new_name}</b>",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Modul tafsilotlarini ko'rsatish
        module = user_db.get_module(module_id)
        await message.answer(
            "📁 Modul:",
            reply_markup=module_detail(module_id, module['course_id'], module['is_active'])
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=ModuleStates.edit_description)
async def edit_module_description(message: types.Message, state: FSMContext):
    """Modul tavsifini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        new_desc = None
    else:
        new_desc = message.text.strip()
        if len(new_desc) > 500:
            await message.answer("❌ Tavsif 500 belgidan oshmasligi kerak!")
            return

    data = await state.get_data()
    module_id = data['module_id']

    if user_db.update_module(module_id, description=new_desc):
        await message.answer(
            "✅ Modul tavsifi yangilandi!",
            reply_markup=types.ReplyKeyboardRemove()
        )

        module = user_db.get_module(module_id)
        await message.answer(
            "📁 Modul:",
            reply_markup=module_detail(module_id, module['course_id'], module['is_active'])
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=ModuleStates.edit_order)
async def edit_module_order(message: types.Message, state: FSMContext):
    """Modul tartibini yangilash"""
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
    module_id = data['module_id']

    if user_db.update_module(module_id, order_num=new_order):
        await message.answer(
            f"✅ Modul tartibi yangilandi!\n\n"
            f"🔢 Yangi tartib: <b>{new_order}</b>",
            reply_markup=types.ReplyKeyboardRemove()
        )

        module = user_db.get_module(module_id)
        await message.answer(
            "📁 Modul:",
            reply_markup=module_detail(module_id, module['course_id'], module['is_active'])
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


# ============================================================
#                    MODUL AKTIVATSIYA/DEAKTIVATSIYA
# ============================================================

@dp.callback_query_handler(text_startswith="admin:module:activate:")
async def activate_module(call: types.CallbackQuery):
    """Modulni faollashtirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    module_id = int(call.data.split(":")[-1])

    if user_db.update_module(module_id, is_active=True):
        await call.answer("✅ Modul faollashtirildi!", show_alert=True)

        # Sahifani yangilash
        module = user_db.get_module(module_id)
        lessons = user_db.get_module_lessons(module_id, active_only=False)

        text = f"""
📁 <b>{module['name']}</b>

✅ Faol
📚 Kurs: {module['course_name']}
🔢 Tartib: {module['order_num']}

📄 <b>Tavsif:</b>
{module.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Statistika:</b>
└ 📹 Darslar: {len(lessons)} ta
"""

        await call.message.edit_text(
            text,
            reply_markup=module_detail(module_id, module['course_id'], True)
        )
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:module:deactivate:")
async def deactivate_module(call: types.CallbackQuery):
    """Modulni nofaol qilish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    module_id = int(call.data.split(":")[-1])

    if user_db.update_module(module_id, is_active=False):
        await call.answer("✅ Modul nofaol qilindi!", show_alert=True)

        # Sahifani yangilash
        module = user_db.get_module(module_id)
        lessons = user_db.get_module_lessons(module_id, active_only=False)

        text = f"""
📁 <b>{module['name']}</b>

❌ Nofaol
📚 Kurs: {module['course_name']}
🔢 Tartib: {module['order_num']}

📄 <b>Tavsif:</b>
{module.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Statistika:</b>
└ 📹 Darslar: {len(lessons)} ta
"""

        await call.message.edit_text(
            text,
            reply_markup=module_detail(module_id, module['course_id'], False)
        )
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


# ============================================================
#                    MODULNI O'CHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:module:delete:")
async def delete_module_confirm(call: types.CallbackQuery):
    """Modulni o'chirishni tasdiqlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    module_id = int(call.data.split(":")[-1])
    module = user_db.get_module(module_id)

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    lessons = user_db.get_module_lessons(module_id, active_only=False)

    text = f"""
🗑 <b>Modulni o'chirish</b>

📁 {module['name']}

⚠️ Diqqat! Modul o'chirilsa:
• {len(lessons)} ta dars
• Barcha testlar
• Barcha progresslar

ham o'chib ketadi!

❓ Rostdan ham o'chirmoqchimisiz?
"""

    await call.message.edit_text(
        text,
        reply_markup=confirm_action("module_delete", module_id)
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:confirm:module_delete:")
async def delete_module_execute(call: types.CallbackQuery):
    """Modulni o'chirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    module_id = int(call.data.split(":")[-1])
    module = user_db.get_module(module_id)

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    course_id = module['course_id']

    if user_db.delete_module(module_id):
        await call.answer("✅ Modul o'chirildi!", show_alert=True)

        # Modullar ro'yxatiga qaytish
        modules = user_db.get_course_modules(course_id, active_only=False)
        course = user_db.get_course(course_id)

        text = f"""
📁 <b>Modullar</b>

📚 Kurs: {course['name']}
📊 Jami: {len(modules)} ta modul

⬇️ Modulni tanlang:
"""

        await call.message.edit_text(text, reply_markup=modules_list(course_id, modules))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:cancel:module_delete:")
async def cancel_delete_module(call: types.CallbackQuery):
    """Modul o'chirishni bekor qilish"""
    module_id = int(call.data.split(":")[-1])
    module = user_db.get_module(module_id)

    if module:
        lessons = user_db.get_module_lessons(module_id, active_only=False)

        text = f"""
📁 <b>{module['name']}</b>

{"✅ Faol" if module['is_active'] else "❌ Nofaol"}
📚 Kurs: {module['course_name']}
🔢 Tartib: {module['order_num']}

📄 <b>Tavsif:</b>
{module.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Statistika:</b>
└ 📹 Darslar: {len(lessons)} ta
"""

        await call.message.edit_text(
            text,
            reply_markup=module_detail(module_id, module['course_id'], module['is_active'])
        )

    await call.answer("❌ Bekor qilindi")