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

def check_has_paid_course(user_id: int) -> bool:
    """
    User kursni sotib olganmi?
    """
    result = user_db.execute(
        "SELECT 1 FROM Payments WHERE user_id = ? AND status = 'approved' LIMIT 1",
        parameters=(user_id,),
        fetchone=True
    )
    if result:
        return True

    result = user_db.execute(
        """SELECT 1 FROM ManualAccess WHERE user_id = ? 
           AND (expires_at IS NULL OR expires_at > datetime('now')) LIMIT 1""",
        parameters=(user_id,),
        fetchone=True
    )
    return bool(result)


# ============================================================
#                    MENING DARSLARIM TUGMASI
# ============================================================

@dp.message_handler(text="📚 Mening Darslarim")
async def my_lessons_handler(message: types.Message):
    """
    Mening darslarim tugmasi bosilganda
    """
    telegram_id = message.from_user.id
    user = user_db.get_user(telegram_id)

    # Ro'yxatdan o'tmaganmi?
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting!\n\n/start buyrug'ini yuboring.")
        return

    user_id = user['id']

    # Kursni sotib olganmi?
    if check_has_paid_course(user_id):
        # Sotib olgan - barcha darslar
        await show_paid_lessons(message, user_id)
    else:
        # Sotib olmagan - faqat bepul darslar
        await show_free_lessons(message)

async def show_paid_lessons(message: types.Message, user_id: int):
    """
    Sotib olgan user uchun - qisqa ko'rinish (3 ta dars)
    """
    lessons = get_all_lessons_with_status(user_id)

    if not lessons:
        await message.answer("📭 Darslar topilmadi")
        return

    completed = sum(1 for l in lessons if l['status'] == 'completed')
    total = len(lessons)
    percent = int(completed / total * 100) if total > 0 else 0
    filled = int(percent / 10)
    bar = "▓" * filled + "░" * (10 - filled)

    # Hozirgi ochiq darsni topish
    current_index = 0
    for i, l in enumerate(lessons):
        if l['status'] == 'unlocked':
            current_index = i
            break
        elif l['status'] == 'completed':
            current_index = i

    # Ko'rsatiladigan darslar: oldingi 1 + hozirgi + keyingi 1
    start = max(0, current_index - 1)
    end = min(len(lessons), current_index + 2)
    visible_lessons = lessons[start:end]

    text = f"""
📚 <b>Mening darslarim</b>

📊 Progress: {completed}/{total} ({percent}%)
[{bar}]

📍 Siz hozir <b>{current_index + 1}</b>-darsdasiz
"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for lesson in visible_lessons:
        status = lesson['status']
        order = lesson['order_num']
        name = lesson['name']

        if status == 'completed':
            icon = "✅"
            callback = f"user:lesson:{lesson['id']}"
        elif status == 'unlocked':
            icon = "🔓"
            callback = f"user:lesson:{lesson['id']}"
        else:
            icon = "🔒"
            callback = f"user:locked:{lesson['id']}"

        # Hozirgi darsni ajratib ko'rsatish
        if status == 'unlocked':
            btn_text = f"▶️ {order}. {name}"
        else:
            btn_text = f"{icon} {order}. {name}"

        keyboard.add(types.InlineKeyboardButton(btn_text, callback_data=callback))

    # Barcha darslar tugmasi
    keyboard.add(types.InlineKeyboardButton(
        f"📋 Barcha darslar ({total} ta)",
        callback_data="user:all_lessons"
    ))

    await message.answer(text, reply_markup=keyboard)


# ============================================================
#                    BARCHA DARSLAR RO'YXATI
# ============================================================
@dp.callback_query_handler(text="user:all_lessons")
async def show_all_lessons(call: types.CallbackQuery):
    """
    To'liq darslar ro'yxati
    """
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    user_id = user['id']

    if not check_has_paid_course(user_id):
        await call.answer("🔒 Kursni sotib oling!", show_alert=True)
        return

    lessons = get_all_lessons_with_status(user_id)

    if not lessons:
        await call.answer("📭 Darslar topilmadi", show_alert=True)
        return

    completed = sum(1 for l in lessons if l['status'] == 'completed')
    total = len(lessons)

    text = f"""
📋 <b>Barcha darslar</b>

✅ Tugallangan: {completed}/{total}
"""

    keyboard = simple_lessons_list(lessons)
    keyboard.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="user:paid_back"))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()



async def show_free_lessons(message: types.Message):
    """
    Sotib olmagan user uchun - faqat bepul darslar
    """
    free_lessons = user_db.execute(
        """SELECT l.id, l.name
           FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           WHERE l.is_free = 1 AND l.is_active = 1 AND m.is_active = 1
           ORDER BY m.order_num, l.order_num""",
        fetchall=True
    )

    if not free_lessons:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("💰 Kursni sotib olish", callback_data="user:buy"))
        await message.answer("📭 Bepul darslar yo'q.\n\n💰 Kursni sotib oling!", reply_markup=keyboard)
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for i, (lid, name) in enumerate(free_lessons, 1):
        keyboard.add(types.InlineKeyboardButton(
            f"🆓 {i}. {name}",
            callback_data=f"user:free:{lid}"
        ))
    keyboard.add(types.InlineKeyboardButton("💰 To'liq kursni sotib olish", callback_data="user:buy"))

    text = f"""
🆓 <b>Bepul darslar</b>

Sizda {len(free_lessons)} ta bepul dars mavjud.

🔒 To'liq kursni ochish uchun sotib oling!
"""
    await message.answer(text, reply_markup=keyboard)


# ============================================================
#                    BEPUL DARS KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:free:")
async def view_free_lesson(call: types.CallbackQuery):
    """
    Bepul darsni ko'rish - TEST YO'Q
    """
    lesson_id = int(call.data.split(":")[-1])
    telegram_id = call.from_user.id

    lesson = user_db.get_lesson(lesson_id)

    # Himoya: faqat bepul darsga ruxsat
    if not lesson or not lesson.get('is_free'):
        await call.answer("🔒 Bu pullik dars! Kursni sotib oling.", show_alert=True)
        return

    try:
        await call.message.delete()
    except:
        pass

    await call.answer("📹 Video yuborilmoqda...")

    # Video yuborish
    video_file_id = lesson.get('video_file_id')
    caption = f"🆓 <b>{lesson['name']}</b>\n\n{lesson.get('description') or ''}"

    if video_file_id:
        try:
            await bot.send_video(telegram_id, video_file_id, caption=caption, protect_content=True)
        except:
            await bot.send_message(telegram_id, caption + "\n\n⚠️ Video yuklanmadi")
    else:
        await bot.send_message(telegram_id, caption)

    # Keyingi bepul dars
    next_free = user_db.execute(
        """SELECT l.id, l.name FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           WHERE l.is_free = 1 AND l.is_active = 1 AND l.id != ?
               AND (m.order_num > (SELECT order_num FROM Modules WHERE id = ?)
                    OR (m.id = ? AND l.order_num > ?))
           ORDER BY m.order_num, l.order_num LIMIT 1""",
        parameters=(lesson_id, lesson['module_id'], lesson['module_id'], lesson['order_num']),
        fetchone=True
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    if next_free:
        keyboard.add(types.InlineKeyboardButton(
            f"⏭ Keyingi: {next_free[1][:20]}...",
            callback_data=f"user:free:{next_free[0]}"
        ))
    else:
        keyboard.add(types.InlineKeyboardButton(
            "🎉 Bepul darslar tugadi!",
            callback_data="user:free_end"
        ))

    keyboard.add(types.InlineKeyboardButton("💰 To'liq kursni sotib olish", callback_data="user:buy"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="user:free_back"))

    await bot.send_message(telegram_id, "👇 Davom eting:", reply_markup=keyboard)


@dp.callback_query_handler(text="user:free_end")
async def free_lessons_end(call: types.CallbackQuery):
    """
    Bepul darslar tugadi
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("💰 To'liq kursni sotib olish", callback_data="user:buy"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="user:free_back"))

    await call.message.edit_text(
        "🎉 <b>Tabriklaymiz!</b>\n\n"
        "Barcha bepul darslarni ko'rib chiqdingiz.\n\n"
        "To'liq kursda yana ko'plab darslar va testlar mavjud!",
        reply_markup=keyboard
    )
    await call.answer()


@dp.callback_query_handler(text="user:free_back")
async def free_lessons_back(call: types.CallbackQuery):
    """
    Bepul darslar ro'yxatiga qaytish
    """
    try:
        await call.message.delete()
    except:
        pass

    await show_free_lessons(call.message)
    await call.answer()



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
#                    DARS KO'RISH (HIMOYALANGAN)
# ============================================================
@dp.callback_query_handler(text_startswith="user:lesson:")
async def view_lesson(call: types.CallbackQuery):
    """
    Darsni ko'rish - FAQAT SOTIB OLGANLARGA
    """
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    user_id = user['id']

    # ⛔ HIMOYA: Kursni sotib olganmi?
    if not check_has_paid_course(user_id):
        await call.answer("🔒 Bu pullik dars! Kursni sotib oling.", show_alert=True)
        return

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
            f"📎 Materiallar ({materials_count})",
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
                f"⏭ Keyingi: {next_lesson['name'][:20]}...",
                callback_data=f"user:lesson:{next_lesson['id']}"
            ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Darslar ro'yxati",
        callback_data="user:paid_back"
    ))

    await bot.send_message(telegram_id, "👇 Davom eting:", reply_markup=keyboard)


# ============================================================
#                    ORQAGA TUGMASI (PULLIK)
# ============================================================
@dp.callback_query_handler(text="user:paid_back")
async def paid_lessons_back(call: types.CallbackQuery):
    """
    Pullik darslar ro'yxatiga qaytish
    """
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    try:
        await call.message.delete()
    except:
        pass

    await show_paid_lessons(call.message, user['id'])
    await call.answer()

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