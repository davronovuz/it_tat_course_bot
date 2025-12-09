"""
User Lessons Handler
====================
Darslarni ko'rish va video tomosha qilish handlerlari
"""

from aiogram import types
from aiogram.utils.exceptions import BadRequest

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    lessons_list,
    lesson_view,
    lesson_completed_menu,
    materials_list
)
from keyboards.default.user_keyboards import main_menu


# ============================================================
#                    YORDAMCHI: XAVFSIZ EDIT
# ============================================================

async def safe_edit_message(message: types.Message, text: str, reply_markup=None):
    """
    Xabar matnini xavfsiz edit qilish:
    - agar text xabar bo'lsa -> edit_text
    - agar video/photo/document bo'lsa -> edit_caption
    - agar baribir xato bo'lsa -> yangi message yuboradi
    """
    try:
        # Oddiy matnli xabar
        if message.text is not None:
            return await message.edit_text(text, reply_markup=reply_markup)

        # Media xabar (video, photo, document, va h.k.)
        if message.caption is not None or message.content_type in (
            "video", "photo", "document", "animation"
        ):
            return await message.edit_caption(text, reply_markup=reply_markup)

        # Default holat
        return await message.edit_text(text, reply_markup=reply_markup)

    except BadRequest:
        # Masalan: "There is no text in the message to edit"
        return await message.bot.send_message(
            message.chat.id,
            text,
            reply_markup=reply_markup
        )


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

    # ✅ Dostupni faqat telegram_id bilan tekshiramiz
    has_access = user_db.has_course_access(telegram_id, module['course_id']) if user_id else False

    lessons = user_db.get_module_lessons(module_id, active_only=True)

    if not lessons:
        await call.answer("📭 Bu modulda darslar yo'q", show_alert=True)
        return

    # Agar dostup bo'lsa, birinchi darsni ochish (agar locked bo'lsa)
    # Birinchi darsni ochish FAQAT shu modul birinchi modul bo'lsa
    # yoki oldingi modul tugagan bo'lsa
    if has_access:
        first_lesson = lessons[0]
        status = user_db.get_lesson_status(telegram_id, first_lesson['id'])

        if status == 'locked':
            # Oldingi modul tugaganmi tekshirish
            prev_module_completed = is_previous_module_completed(telegram_id, module_id)
            if prev_module_completed:
                user_db.unlock_lesson(telegram_id, first_lesson['id'])

    # Har bir dars uchun status
    lessons_with_status = []
    for lesson in lessons:
        if has_access:
            status = user_db.get_lesson_status(telegram_id, lesson['id'])
        else:
            # Bepul dars bo'lsa – free, bo‘lmasa locked
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

    await safe_edit_message(
        call.message,
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

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # ✅ Dostup faqat telegram_id bilan
    has_access = user_db.has_course_access(telegram_id, module['course_id']) if user_id else False

    # Pullik dars + dostup yo'q bo'lsa
    if not lesson['is_free'] and not has_access:
        await call.answer("🔒 Bu darsni ko'rish uchun kursni sotib oling!", show_alert=True)
        return

    # Materiallar soni
    materials_count = user_db.count_lesson_materials(lesson_id)

    # Video davomiyligi
    if lesson['video_duration']:
        duration = f"{lesson['video_duration'] // 60}:{lesson['video_duration'] % 60:02d}"
    else:
        duration = "Noma'lum"

    # Status va status matni
    if has_access:
        status = user_db.get_lesson_status(telegram_id, lesson_id)
        if status == 'completed':
            status_text = "✅ Tugallangan"
        else:
            status_text = "🔓 Ochiq"
    else:
        status = 'free'
        status_text = "🆓 Bepul dars"

    # 🔥 Agar dars tugagan bo‘lsa – keyingi darsni topamiz
    next_lesson = None
    if status == 'completed':
        next_lesson = get_next_lesson(lesson_id)

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
"""

    # ✅ Agar dars tugagan bo‘lsa va keyingi dars bo‘lsa – taklif
    if next_lesson:
        text += f"""

⏭ <b>Keyingi darsni davom ettirishingiz mumkin:</b>
➡️ <i>{next_lesson['name']}</i>
"""

    text += "\n⬇️ Tanlang:"

    await safe_edit_message(
        call.message,
        text,
        reply_markup=lesson_view(
            lesson_id=lesson_id,
            module_id=lesson['module_id'],
            has_video=bool(lesson['video_file_id']),
            has_materials=materials_count > 0,
            has_test=lesson['has_test'],
            is_completed=(status == 'completed'),
            has_access=has_access or lesson['is_free'],
            next_lesson_id=next_lesson['id'] if next_lesson else None,  # 🔥 yangi
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

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # 🔐 Dostup tekshirish – faqat telegram_id bilan
    has_access = user_db.has_course_access(telegram_id, module['course_id']) if user_id else False

    # Pullik dars + dostup yo'q bo'lsa
    if not lesson['is_free'] and not has_access:
        await call.answer("🔒 Bu videoni ko'rish uchun kursni sotib oling!", show_alert=True)
        return

    # Materiallar soni va status
    materials_count = user_db.count_lesson_materials(lesson_id)

    if has_access:
        status = user_db.get_lesson_status(telegram_id, lesson_id)
    else:
        status = 'free' if lesson['is_free'] else 'locked'

    is_completed = (status == 'completed') if has_access else False

    # Eski text xabarni o'chirib yuboramiz, tugmalar videoning ostida bo'lishi uchun
    try:
        await call.message.delete()
    except Exception:
        pass

    await call.answer("📹 Video yuborilmoqda...")

    caption = (
        f"📹 <b>{lesson['name']}</b>\n\n"
        f"📁 Modul: {lesson['module_name']}"
    )

    try:
        await bot.send_video(
            call.from_user.id,
            lesson['video_file_id'],
            caption=caption,
            reply_markup=lesson_view(
                lesson_id=lesson_id,
                module_id=lesson['module_id'],
                has_video=True,
                has_materials=materials_count > 0,
                has_test=lesson['has_test'],
                is_completed=is_completed,
                has_access=has_access or lesson['is_free'],
                next_lesson_id=None  # Video ichida "keyingi dars"ni view_lesson dan boshqaramiz
            ),
            protect_content=True
        )

    except Exception as e:
        await bot.send_message(
            call.from_user.id,
            f"❌ Videoni yuborishda xato: {e}"
        )


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

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # ✅ Dostupni telegram_id bilan tekshiramiz
    has_access = user_db.has_course_access(telegram_id, module['course_id']) if user_id else False

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

    await safe_edit_message(
        call.message,
        text,
        reply_markup=materials_list(lesson_id, materials)
    )
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

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # ✅ Dostupni telegram_id bilan tekshiramiz
    has_access = user_db.has_course_access(telegram_id, module['course_id']) if user_id else False

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

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # ✅ Dostupni telegram_id bilan tekshiramiz
    has_access = user_db.has_course_access(telegram_id, module['course_id']) if user_id else False

    if not has_access:
        await call.answer("🔒 Avval kursni sotib oling!", show_alert=True)
        return

    # Test bormi tekshirish
    if lesson['has_test']:
        test = user_db.get_test_by_lesson(lesson_id)
        if test:
            passed = user_db.has_passed_test(telegram_id, test['id'])
            if not passed:
                await call.answer("📝 Avval testni topshiring!", show_alert=True)
                return

    # Fikr majburiymi tekshirish
    feedback_required = user_db.get_setting('feedback_required')
    if feedback_required == 'true' or feedback_required == '1':
        has_feedback = user_db.has_feedback(telegram_id, lesson_id)
        if not has_feedback:
            await call.answer("💬 Avval fikr qoldiring!", show_alert=True)
            from keyboards.inline.user_keyboards import feedback_prompt
            await safe_edit_message(
                call.message,
                f"💬 <b>Fikr qoldiring</b>\n\n"
                f"📹 Dars: {lesson['name']}\n\n"
                f"Darsni tugatish uchun fikr qoldirishingiz kerak.",
                reply_markup=feedback_prompt(lesson_id)
            )
            return

    # ✅ DB ichida darsni completed qiladi va keyingi darsni ochadi
    user_db.complete_lesson(telegram_id, lesson_id)

    # UI uchun keyingi dars nomini olaylik
    next_lesson = get_next_lesson(lesson_id)

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
        text += "🎉 Siz modulni tugatdingiz!"
        # Kurs tugadimi tekshirish (bu funksiya hali ham user_id bilan ishlaydi)
        course_completed = check_course_completion(user_id, module['course_id'])
        if course_completed:
            text += "\n\n🎓 Tabriklaymiz! Siz kursni tugatdingiz!"

    await safe_edit_message(
        call.message,
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

def get_next_lesson(current_lesson_id: int) -> dict | None:
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


# ============================================================
#                    YOPIQ DARS
# ============================================================

@dp.callback_query_handler(text_startswith="user:locked:")
async def locked_lesson(call: types.CallbackQuery):
    """Yopiq darsni bosganda"""
    await call.answer("🔒 Bu dars yopiq! Avvalgi darsni yakunlang.", show_alert=True)


# ============================================================
#                    ORQAGA - MODULLAR
# ============================================================

@dp.callback_query_handler(text_startswith="user:module:back:")
async def back_to_modules(call: types.CallbackQuery):
    """Modullar ro'yxatiga qaytish"""
    module_id = int(call.data.split(":")[-1])
    module = user_db.get_module(module_id)

    if not module:
        await call.answer("❌ Modul topilmadi!", show_alert=True)
        return

    # Video/media xabarni o'chiramiz
    try:
        await call.message.delete()
    except:
        pass

    # Yangi xabar yuboramiz
    telegram_id = call.from_user.id
    course_id = module['course_id']
    course = user_db.get_course(course_id)

    modules = user_db.get_course_modules(course_id, active_only=True)

    modules_with_progress = []
    for mod in modules:
        lessons = user_db.get_module_lessons(mod['id'], active_only=True)
        completed = 0
        total = len(lessons)

        for lesson in lessons:
            status = user_db.get_lesson_status(telegram_id, lesson['id'])
            if status == 'completed':
                completed += 1

        modules_with_progress.append({
            **mod,
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

    from keyboards.inline.user_keyboards import modules_list
    await bot.send_message(
        call.from_user.id,
        text,
        reply_markup=modules_list(course_id, modules_with_progress)
    )
    await call.answer()


def is_previous_module_completed(telegram_id: int, current_module_id: int) -> bool:
    """Oldingi modul tugaganmi tekshirish"""
    module = user_db.get_module(current_module_id)
    if not module:
        return False

    # Birinchi modul bo'lsa — ochiq
    if module['order_num'] == 1:
        return True

    # Oldingi modulni topish
    prev_module = user_db.execute(
        """SELECT id FROM Modules 
           WHERE course_id = ? AND order_num < ? AND is_active = TRUE
           ORDER BY order_num DESC LIMIT 1""",
        parameters=(module['course_id'], module['order_num']),
        fetchone=True
    )

    if not prev_module:
        return True  # Oldingi modul yo'q — ochiq

    prev_module_id = prev_module[0]

    # Oldingi modulning barcha darslari tugaganmi
    prev_lessons = user_db.get_module_lessons(prev_module_id, active_only=True)

    if not prev_lessons:
        return True  # Darslar yo'q — ochiq

    for lesson in prev_lessons:
        status = user_db.get_lesson_status(telegram_id, lesson['id'])
        if status != 'completed':
            return False  # Tugatilmagan dars bor

    return True  # Barcha darslar tugagan