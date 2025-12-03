"""
Admin Lessons Handler
=====================
Darslarni qo'shish, tahrirlash, o'chirish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import (
    lessons_list,
    lesson_detail,
    lesson_edit_menu,
    confirm_action
)
from keyboards.default.admin_keyboards import (
    admin_cancel_button,
    admin_skip_button,
    admin_confirm_keyboard
)
from states.admin_states import LessonStates


# ============================================================
#                    DARSLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text_startswith="admin:lesson:list:")
async def show_lessons_list(call: types.CallbackQuery):
    """Darslar ro'yxatini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    module_id = int(call.data.split(":")[-1])
    module = user_db.get_module(module_id)

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    lessons = user_db.get_module_lessons(module_id, active_only=False)

    if not lessons:
        text = f"""
📹 <b>Darslar</b>

📁 Modul: {module['name']}
📚 Kurs: {module['course_name']}

📭 Hozircha darslar yo'q.

Yangi dars qo'shish uchun tugmani bosing.
"""
    else:
        text = f"""
📹 <b>Darslar</b>

📁 Modul: {module['name']}
📚 Kurs: {module['course_name']}
📊 Jami: {len(lessons)} ta dars

✅ - Faol | 🆓 - Bepul | 📝 - Test bor

⬇️ Darsni tanlang:
"""

    await call.message.edit_text(text, reply_markup=lessons_list(module_id, lessons))
    await call.answer()


# ============================================================
#                    DARS QO'SHISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:lesson:add:")
async def add_lesson_start(call: types.CallbackQuery, state: FSMContext):
    """Yangi dars qo'shishni boshlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    module_id = int(call.data.split(":")[-1])
    module = user_db.get_module(module_id)

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    await state.update_data(
        module_id=module_id,
        module_name=module['name'],
        course_id=module['course_id']
    )

    await call.message.edit_text(
        f"📹 <b>Yangi dars qo'shish</b>\n\n"
        f"📁 Modul: {module['name']}\n\n"
        f"📝 Dars nomini kiriting:\n\n"
        f"<i>Masalan: Kompyuterni yoqish va o'chirish</i>"
    )

    await call.message.answer(
        "⌨️ Dars nomini yozing:",
        reply_markup=admin_cancel_button()
    )

    await LessonStates.add_name.set()
    await call.answer()


@dp.message_handler(state=LessonStates.add_name)
async def add_lesson_name(message: types.Message, state: FSMContext):
    """Dars nomini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    lesson_name = message.text.strip()

    if len(lesson_name) < 2:
        await message.answer("❌ Dars nomi kamida 2 ta belgidan iborat bo'lishi kerak!")
        return

    if len(lesson_name) > 150:
        await message.answer("❌ Dars nomi 150 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(name=lesson_name)

    await message.answer(
        f"✅ Dars nomi: <b>{lesson_name}</b>\n\n"
        f"📄 Endi dars tavsifini kiriting:\n\n"
        f"<i>Masalan: Bu darsda kompyuterni to'g'ri yoqish va xavfsiz o'chirishni o'rganamiz</i>",
        reply_markup=admin_skip_button()
    )

    await LessonStates.add_description.set()


@dp.message_handler(state=LessonStates.add_description)
async def add_lesson_description(message: types.Message, state: FSMContext):
    """Dars tavsifini qabul qilish"""
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

    await message.answer(
        "📹 <b>Video yuklash</b>\n\n"
        "Dars videosini yuboring.\n\n"
        "<i>Diqqat: Video Telegram serveriga yuklanadi va file_id saqlanadi.</i>\n\n"
        "Keyinroq qo'shish uchun \"O'tkazib yuborish\" tugmasini bosing.",
        reply_markup=admin_skip_button()
    )

    await LessonStates.add_video.set()


@dp.message_handler(state=LessonStates.add_video, content_types=['video'])
async def add_lesson_video(message: types.Message, state: FSMContext):
    """Dars videosini qabul qilish"""
    video = message.video
    video_file_id = video.file_id
    video_duration = video.duration

    await state.update_data(
        video_file_id=video_file_id,
        video_duration=video_duration
    )

    duration_str = f"{video_duration // 60}:{video_duration % 60:02d}" if video_duration else "Noma'lum"

    await message.answer(
        f"✅ Video qabul qilindi!\n"
        f"⏱ Davomiyligi: {duration_str}\n\n"
        f"🆓 Bu dars bepul bo'lsinmi?\n\n"
        f"Bepul darslar ro'yxatdan o'tmagan foydalanuvchilarga ham ko'rinadi.",
        reply_markup=admin_confirm_keyboard()
    )

    await LessonStates.add_is_free.set()


@dp.message_handler(state=LessonStates.add_video)
async def add_lesson_video_text(message: types.Message, state: FSMContext):
    """Video o'rniga matn kelsa"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        await state.update_data(video_file_id=None, video_duration=None)

        await message.answer(
            "🆓 Bu dars bepul bo'lsinmi?\n\n"
            "Bepul darslar ro'yxatdan o'tmagan foydalanuvchilarga ham ko'rinadi.",
            reply_markup=admin_confirm_keyboard()
        )

        await LessonStates.add_is_free.set()
    else:
        await message.answer("❌ Iltimos, video yuboring yoki \"O'tkazib yuborish\" tugmasini bosing!")


@dp.message_handler(state=LessonStates.add_is_free)
async def add_lesson_is_free(message: types.Message, state: FSMContext):
    """Dars bepul/pullik ekanligini belgilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "✅ Ha":
        is_free = True
    elif message.text == "❌ Yo'q":
        is_free = False
    else:
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")
        return

    await state.update_data(is_free=is_free)

    # Ma'lumotlarni ko'rsatish
    data = await state.get_data()

    video_status = "✅ Yuklangan" if data.get('video_file_id') else "❌ Yuklanmagan"
    free_status = "🆓 Ha" if is_free else "💰 Yo'q"

    text = f"""
📹 <b>Yangi dars</b>

📁 Modul: {data['module_name']}
📝 Nom: <b>{data['name']}</b>
📄 Tavsif: {data.get('description') or '<i>Yoq</i>'}
🎬 Video: {video_status}
🆓 Bepul: {free_status}

✅ Tasdiqlaysizmi?
"""

    await message.answer(text, reply_markup=admin_confirm_keyboard())
    await LessonStates.add_confirm.set()


@dp.message_handler(state=LessonStates.add_confirm)
async def add_lesson_confirm(message: types.Message, state: FSMContext):
    """Dars qo'shishni tasdiqlash"""
    if message.text == "❌ Yo'q" or message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text != "✅ Ha":
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")
        return

    data = await state.get_data()

    # Darsni qo'shish
    lesson_id = user_db.add_lesson(
        module_id=data['module_id'],
        name=data['name'],
        description=data.get('description'),
        video_file_id=data.get('video_file_id'),
        video_duration=data.get('video_duration'),
        is_free=data.get('is_free', False)
    )

    if lesson_id:
        await message.answer(
            f"✅ Dars muvaffaqiyatli qo'shildi!\n\n"
            f"📹 <b>{data['name']}</b>\n"
            f"🆔 ID: {lesson_id}\n\n"
            f"Endi bu darsga materiallar va test qo'shishingiz mumkin.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Dars tafsilotlarini ko'rsatish
        await message.answer(
            "📹 Dars tafsilotlari:",
            reply_markup=lesson_detail(
                lesson_id,
                data['module_id'],
                has_test=False,
                is_free=data.get('is_free', False)
            )
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.finish()


# ============================================================
#                    DARS KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:lesson:view:")
async def view_lesson(call: types.CallbackQuery):
    """Dars tafsilotlarini ko'rish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    # Materiallar soni
    materials_count = user_db.count_lesson_materials(lesson_id)

    # Status belgilari
    status = "✅ Faol" if lesson['is_active'] else "❌ Nofaol"
    free_status = "🆓 Bepul" if lesson['is_free'] else "💰 Pullik"
    video_status = "✅ Bor" if lesson['video_file_id'] else "❌ Yo'q"
    test_status = "✅ Bor" if lesson['has_test'] else "❌ Yo'q"

    # Video davomiyligi
    if lesson['video_duration']:
        duration = f"{lesson['video_duration'] // 60}:{lesson['video_duration'] % 60:02d}"
    else:
        duration = "Noma'lum"

    text = f"""
📹 <b>{lesson['name']}</b>

{status} | {free_status}

📁 Modul: {lesson['module_name']}
🔢 Tartib: {lesson['order_num']}

📄 <b>Tavsif:</b>
{lesson.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Ma'lumotlar:</b>
├ 🎬 Video: {video_status}
├ ⏱ Davomiylik: {duration}
├ 📝 Test: {test_status}
└ 📎 Materiallar: {materials_count} ta

⬇️ Amal tanlang:
"""

    await call.message.edit_text(
        text,
        reply_markup=lesson_detail(
            lesson_id,
            lesson['module_id'],
            lesson['has_test'],
            lesson['is_free']
        )
    )
    await call.answer()


# ============================================================
#                    VIDEO KO'RISH/YUKLASH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:lesson:video:")
async def show_lesson_video(call: types.CallbackQuery):
    """Dars videosini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    if not lesson['video_file_id']:
        await call.answer("❌ Bu darsda video yo'q!", show_alert=True)
        return

    await call.answer("📹 Video yuborilmoqda...")

    try:
        await bot.send_video(
            call.from_user.id,
            lesson['video_file_id'],
            caption=f"📹 <b>{lesson['name']}</b>\n\n"
                    f"📁 Modul: {lesson['module_name']}",
            protect_content=True  # Forward qilishni taqiqlash
        )
    except Exception as e:
        await call.message.answer(f"❌ Videoni yuborishda xato: {e}")


# ============================================================
#                    DARS TAHRIRLASH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:lesson:edit:")
async def edit_lesson_menu(call: types.CallbackQuery, state: FSMContext):
    """Dars tahrirlash menyusi"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    parts = call.data.split(":")

    if len(parts) == 5:
        # Aniq maydonni tahrirlash
        field = parts[3]
        lesson_id = int(parts[4])

        lesson = user_db.get_lesson(lesson_id)
        if not lesson:
            await call.answer("❌ Dars topilmadi!", show_alert=True)
            return

        await state.update_data(lesson_id=lesson_id, module_id=lesson['module_id'])

        if field == "name":
            await call.message.edit_text(
                f"📝 <b>Dars nomini tahrirlash</b>\n\n"
                f"Hozirgi nom: {lesson['name']}\n\n"
                f"Yangi nomni kiriting:"
            )
            await call.message.answer("⌨️ Yangi nom:", reply_markup=admin_cancel_button())
            await LessonStates.edit_name.set()

        elif field == "desc":
            await call.message.edit_text(
                f"📄 <b>Dars tavsifini tahrirlash</b>\n\n"
                f"Hozirgi tavsif: {lesson.get('description') or 'Yo`q'}\n\n"
                f"Yangi tavsifni kiriting:"
            )
            await call.message.answer("⌨️ Yangi tavsif:", reply_markup=admin_skip_button())
            await LessonStates.edit_description.set()

        elif field == "video":
            await call.message.edit_text(
                f"📹 <b>Dars videosini tahrirlash</b>\n\n"
                f"Yangi videoni yuboring:"
            )
            await call.message.answer("📹 Video yuboring:", reply_markup=admin_cancel_button())
            await LessonStates.edit_video.set()

        elif field == "order":
            await call.message.edit_text(
                f"🔢 <b>Dars tartibini tahrirlash</b>\n\n"
                f"Hozirgi tartib: {lesson['order_num']}\n\n"
                f"Yangi tartib raqamini kiriting:"
            )
            await call.message.answer("⌨️ Tartib raqami:", reply_markup=admin_cancel_button())
            await LessonStates.edit_order.set()

    else:
        # Tahrirlash menyusi
        lesson_id = int(parts[3])
        lesson = user_db.get_lesson(lesson_id)

        if not lesson:
            await call.answer("❌ Dars topilmadi!", show_alert=True)
            return

        text = f"""
✏️ <b>Darsni tahrirlash</b>

📹 {lesson['name']}

Qaysi maydonni tahrirlamoqchisiz?
"""

        await call.message.edit_text(text, reply_markup=lesson_edit_menu(lesson_id))

    await call.answer()


@dp.message_handler(state=LessonStates.edit_name)
async def edit_lesson_name(message: types.Message, state: FSMContext):
    """Dars nomini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    new_name = message.text.strip()

    if len(new_name) < 2 or len(new_name) > 150:
        await message.answer("❌ Nom 2-150 belgi orasida bo'lishi kerak!")
        return

    data = await state.get_data()
    lesson_id = data['lesson_id']

    if user_db.update_lesson(lesson_id, name=new_name):
        await message.answer(
            f"✅ Dars nomi yangilandi!\n\n"
            f"📹 Yangi nom: <b>{new_name}</b>",
            reply_markup=types.ReplyKeyboardRemove()
        )

        lesson = user_db.get_lesson(lesson_id)
        await message.answer(
            "📹 Dars:",
            reply_markup=lesson_detail(
                lesson_id,
                lesson['module_id'],
                lesson['has_test'],
                lesson['is_free']
            )
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=LessonStates.edit_description)
async def edit_lesson_description(message: types.Message, state: FSMContext):
    """Dars tavsifini yangilash"""
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
    lesson_id = data['lesson_id']

    if user_db.update_lesson(lesson_id, description=new_desc):
        await message.answer(
            "✅ Dars tavsifi yangilandi!",
            reply_markup=types.ReplyKeyboardRemove()
        )

        lesson = user_db.get_lesson(lesson_id)
        await message.answer(
            "📹 Dars:",
            reply_markup=lesson_detail(
                lesson_id,
                lesson['module_id'],
                lesson['has_test'],
                lesson['is_free']
            )
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=LessonStates.edit_video, content_types=['video'])
async def edit_lesson_video(message: types.Message, state: FSMContext):
    """Dars videosini yangilash"""
    video = message.video

    data = await state.get_data()
    lesson_id = data['lesson_id']

    if user_db.update_lesson(
            lesson_id,
            video_file_id=video.file_id,
            video_duration=video.duration
    ):
        duration = f"{video.duration // 60}:{video.duration % 60:02d}" if video.duration else "Noma'lum"

        await message.answer(
            f"✅ Video yangilandi!\n\n"
            f"⏱ Davomiylik: {duration}",
            reply_markup=types.ReplyKeyboardRemove()
        )

        lesson = user_db.get_lesson(lesson_id)
        await message.answer(
            "📹 Dars:",
            reply_markup=lesson_detail(
                lesson_id,
                lesson['module_id'],
                lesson['has_test'],
                lesson['is_free']
            )
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(state=LessonStates.edit_video)
async def edit_lesson_video_text(message: types.Message, state: FSMContext):
    """Video o'rniga matn kelsa"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    await message.answer("❌ Iltimos, video yuboring!")


@dp.message_handler(state=LessonStates.edit_order)
async def edit_lesson_order(message: types.Message, state: FSMContext):
    """Dars tartibini yangilash"""
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
    lesson_id = data['lesson_id']

    if user_db.update_lesson(lesson_id, order_num=new_order):
        await message.answer(
            f"✅ Dars tartibi yangilandi!\n\n"
            f"🔢 Yangi tartib: <b>{new_order}</b>",
            reply_markup=types.ReplyKeyboardRemove()
        )

        lesson = user_db.get_lesson(lesson_id)
        await message.answer(
            "📹 Dars:",
            reply_markup=lesson_detail(
                lesson_id,
                lesson['module_id'],
                lesson['has_test'],
                lesson['is_free']
            )
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


# ============================================================
#                    BEPUL/PULLIK QILISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:lesson:free:")
async def make_lesson_free(call: types.CallbackQuery):
    """Darsni bepul qilish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])

    if user_db.update_lesson(lesson_id, is_free=True):
        await call.answer("✅ Dars bepul qilindi!", show_alert=True)

        lesson = user_db.get_lesson(lesson_id)
        materials_count = user_db.count_lesson_materials(lesson_id)

        text = f"""
📹 <b>{lesson['name']}</b>

✅ Faol | 🆓 Bepul

📁 Modul: {lesson['module_name']}
🔢 Tartib: {lesson['order_num']}

📄 <b>Tavsif:</b>
{lesson.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Ma'lumotlar:</b>
├ 🎬 Video: {'✅ Bor' if lesson['video_file_id'] else '❌ Yo`q'}
├ 📝 Test: {'✅ Bor' if lesson['has_test'] else '❌ Yo`q'}
└ 📎 Materiallar: {materials_count} ta
"""

        await call.message.edit_text(
            text,
            reply_markup=lesson_detail(
                lesson_id,
                lesson['module_id'],
                lesson['has_test'],
                True
            )
        )
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:lesson:paid:")
async def make_lesson_paid(call: types.CallbackQuery):
    """Darsni pullik qilish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])

    if user_db.update_lesson(lesson_id, is_free=False):
        await call.answer("✅ Dars pullik qilindi!", show_alert=True)

        lesson = user_db.get_lesson(lesson_id)
        materials_count = user_db.count_lesson_materials(lesson_id)

        text = f"""
📹 <b>{lesson['name']}</b>

✅ Faol | 💰 Pullik

📁 Modul: {lesson['module_name']}
🔢 Tartib: {lesson['order_num']}

📄 <b>Tavsif:</b>
{lesson.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Ma'lumotlar:</b>
├ 🎬 Video: {'✅ Bor' if lesson['video_file_id'] else '❌ Yo`q'}
├ 📝 Test: {'✅ Bor' if lesson['has_test'] else '❌ Yo`q'}
└ 📎 Materiallar: {materials_count} ta
"""

        await call.message.edit_text(
            text,
            reply_markup=lesson_detail(
                lesson_id,
                lesson['module_id'],
                lesson['has_test'],
                False
            )
        )
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


# ============================================================
#                    DARSNI O'CHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:lesson:delete:")
async def delete_lesson_confirm(call: types.CallbackQuery):
    """Darsni o'chirishni tasdiqlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    materials_count = user_db.count_lesson_materials(lesson_id)

    text = f"""
🗑 <b>Darsni o'chirish</b>

📹 {lesson['name']}

⚠️ Diqqat! Dars o'chirilsa:
• Video
• {materials_count} ta material
• Test va savollar
• Barcha progresslar

ham o'chib ketadi!

❓ Rostdan ham o'chirmoqchimisiz?
"""

    await call.message.edit_text(
        text,
        reply_markup=confirm_action("lesson_delete", lesson_id)
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:confirm:lesson_delete:")
async def delete_lesson_execute(call: types.CallbackQuery):
    """Darsni o'chirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    module_id = lesson['module_id']

    if user_db.delete_lesson(lesson_id):
        await call.answer("✅ Dars o'chirildi!", show_alert=True)

        # Darslar ro'yxatiga qaytish
        lessons = user_db.get_module_lessons(module_id, active_only=False)
        module = user_db.get_module(module_id)

        text = f"""
📹 <b>Darslar</b>

📁 Modul: {module['name']}
📊 Jami: {len(lessons)} ta dars

⬇️ Darsni tanlang:
"""

        await call.message.edit_text(text, reply_markup=lessons_list(module_id, lessons))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:cancel:lesson_delete:")
async def cancel_delete_lesson(call: types.CallbackQuery):
    """Dars o'chirishni bekor qilish"""
    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if lesson:
        materials_count = user_db.count_lesson_materials(lesson_id)

        text = f"""
📹 <b>{lesson['name']}</b>

{'✅ Faol' if lesson['is_active'] else '❌ Nofaol'} | {'🆓 Bepul' if lesson['is_free'] else '💰 Pullik'}

📁 Modul: {lesson['module_name']}

📊 <b>Ma'lumotlar:</b>
├ 🎬 Video: {'✅ Bor' if lesson['video_file_id'] else '❌ Yo`q'}
├ 📝 Test: {'✅ Bor' if lesson['has_test'] else '❌ Yo`q'}
└ 📎 Materiallar: {materials_count} ta
"""

        await call.message.edit_text(
            text,
            reply_markup=lesson_detail(
                lesson_id,
                lesson['module_id'],
                lesson['has_test'],
                lesson['is_free']
            )
        )

    await call.answer("❌ Bekor qilindi")