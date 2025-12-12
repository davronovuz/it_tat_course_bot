"""
User Lessons Handler (SODDALASHTIRILGAN)
========================================
Modul ko'rinmaydi - faqat ketma-ket darslar
Dars → Video → Test (agar bor bo'lsa) → Keyingi dars
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    simple_lessons_list,
    lesson_view,
    after_video_with_test,
    after_video_no_test,
    materials_list,
    back_to_lessons
)


# ============================================================
#                    DARSLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text="user:lessons")
async def show_lessons_list(call: types.CallbackQuery):
    """
    Barcha darslar ro'yxati (modul ko'rinmaydi)
    """
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    user_id = user['id']

    # Darslarni olish
    lessons = get_all_lessons_with_status(user_id)

    if not lessons:
        await call.message.edit_text("📭 Darslar topilmadi")
        await call.answer()
        return

    completed = sum(1 for l in lessons if l['status'] == 'completed')
    total = len(lessons)

    text = f"""
📚 <b>Darslar</b>

📊 Progress: {completed}/{total}
"""

    # Avvalgi xabarni o'chirish
    try:
        await call.message.delete()
    except:
        pass

    # Yangi xabar yuborish
    await call.message.answer(text, reply_markup=simple_lessons_list(lessons))

    await call.answer()


# ============================================================
#                    DARS KO'RISH
# ============================================================
@dp.callback_query_handler(text_startswith="user:lesson:")
async def view_lesson(call: types.CallbackQuery):
    """
    Darsni ko'rish - BIRDAN VIDEO CHIQADI
    """
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    user_id = user['id']
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi", show_alert=True)
        return

    # Status tekshirish
    status = get_lesson_status(user_id, lesson_id)

    if status == 'locked':
        await call.answer("🔒 Bu dars yopiq! Avvalgi darsni yakunlang.", show_alert=True)
        return

    # Eski xabarni o'chirish
    try:
        await call.message.delete()
    except:
        pass

    await call.answer("📹 Video yuborilmoqda...")

    # Video yuborish
    video_file_id = lesson.get('video_file_id')
    caption = f"📹 <b>{lesson['name']}</b>\n\n{lesson.get('description') or ''}"

    if video_file_id:
        try:
            await bot.send_video(
                telegram_id,
                video_file_id,
                caption=caption,
                protect_content=True
            )
        except:
            await bot.send_message(telegram_id, caption + "\n\n⚠️ Video yuklanmadi")
    else:
        await bot.send_message(telegram_id, caption)

    # Keyingi tugmalar
    has_test = lesson.get('has_test', False)
    materials_count = user_db.count_lesson_materials(lesson_id)
    next_lesson = get_next_lesson(lesson_id)

    # Tugmalar
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    if materials_count > 0:
        keyboard.add(types.InlineKeyboardButton(
            "📎 Materiallar",
            callback_data=f"user:materials:{lesson_id}"
        ))

    if has_test:
        keyboard.add(types.InlineKeyboardButton(
            "📝 Test yechish",
            callback_data=f"user:test:{lesson_id}"
        ))
    else:
        # Test yo'q - darsni avtomatik tugatish
        if status != 'completed':
            complete_lesson_db(user_id, lesson_id)
            user_db.add_score(telegram_id, 10)

        if next_lesson:
            keyboard.add(types.InlineKeyboardButton(
                "⏭ Keyingi dars",
                callback_data=f"user:lesson:{next_lesson['id']}"
            ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:lessons"
    ))

    await bot.send_message(telegram_id, "👇 Davom eting:", reply_markup=keyboard)



# ============================================================
#                    VIDEO KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:video:")
async def watch_video(call: types.CallbackQuery):
    """
    Videoni ko'rish
    Test yo'q bo'lsa - dars avtomatik tugaydi
    """
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    user_id = user['id']

    # Dars ma'lumotlari
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi", show_alert=True)
        return

    # Video bormi
    video_file_id = lesson.get('video_file_id')
    video_url = lesson.get('video_url')

    if not video_file_id and not video_url:
        await call.answer("❌ Bu darsda video yo'q", show_alert=True)
        return

    # Eski xabarni o'chirish
    try:
        await call.message.delete()
    except:
        pass

    await call.answer("📹 Video yuborilmoqda...")

    # Video yuborish
    caption = f"📹 <b>{lesson['name']}</b>"

    try:
        if video_file_id:
            await bot.send_video(
                telegram_id,
                video_file_id,
                caption=caption,
                protect_content=True
            )
        else:
            await bot.send_video(
                telegram_id,
                video_url,
                caption=caption,
                protect_content=True
            )
    except Exception as e:
        await bot.send_message(telegram_id, f"❌ Video yuborishda xato: {e}")
        return

    # Test bormi?
    has_test = lesson.get('has_test', False)
    next_lesson = get_next_lesson(lesson_id)

    if has_test:
        # Test bor - test yechishga yo'naltirish
        text = """
✅ Videoni ko'rdingiz!

Endi testni yeching:
"""
        await bot.send_message(
            telegram_id,
            text,
            reply_markup=after_video_with_test(lesson_id)
        )
    else:
        # Test yo'q - darsni avtomatik tugatish
        current_status = get_lesson_status(user_id, lesson_id)

        if current_status != 'completed':
            # Darsni tugatish
            complete_lesson_db(user_id, lesson_id)

            # Ball qo'shish
            user_db.add_score(telegram_id, 10)

            text = """
✅ Dars tugallandi! +10 ball
"""
        else:
            text = """
✅ Videoni ko'rdingiz!
"""

        await bot.send_message(
            telegram_id,
            text,
            reply_markup=after_video_no_test(next_lesson['id'] if next_lesson else None)
        )


# ============================================================
#                    MATERIALLAR
# ============================================================

@dp.callback_query_handler(text_startswith="user:materials:")
async def show_materials(call: types.CallbackQuery):
    """
    Dars materiallarini ko'rsatish
    """
    lesson_id = int(call.data.split(":")[-1])

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi", show_alert=True)
        return

    materials = user_db.get_lesson_materials(lesson_id)

    if not materials:
        await call.answer("📭 Materiallar yo'q", show_alert=True)
        return

    text = f"""
📎 <b>Materiallar</b>

📹 Dars: {lesson['name']}
"""

    await call.message.edit_text(text, reply_markup=materials_list(lesson_id, materials))
    await call.answer()


@dp.callback_query_handler(text_startswith="user:material:")
async def download_material(call: types.CallbackQuery):
    """
    Materialni yuklab olish
    """
    material_id = int(call.data.split(":")[-1])

    material = user_db.get_material(material_id)

    if not material:
        await call.answer("❌ Material topilmadi", show_alert=True)
        return

    await call.answer("📥 Fayl yuborilmoqda...")

    try:
        if material.get('file_type') == 'image':
            await bot.send_photo(
                call.from_user.id,
                material['file_id'],
                caption=f"📎 {material['name']}"
            )
        else:
            await bot.send_document(
                call.from_user.id,
                material['file_id'],
                caption=f"📎 {material['name']}"
            )
    except Exception as e:
        await call.message.answer(f"❌ Xato: {e}")


# ============================================================
#                    YOPIQ DARS
# ============================================================

@dp.callback_query_handler(text_startswith="user:locked:")
async def locked_lesson(call: types.CallbackQuery):
    """
    Yopiq dars bosilganda
    """
    await call.answer(
        "🔒 Bu dars yopiq!\n\nAvvalgi darsni yakunlang.",
        show_alert=True
    )


# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def get_all_lessons_with_status(user_id: int) -> list:
    """
    Barcha darslarni ketma-ket status bilan olish
    Modul ko'rinmaydi
    """
    # Barcha darslar (modul va kurs bo'yicha tartiblangan)
    lessons = user_db.execute(
        """SELECT l.id, l.name
           FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE l.is_active = TRUE AND m.is_active = TRUE AND c.is_active = TRUE
           ORDER BY c.order_num, m.order_num, l.order_num""",
        fetchall=True
    )

    if not lessons:
        return []

    # User progress
    progress = user_db.execute(
        "SELECT lesson_id, status FROM UserProgress WHERE user_id = ?",
        parameters=(user_id,),
        fetchall=True
    )
    progress_dict = {p[0]: p[1] for p in progress} if progress else {}

    result = []
    order = 0
    prev_completed = True  # Birinchi dars ochiq

    for lesson in lessons:
        order += 1
        lesson_id = lesson[0]
        name = lesson[1]

        user_status = progress_dict.get(lesson_id)

        if user_status == 'completed':
            status = 'completed'
            prev_completed = True
        elif prev_completed:
            status = 'unlocked'
            prev_completed = False
        else:
            status = 'locked'

        result.append({
            'id': lesson_id,
            'order_num': order,
            'name': name,
            'status': status
        })

    return result


def get_lesson_status(user_id: int, lesson_id: int) -> str:
    """
    Bitta dars statusini olish
    """
    lessons = get_all_lessons_with_status(user_id)

    for lesson in lessons:
        if lesson['id'] == lesson_id:
            return lesson['status']

    return 'locked'


def get_next_lesson(current_lesson_id: int) -> dict | None:
    """
    Keyingi darsni olish
    """
    current = user_db.get_lesson(current_lesson_id)
    if not current:
        return None

    # Shu modul ichidagi keyingi dars
    next_in_module = user_db.execute(
        """SELECT id, name FROM Lessons 
           WHERE module_id = ? AND order_num > ? AND is_active = TRUE
           ORDER BY order_num LIMIT 1""",
        parameters=(current['module_id'], current['order_num']),
        fetchone=True
    )

    if next_in_module:
        return {'id': next_in_module[0], 'name': next_in_module[1]}

    # Keyingi modulning birinchi darsi
    module = user_db.get_module(current['module_id'])
    if not module:
        return None

    next_module = user_db.execute(
        """SELECT id FROM Modules 
           WHERE course_id = ? AND order_num > ? AND is_active = TRUE
           ORDER BY order_num LIMIT 1""",
        parameters=(module['course_id'], module['order_num']),
        fetchone=True
    )

    if next_module:
        first_lesson = user_db.execute(
            """SELECT id, name FROM Lessons 
               WHERE module_id = ? AND is_active = TRUE
               ORDER BY order_num LIMIT 1""",
            parameters=(next_module[0],),
            fetchone=True
        )

        if first_lesson:
            return {'id': first_lesson[0], 'name': first_lesson[1]}

    return None


def complete_lesson_db(user_id: int, lesson_id: int):
    """
    Darsni tugatish (bazada)
    """
    # Progress mavjudmi?
    existing = user_db.execute(
        "SELECT id, status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
        parameters=(user_id, lesson_id),
        fetchone=True
    )

    if existing:
        if existing[1] != 'completed':
            user_db.execute(
                """UPDATE UserProgress 
                   SET status = 'completed', completed_at = datetime('now')
                   WHERE user_id = ? AND lesson_id = ?""",
                parameters=(user_id, lesson_id),
                commit=True
            )
    else:
        user_db.execute(
            """INSERT INTO UserProgress (user_id, lesson_id, status, completed_at)
               VALUES (?, ?, 'completed', datetime('now'))""",
            parameters=(user_id, lesson_id),
            commit=True
        )


def check_course_completion(user_id: int) -> bool:
    """
    Kurs tugadimi tekshirish
    """
    # Barcha darslar
    total = user_db.execute(
        """SELECT COUNT(*) FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE l.is_active = TRUE AND m.is_active = TRUE AND c.is_active = TRUE""",
        fetchone=True
    )

    # Tugallangan darslar
    completed = user_db.execute(
        """SELECT COUNT(*) FROM UserProgress 
           WHERE user_id = ? AND status = 'completed'""",
        parameters=(user_id,),
        fetchone=True
    )

    total_count = total[0] if total else 0
    completed_count = completed[0] if completed else 0

    return total_count > 0 and completed_count >= total_count