"""
User Lessons Handler
====================
Darslarni ko'rish va video tomosha qilish handlerlari
"""

from aiogram import types

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    lessons_list,
    lesson_view,
    lesson_completed_menu,
    materials_list
)
from keyboards.default.user_keyboards import main_menu


# ============================================================
#                    DARSLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text_startswith="user:lessons:")
async def show_module_lessons(call: types.CallbackQuery):
    """Modul darslarini ko'rsatish"""
    module_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    module = user_db.get_module(module_id)

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, module['course_id']) if user_id else False

    lessons = user_db.get_module_lessons(module_id, active_only=True)

    if not lessons:
        await call.answer("📭 Bu modulda darslar yo'q", show_alert=True)
        return

    # Agar dostup bo'lsa, progressni olish
    if has_access:
        # Birinchi darsni ochish (agar progress yo'q bo'lsa)
        first_lesson = lessons[0]
        status = user_db.get_lesson_status(user_id, first_lesson['id'])

        if status == 'locked':
            user_db.unlock_lesson(user_id, first_lesson['id'])

    # Har bir dars uchun status
    lessons_with_status = []
    for lesson in lessons:
        if has_access:
            status = user_db.get_lesson_status(user_id, lesson['id'])
        else:
            # Bepul dars yoki yo'q
            status = 'free' if lesson['is_free'] else 'locked'

        lessons_with_status.append({
            **lesson,
            'status': status
        })

    text = f"""
📹 <b>Darslar</b>

📁 Modul: {module['name']}
📚 Kurs: {module['course_name']}
📊 Jami: {len(lessons)} ta dars

✅ - Tugagan
🔓 - Ochiq
🔒 - Yopiq
🆓 - Bepul

⬇️ Darsni tanlang:
"""

    await call.message.edit_text(
        text,
        reply_markup=lessons_list(module_id, lessons_with_status, has_access)
    )
    await call.answer()


# ============================================================
#                    DARS KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:lesson:view:")
async def view_lesson(call: types.CallbackQuery):
    """Darsni ko'rish"""
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    module = user_db.get_module(lesson['module_id'])

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, module['course_id']) if user_id else False

    # Bepul dars yoki dostup bor
    if not lesson['is_free'] and not has_access:
        await call.answer("🔒 Bu darsni ko'rish uchun kursni sotib oling!", show_alert=True)
        return

    # Status tekshirish
    if has_access:
        status = user_db.get_lesson_status(user_id, lesson_id)

        if status == 'locked':
            await call.answer("🔒 Avvalgi darslarni tugating!", show_alert=True)
            return

    # Materiallar soni
    materials_count = user_db.count_lesson_materials(lesson_id)

    # Video davomiyligi
    if lesson['video_duration']:
        duration = f"{lesson['video_duration'] // 60}:{lesson['video_duration'] % 60:02d}"
    else:
        duration = "Noma'lum"

    # Status text
    if has_access:
        status = user_db.get_lesson_status(user_id, lesson_id)
        if status == 'completed':
            status_text = "✅ Tugallangan"
        else:
            status_text = "🔓 Ochiq"
    else:
        status_text = "🆓 Bepul dars"

    text = f"""
📹 <b>{lesson['name']}</b>

{status_text}

📁 Modul: {lesson['module_name']}
⏱ Davomiylik: {duration}

📄 <b>Tavsif:</b>
{lesson.get('description') or '<i>Tavsif yoq</i>'}

📊 <b>Ma'lumotlar:</b>
├ 📎 Materiallar: {materials_count} ta
└ 📝 Test: {'Bor' if lesson['has_test'] else 'Yoq'}

⬇️ Tanlang:
"""

    await call.message.edit_text(
        text,
        reply_markup=lesson_view(
            lesson_id,
            lesson['module_id'],
            has_video=bool(lesson['video_file_id']),
            has_materials=materials_count > 0,
            has_test=lesson['has_test'],
            is_completed=(status == 'completed') if has_access else False,
            has_access=has_access or lesson['is_free']
        )
    )
    await call.answer()


# ============================================================
#                    VIDEO KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:video:")
async def watch_video(call: types.CallbackQuery):
    """Videoni ko'rish"""
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    if not lesson['video_file_id']:
        await call.answer("❌ Bu darsda video yo'q!", show_alert=True)
        return

    module = user_db.get_module(lesson['module_id'])

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, module['course_id']) if user_id else False

    if not lesson['is_free'] and not has_access:
        await call.answer("🔒 Bu videoni ko'rish uchun kursni sotib oling!", show_alert=True)
        return

    await call.answer("📹 Video yuborilmoqda...")

    try:
        # Video yuborish
        await bot.send_video(
            call.from_user.id,
            lesson['video_file_id'],
            caption=f"📹 <b>{lesson['name']}</b>\n\n"
                    f"📁 Modul: {lesson['module_name']}",
            protect_content=True  # Forward qilishni taqiqlash
        )

        # Videoni ko'rganini belgilash (agar dostup bo'lsa va video ko'rilmagan bo'lsa)
        if has_access:
            status = user_db.get_lesson_status(user_id, lesson_id)
            if status == 'unlocked':
                # Ko'rilgan, lekin hali tugallanmagan
                pass

    except Exception as e:
        await call.message.answer(f"❌ Videoni yuborishda xato: {e}")


# ============================================================
#                    MATERIALLAR
# ============================================================

@dp.callback_query_handler(text_startswith="user:materials:")
async def show_lesson_materials(call: types.CallbackQuery):
    """Dars materiallarini ko'rsatish"""
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    module = user_db.get_module(lesson['module_id'])

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, module['course_id']) if user_id else False

    if not lesson['is_free'] and not has_access:
        await call.answer("🔒 Bu materiallarni ko'rish uchun kursni sotib oling!", show_alert=True)
        return

    materials = user_db.get_lesson_materials(lesson_id)

    if not materials:
        await call.answer("📭 Bu darsda materiallar yo'q", show_alert=True)
        return

    text = f"""
📎 <b>Dars materiallari</b>

📹 Dars: {lesson['name']}
📊 Jami: {len(materials)} ta material

⬇️ Yuklab olish uchun tanlang:
"""

    await call.message.edit_text(text, reply_markup=materials_list(lesson_id, materials))
    await call.answer()


@dp.callback_query_handler(text_startswith="user:material:download:")
async def download_material(call: types.CallbackQuery):
    """Materialni yuklab olish"""
    material_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    material = user_db.get_material(material_id)

    if not material:
        await call.answer("❌ Material topilmadi!", show_alert=True)
        return

    lesson = user_db.get_lesson(material['lesson_id'])
    module = user_db.get_module(lesson['module_id'])

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, module['course_id']) if user_id else False

    if not lesson['is_free'] and not has_access:
        await call.answer("🔒 Bu materialni yuklab olish uchun kursni sotib oling!", show_alert=True)
        return

    await call.answer("📥 Fayl yuborilmoqda...")

    # Fayl ikonkasi
    file_icons = {
        'pdf': '📕',
        'pptx': '📊',
        'docx': '📄',
        'xlsx': '📗',
        'image': '🖼',
        'other': '📎'
    }
    icon = file_icons.get(material['file_type'], '📎')

    caption = f"{icon} <b>{material['name']}</b>\n\n📹 Dars: {lesson['name']}"

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
#                    DARSNI TUGATISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:complete:")
async def complete_lesson(call: types.CallbackQuery):
    """Darsni tugatish"""
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    module = user_db.get_module(lesson['module_id'])

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, module['course_id']) if user_id else False

    if not has_access:
        await call.answer("🔒 Avval kursni sotib oling!", show_alert=True)
        return

    # Test bormi tekshirish
    if lesson['has_test']:
        # Testni topshirganmi tekshirish
        test = user_db.get_test_by_lesson(lesson_id)
        if test:
            passed = user_db.has_passed_test(user_id, test['id'])
            if not passed:
                await call.answer("📝 Avval testni topshiring!", show_alert=True)
                return

    # Fikr majburiymi tekshirish
    feedback_required = user_db.get_setting('feedback_required')
    if feedback_required == 'true' or feedback_required == '1':
        has_feedback = user_db.has_feedback(user_id, lesson_id)
        if not has_feedback:
            await call.answer("💬 Avval fikr qoldiring!", show_alert=True)
            # Fikr qoldirish sahifasiga yo'naltirish
            from keyboards.inline.user_keyboards import feedback_prompt
            await call.message.edit_text(
                f"💬 <b>Fikr qoldiring</b>\n\n"
                f"📹 Dars: {lesson['name']}\n\n"
                f"Darsni tugatish uchun fikr qoldirishingiz kerak.",
                reply_markup=feedback_prompt(lesson_id)
            )
            return

    # Darsni tugatish
    user_db.complete_lesson(user_id, lesson_id)

    # Keyingi darsni ochish
    next_lesson = get_next_lesson(lesson_id)

    if next_lesson:
        user_db.unlock_lesson(user_id, next_lesson['id'])

    # Ball qo'shish
    user_db.add_score(telegram_id, 10)  # Har bir dars uchun 10 ball

    await call.answer("✅ Dars tugallandi! +10 ball", show_alert=True)

    # Natija xabari
    text = f"""
✅ <b>Dars tugallandi!</b>

📹 {lesson['name']}
🏆 +10 ball

"""

    if next_lesson:
        text += f"⏭ Keyingi dars: {next_lesson['name']}"
    else:
        # Modul tugadimi tekshirish
        text += "🎉 Siz modulni tugatdingiz!"

        # Kurs tugadimi tekshirish
        course_completed = check_course_completion(user_id, module['course_id'])
        if course_completed:
            text += "\n\n🎓 Tabriklaymiz! Siz kursni tugatdingiz!"

    await call.message.edit_text(
        text,
        reply_markup=lesson_completed_menu(
            lesson_id,
            module['id'],
            next_lesson['id'] if next_lesson else None,
            lesson['has_test']
        )
    )


# ============================================================
#                    KEYINGI DARS
# ============================================================

@dp.callback_query_handler(text_startswith="user:next_lesson:")
async def go_to_next_lesson(call: types.CallbackQuery):
    """Keyingi darsga o'tish"""
    lesson_id = int(call.data.split(":")[-1])

    # view_lesson funksiyasini chaqirish
    call.data = f"user:lesson:view:{lesson_id}"
    await view_lesson(call)


# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def get_next_lesson(current_lesson_id: int) -> dict:
    """Keyingi darsni olish"""
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


def check_course_completion(user_id: int, course_id: int) -> bool:
    """Kurs tugallanganmi tekshirish"""
    # Barcha darslar soni
    total_lessons = user_db.execute(
        """SELECT COUNT(*) FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           WHERE m.course_id = ? AND l.is_active = TRUE AND m.is_active = TRUE""",
        parameters=(course_id,),
        fetchone=True
    )

    # Tugallangan darslar
    completed_lessons = user_db.execute(
        """SELECT COUNT(*) FROM UserProgress up
           JOIN Lessons l ON up.lesson_id = l.id
           JOIN Modules m ON l.module_id = m.id
           WHERE up.user_id = ? AND m.course_id = ? AND up.status = 'completed'""",
        parameters=(user_id, course_id),
        fetchone=True
    )

    total = total_lessons[0] if total_lessons else 0
    completed = completed_lessons[0] if completed_lessons else 0

    return total > 0 and completed >= total