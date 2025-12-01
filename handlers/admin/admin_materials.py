"""
Admin Materials Handler
=======================
Dars materiallarini qo'shish, tahrirlash, o'chirish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from loader import dp, bot, user_db
from keyboards.default.admin_keyboards import (
    materials_list,
    material_detail,
    material_type_select,
    confirm_action,
    back_button
)
from keyboards.default.admin_keyboards import (
    admin_cancel_button,
    admin_skip_button,
    admin_confirm_keyboard
)
from states.admin_states import MaterialStates

# Fayl turi ikonkalari
FILE_TYPE_ICONS = {
    'pdf': '📕',
    'pptx': '📊',
    'docx': '📄',
    'xlsx': '📗',
    'image': '🖼',
    'other': '📎'
}

# Content type -> fayl turi mapping
CONTENT_TYPE_MAP = {
    'document': {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
        'application/vnd.ms-powerpoint': 'pptx',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.ms-excel': 'xlsx',
    },
    'photo': 'image'
}


# ============================================================
#                    MATERIALLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text_startswith="admin:material:list:")
async def show_materials_list(call: types.CallbackQuery):
    """Materiallar ro'yxatini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    materials = user_db.get_lesson_materials(lesson_id)

    if not materials:
        text = f"""
📎 <b>Dars materiallari</b>

📹 Dars: {lesson['name']}
📁 Modul: {lesson['module_name']}

📭 Hozircha materiallar yo'q.

Yangi material qo'shish uchun tugmani bosing.
"""
    else:
        text = f"""
📎 <b>Dars materiallari</b>

📹 Dars: {lesson['name']}
📁 Modul: {lesson['module_name']}
📊 Jami: {len(materials)} ta material

⬇️ Materialni tanlang:
"""

    await call.message.edit_text(text, reply_markup=materials_list(lesson_id, materials))
    await call.answer()


# ============================================================
#                    MATERIAL QO'SHISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:material:add:")
async def add_material_start(call: types.CallbackQuery, state: FSMContext):
    """Yangi material qo'shishni boshlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    await state.update_data(
        lesson_id=lesson_id,
        lesson_name=lesson['name']
    )

    text = f"""
📎 <b>Yangi material qo'shish</b>

📹 Dars: {lesson['name']}

📝 Material nomini kiriting:

<i>Masalan: 1-dars prezentatsiya.pptx</i>
"""

    await call.message.edit_text(text)
    await call.message.answer("⌨️ Material nomini yozing:", reply_markup=admin_cancel_button())

    await MaterialStates.add_name.set()
    await call.answer()


@dp.message_handler(state=MaterialStates.add_name)
async def add_material_name(message: types.Message, state: FSMContext):
    """Material nomini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    material_name = message.text.strip()

    if len(material_name) < 2:
        await message.answer("❌ Material nomi kamida 2 ta belgidan iborat bo'lishi kerak!")
        return

    if len(material_name) > 150:
        await message.answer("❌ Material nomi 150 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(name=material_name)

    await message.answer(
        f"✅ Material nomi: <b>{material_name}</b>\n\n"
        f"📎 <b>Endi faylni yuboring</b>\n\n"
        f"Qo'llab-quvvatlanadigan formatlar:\n"
        f"• 📕 PDF\n"
        f"• 📊 PowerPoint (PPTX)\n"
        f"• 📄 Word (DOCX)\n"
        f"• 📗 Excel (XLSX)\n"
        f"• 🖼 Rasmlar (PNG, JPG)",
        reply_markup=admin_cancel_button()
    )

    await MaterialStates.add_file.set()


@dp.message_handler(state=MaterialStates.add_file, content_types=['document', 'photo'])
async def add_material_file(message: types.Message, state: FSMContext):
    """Material faylini qabul qilish"""

    if message.document:
        file_id = message.document.file_id
        file_size = message.document.file_size
        mime_type = message.document.mime_type
        file_name = message.document.file_name or "file"

        # Fayl turini aniqlash
        file_type = CONTENT_TYPE_MAP['document'].get(mime_type, 'other')

    elif message.photo:
        # Eng katta o'lchamdagi rasmni olish
        photo = message.photo[-1]
        file_id = photo.file_id
        file_size = photo.file_size
        file_type = 'image'
        file_name = "image.jpg"

    else:
        await message.answer("❌ Noto'g'ri fayl formati!")
        return

    await state.update_data(
        file_id=file_id,
        file_size=file_size,
        file_type=file_type
    )

    icon = FILE_TYPE_ICONS.get(file_type, '📎')
    size_kb = file_size / 1024 if file_size else 0
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

    await message.answer(
        f"✅ Fayl qabul qilindi!\n\n"
        f"{icon} Turi: {file_type.upper()}\n"
        f"📦 Hajmi: {size_str}\n\n"
        f"📄 Tavsif qo'shmoqchimisiz?\n\n"
        f"<i>Masalan: Bu materialda asosiy tushunchalar keltirilgan</i>",
        reply_markup=admin_skip_button()
    )

    await MaterialStates.add_description.set()


@dp.message_handler(state=MaterialStates.add_file)
async def add_material_file_text(message: types.Message, state: FSMContext):
    """Fayl o'rniga matn kelsa"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    await message.answer(
        "❌ Iltimos, fayl yuboring!\n\n"
        "Qo'llab-quvvatlanadigan formatlar: PDF, PPTX, DOCX, XLSX, PNG, JPG"
    )


@dp.message_handler(state=MaterialStates.add_description)
async def add_material_description(message: types.Message, state: FSMContext):
    """Material tavsifini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        description = None
    else:
        description = message.text.strip()
        if len(description) > 300:
            await message.answer("❌ Tavsif 300 ta belgidan oshmasligi kerak!")
            return

    await state.update_data(description=description)

    # Ma'lumotlarni ko'rsatish
    data = await state.get_data()

    icon = FILE_TYPE_ICONS.get(data['file_type'], '📎')
    size_kb = data.get('file_size', 0) / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

    text = f"""
📎 <b>Yangi material</b>

📹 Dars: {data['lesson_name']}
📝 Nom: <b>{data['name']}</b>
{icon} Turi: {data['file_type'].upper()}
📦 Hajmi: {size_str}
📄 Tavsif: {description or '<i>Yo\'q</i>'}

✅ Tasdiqlaysizmi?
"""

    await message.answer(text, reply_markup=admin_confirm_keyboard())
    await MaterialStates.add_confirm.set()


@dp.message_handler(state=MaterialStates.add_confirm)
async def add_material_confirm(message: types.Message, state: FSMContext):
    """Material qo'shishni tasdiqlash"""
    if message.text == "❌ Yo'q" or message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text != "✅ Ha":
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")
        return

    data = await state.get_data()

    # Materialni qo'shish
    material_id = user_db.add_material(
        lesson_id=data['lesson_id'],
        name=data['name'],
        file_type=data['file_type'],
        file_id=data['file_id'],
        file_size=data.get('file_size'),
        description=data.get('description')
    )

    if material_id:
        icon = FILE_TYPE_ICONS.get(data['file_type'], '📎')

        await message.answer(
            f"✅ Material muvaffaqiyatli qo'shildi!\n\n"
            f"{icon} <b>{data['name']}</b>\n"
            f"🆔 ID: {material_id}",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Materiallar ro'yxatiga qaytish
        materials = user_db.get_lesson_materials(data['lesson_id'])
        lesson = user_db.get_lesson(data['lesson_id'])

        await message.answer(
            f"📎 <b>Materiallar</b>\n\n"
            f"📹 Dars: {lesson['name']}\n"
            f"📊 Jami: {len(materials)} ta material",
            reply_markup=materials_list(data['lesson_id'], materials)
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.finish()


# ============================================================
#                    MATERIAL KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:material:view:")
async def view_material(call: types.CallbackQuery):
    """Material tafsilotlarini ko'rish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    material_id = int(call.data.split(":")[-1])
    material = user_db.get_material(material_id)

    if not material:
        await call.answer("❌ Material topilmadi!", show_alert=True)
        return

    icon = FILE_TYPE_ICONS.get(material['file_type'], '📎')
    size_kb = (material.get('file_size') or 0) / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

    text = f"""
{icon} <b>{material['name']}</b>

📹 Dars: {material['lesson_name']}
🔢 Tartib: {material['order_num']}

📊 <b>Ma'lumotlar:</b>
├ Turi: {material['file_type'].upper()}
├ Hajmi: {size_str}
└ Qo'shilgan: {material['created_at'][:10]}

📄 <b>Tavsif:</b>
{material.get('description') or '<i>Tavsif yo\'q</i>'}

⬇️ Amal tanlang:
"""

    await call.message.edit_text(
        text,
        reply_markup=material_detail(material_id, material['lesson_id'])
    )
    await call.answer()


# ============================================================
#                    MATERIAL YUKLASH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:material:download:")
async def download_material(call: types.CallbackQuery):
    """Materialni yuklab olish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    material_id = int(call.data.split(":")[-1])
    material = user_db.get_material(material_id)

    if not material:
        await call.answer("❌ Material topilmadi!", show_alert=True)
        return

    await call.answer("📥 Fayl yuborilmoqda...")

    icon = FILE_TYPE_ICONS.get(material['file_type'], '📎')
    caption = f"{icon} <b>{material['name']}</b>\n\n📹 Dars: {material['lesson_name']}"

    try:
        if material['file_type'] == 'image':
            await bot.send_photo(
                call.from_user.id,
                material['file_id'],
                caption=caption
            )
        else:
            await bot.send_document(
                call.from_user.id,
                material['file_id'],
                caption=caption
            )
    except Exception as e:
        await call.message.answer(f"❌ Faylni yuborishda xato: {e}")


# ============================================================
#                    MATERIAL TAHRIRLASH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:material:edit:")
async def edit_material_menu(call: types.CallbackQuery, state: FSMContext):
    """Material tahrirlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    material_id = int(call.data.split(":")[-1])
    material = user_db.get_material(material_id)

    if not material:
        await call.answer("❌ Material topilmadi!", show_alert=True)
        return

    await state.update_data(
        material_id=material_id,
        lesson_id=material['lesson_id']
    )

    await call.message.edit_text(
        f"✏️ <b>Materialni tahrirlash</b>\n\n"
        f"📎 {material['name']}\n\n"
        f"Yangi nomni kiriting:"
    )

    await call.message.answer("⌨️ Yangi nom:", reply_markup=admin_skip_button())
    await MaterialStates.edit_name.set()
    await call.answer()


@dp.message_handler(state=MaterialStates.edit_name)
async def edit_material_name(message: types.Message, state: FSMContext):
    """Material nomini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    data = await state.get_data()
    material_id = data['material_id']

    if message.text == "⏩ O'tkazib yuborish":
        # Tavsifga o'tish
        await message.answer(
            "📄 <b>Tavsifni tahrirlash</b>\n\n"
            "Yangi tavsifni kiriting:",
            reply_markup=admin_skip_button()
        )
        await MaterialStates.edit_description.set()
        return

    new_name = message.text.strip()

    if len(new_name) < 2 or len(new_name) > 150:
        await message.answer("❌ Nom 2-150 belgi orasida bo'lishi kerak!")
        return

    if user_db.update_material(material_id, name=new_name):
        await state.update_data(new_name=new_name)

        await message.answer(
            f"✅ Nom yangilandi: <b>{new_name}</b>\n\n"
            f"📄 Tavsifni ham yangilamoqchimisiz?",
            reply_markup=admin_skip_button()
        )
        await MaterialStates.edit_description.set()
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()


@dp.message_handler(state=MaterialStates.edit_description)
async def edit_material_description(message: types.Message, state: FSMContext):
    """Material tavsifini yangilash"""
    data = await state.get_data()
    material_id = data['material_id']
    lesson_id = data['lesson_id']

    if message.text == "❌ Bekor qilish" or message.text == "⏩ O'tkazib yuborish":
        await state.finish()
        await message.answer("✅ Tayyor!", reply_markup=types.ReplyKeyboardRemove())

        # Materiallar ro'yxatiga qaytish
        materials = user_db.get_lesson_materials(lesson_id)
        await message.answer(
            "📎 Materiallar:",
            reply_markup=materials_list(lesson_id, materials)
        )
        return

    new_desc = message.text.strip()

    if len(new_desc) > 300:
        await message.answer("❌ Tavsif 300 belgidan oshmasligi kerak!")
        return

    if user_db.update_material(material_id, description=new_desc):
        await message.answer(
            "✅ Tavsif yangilandi!",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Materiallar ro'yxatiga qaytish
        materials = user_db.get_lesson_materials(lesson_id)
        await message.answer(
            "📎 Materiallar:",
            reply_markup=materials_list(lesson_id, materials)
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


# ============================================================
#                    MATERIALNI O'CHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:material:delete:")
async def delete_material_confirm(call: types.CallbackQuery):
    """Materialni o'chirishni tasdiqlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    material_id = int(call.data.split(":")[-1])
    material = user_db.get_material(material_id)

    if not material:
        await call.answer("❌ Material topilmadi!", show_alert=True)
        return

    icon = FILE_TYPE_ICONS.get(material['file_type'], '📎')

    text = f"""
🗑 <b>Materialni o'chirish</b>

{icon} {material['name']}

❓ Rostdan ham o'chirmoqchimisiz?
"""

    await call.message.edit_text(
        text,
        reply_markup=confirm_action("material_delete", material_id)
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:confirm:material_delete:")
async def delete_material_execute(call: types.CallbackQuery):
    """Materialni o'chirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    material_id = int(call.data.split(":")[-1])
    material = user_db.get_material(material_id)

    if not material:
        await call.answer("❌ Material topilmadi!", show_alert=True)
        return

    lesson_id = material['lesson_id']

    if user_db.delete_material(material_id):
        await call.answer("✅ Material o'chirildi!", show_alert=True)

        # Materiallar ro'yxatiga qaytish
        materials = user_db.get_lesson_materials(lesson_id)
        lesson = user_db.get_lesson(lesson_id)

        if not materials:
            text = f"""
📎 <b>Dars materiallari</b>

📹 Dars: {lesson['name']}

📭 Hozircha materiallar yo'q.
"""
        else:
            text = f"""
📎 <b>Dars materiallari</b>

📹 Dars: {lesson['name']}
📊 Jami: {len(materials)} ta material
"""

        await call.message.edit_text(text, reply_markup=materials_list(lesson_id, materials))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:cancel:material_delete:")
async def cancel_delete_material(call: types.CallbackQuery):
    """Material o'chirishni bekor qilish"""
    material_id = int(call.data.split(":")[-1])
    material = user_db.get_material(material_id)

    if material:
        icon = FILE_TYPE_ICONS.get(material['file_type'], '📎')
        size_kb = (material.get('file_size') or 0) / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

        text = f"""
{icon} <b>{material['name']}</b>

📹 Dars: {material['lesson_name']}

📊 <b>Ma'lumotlar:</b>
├ Turi: {material['file_type'].upper()}
└ Hajmi: {size_str}

📄 <b>Tavsif:</b>
{material.get('description') or '<i>Tavsif yo\'q</i>'}
"""

        await call.message.edit_text(
            text,
            reply_markup=material_detail(material_id, material['lesson_id'])
        )

    await call.answer("❌ Bekor qilindi")