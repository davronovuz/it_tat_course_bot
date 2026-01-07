"""
Admin Tests Handler
===================
Test va savollarni qo'shish, tahrirlash, o'chirish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import (
    test_menu,
    test_questions_list,
    question_detail,
    test_settings,
    correct_answer_select,
    confirm_action
)
from keyboards.default.admin_keyboards import (
    admin_cancel_button,
    admin_skip_button,
    admin_confirm_keyboard
)
from states.admin_states import TestStates, QuestionStates


# ============================================================
#                    TEST MENYUSI
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:view:")
async def show_test_menu(call: types.CallbackQuery):
    """Test menyusini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    test = user_db.get_test_by_lesson(lesson_id)
    has_test = test is not None

    if has_test:
        questions_count = user_db.count_test_questions(test['id'])

        text = f"""
📝 <b>Test</b>

📹 Dars: {lesson['name']}
📁 Modul: {lesson['module_name']}

📊 <b>Test ma'lumotlari:</b>
├ 📋 Savollar: {questions_count} ta
├ 🎯 O'tish bali: {test['passing_score']}%
└ ⏱ Vaqt chegarasi: {test.get('time_limit') or 'Yo`q'}

⬇️ Amal tanlang:
"""
    else:
        text = f"""
📝 <b>Test</b>

📹 Dars: {lesson['name']}
📁 Modul: {lesson['module_name']}

❌ Bu darsda test yo'q.

Test yaratish uchun tugmani bosing.
"""

    await call.message.edit_text(text, reply_markup=test_menu(lesson_id, has_test))
    await call.answer()


# ============================================================
#                    TEST YARATISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:create:")
async def create_test(call: types.CallbackQuery, state: FSMContext):
    """Yangi test yaratish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    # Testni yaratish (default sozlamalar bilan)
    test_id = user_db.add_test(lesson_id, passing_score=60)

    if test_id:
        await call.answer("✅ Test yaratildi!", show_alert=True)

        text = f"""
📝 <b>Test yaratildi!</b>

📹 Dars: {lesson['name']}

Endi savollar qo'shishingiz mumkin.

⬇️ Amal tanlang:
"""

        await call.message.edit_text(text, reply_markup=test_menu(lesson_id, True))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


# ============================================================
#                    SAVOLLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:questions:")
async def show_questions_list(call: types.CallbackQuery):
    """Savollar ro'yxatini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    test = user_db.get_test_by_lesson(lesson_id)
    if not test:
        test_id = user_db.add_test(lesson_id, passing_score=60)
        if not test_id:
            await call.answer("❌ Test yaratishda xatolik!", show_alert=True)
            return
        test = {'id': test_id}

    questions = user_db.get_test_questions(test['id'])

    if not questions:
        text = f"""
📋 <b>Test savollari</b>

📹 Dars: {lesson['name']}

📭 Hozircha savollar yo'q.

Savol qo'shish uchun tugmani bosing.
"""
    else:
        text = f"""
📋 <b>Test savollari</b>

📹 Dars: {lesson['name']}
📊 Jami: {len(questions)} ta savol

⬇️ Savolni tanlang:
"""

    await call.message.edit_text(text, reply_markup=test_questions_list(lesson_id, questions))
    await call.answer()


# ============================================================
#                    SAVOL QO'SHISH (QO'LDA)
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:add_q:")
async def add_question_start(call: types.CallbackQuery, state: FSMContext):
    """Yangi savol qo'shishni boshlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    test = user_db.get_test_by_lesson(lesson_id)
    if not test:
        test_id = user_db.add_test(lesson_id, passing_score=60)
        if not test_id:
            await call.answer("❌ Test yaratishda xatolik!", show_alert=True)
            return
        test = {'id': test_id}

    await state.update_data(
        lesson_id=lesson_id,
        test_id=test['id'],
        lesson_name=lesson['name']
    )

    await call.message.edit_text(
        f"📝 <b>Yangi savol qo'shish</b>\n\n"
        f"📹 Dars: {lesson['name']}\n\n"
        f"❓ Savol matnini kiriting:\n\n"
        f"<i>Masalan: Windows operatsion tizimi qachon yaratilgan?</i>"
    )

    await call.message.answer("⌨️ Savol matnini yozing:", reply_markup=admin_cancel_button())

    await QuestionStates.add_question.set()
    await call.answer()


@dp.message_handler(state=QuestionStates.add_question)
async def add_question_text(message: types.Message, state: FSMContext):
    """Savol matnini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    question_text = message.text.strip()

    if len(question_text) < 5:
        await message.answer("❌ Savol matni kamida 5 ta belgidan iborat bo'lishi kerak!")
        return

    if len(question_text) > 500:
        await message.answer("❌ Savol matni 500 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(question=question_text)

    await message.answer(
        f"✅ Savol: <b>{question_text}</b>\n\n"
        f"🅰️ A variantini kiriting:",
        reply_markup=admin_cancel_button()
    )

    await QuestionStates.add_option_a.set()


@dp.message_handler(state=QuestionStates.add_option_a)
async def add_option_a(message: types.Message, state: FSMContext):
    """A variantini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    option_a = message.text.strip()

    if len(option_a) > 200:
        await message.answer("❌ Variant 200 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(option_a=option_a)

    await message.answer(
        f"✅ A: {option_a}\n\n"
        f"🅱️ B variantini kiriting:",
        reply_markup=admin_cancel_button()
    )

    await QuestionStates.add_option_b.set()


@dp.message_handler(state=QuestionStates.add_option_b)
async def add_option_b(message: types.Message, state: FSMContext):
    """B variantini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    option_b = message.text.strip()

    if len(option_b) > 200:
        await message.answer("❌ Variant 200 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(option_b=option_b)

    await message.answer(
        f"✅ B: {option_b}\n\n"
        f"🅲 C variantini kiriting:\n\n"
        f"<i>O'tkazib yuborish uchun tugmani bosing</i>",
        reply_markup=admin_skip_button()
    )

    await QuestionStates.add_option_c.set()


@dp.message_handler(state=QuestionStates.add_option_c)
async def add_option_c(message: types.Message, state: FSMContext):
    """C variantini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        await state.update_data(option_c=None, option_d=None)

        # To'g'ri javobni tanlash
        data = await state.get_data()

        text = f"""
❓ <b>To'g'ri javobni tanlang</b>

Savol: {data['question']}

🅰️ A: {data['option_a']}
🅱️ B: {data['option_b']}
"""

        await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        await message.answer(
            "To'g'ri javobni tanlang:",
            reply_markup=correct_answer_select(data['lesson_id'])
        )

        await QuestionStates.add_correct.set()
        return

    option_c = message.text.strip()

    if len(option_c) > 200:
        await message.answer("❌ Variant 200 ta belgidan oshmasligi kerak!")
        return

    await state.update_data(option_c=option_c)

    await message.answer(
        f"✅ C: {option_c}\n\n"
        f"🅳 D variantini kiriting:\n\n"
        f"<i>O'tkazib yuborish uchun tugmani bosing</i>",
        reply_markup=admin_skip_button()
    )

    await QuestionStates.add_option_d.set()


@dp.message_handler(state=QuestionStates.add_option_d)
async def add_option_d(message: types.Message, state: FSMContext):
    """D variantini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "⏩ O'tkazib yuborish":
        await state.update_data(option_d=None)
    else:
        option_d = message.text.strip()

        if len(option_d) > 200:
            await message.answer("❌ Variant 200 ta belgidan oshmasligi kerak!")
            return

        await state.update_data(option_d=option_d)

    # To'g'ri javobni tanlash
    data = await state.get_data()

    text = f"""
❓ <b>To'g'ri javobni tanlang</b>

Savol: {data['question']}

🅰️ A: {data['option_a']}
🅱️ B: {data['option_b']}
"""

    if data.get('option_c'):
        text += f"🅲 C: {data['option_c']}\n"
    if data.get('option_d'):
        text += f"🅳 D: {data['option_d']}\n"

    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
    await message.answer(
        "To'g'ri javobni tanlang:",
        reply_markup=correct_answer_select(data['lesson_id'])
    )

    await QuestionStates.add_correct.set()


@dp.callback_query_handler(text_startswith="admin:answer:", state=QuestionStates.add_correct)
async def add_correct_answer(call: types.CallbackQuery, state: FSMContext):
    """To'g'ri javobni tanlash"""
    parts = call.data.split(":")
    correct_answer = parts[2]  # A, B, C, yoki D

    data = await state.get_data()

    # Variant mavjudligini tekshirish
    if correct_answer == 'C' and not data.get('option_c'):
        await call.answer("❌ C varianti mavjud emas!", show_alert=True)
        return
    if correct_answer == 'D' and not data.get('option_d'):
        await call.answer("❌ D varianti mavjud emas!", show_alert=True)
        return

    # Savolni qo'shish
    question_id = user_db.add_question(
        test_id=data['test_id'],
        question_text=data['question'],
        option_a=data['option_a'],
        option_b=data['option_b'],
        option_c=data.get('option_c'),
        option_d=data.get('option_d'),
        correct_answer=correct_answer
    )

    if question_id:
        await call.answer("✅ Savol qo'shildi!", show_alert=True)

        # Yana savol qo'shish taklifi
        questions = user_db.get_test_questions(data['test_id'])

        text = f"""
✅ <b>Savol qo'shildi!</b>

📹 Dars: {data['lesson_name']}
📊 Jami savollar: {len(questions)} ta

Yana savol qo'shmoqchimisiz?
"""

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Yana qo'shish", callback_data=f"admin:test:add_q:{data['lesson_id']}"),
            InlineKeyboardButton("📋 Savollar", callback_data=f"admin:test:questions:{data['lesson_id']}")
        )
        keyboard.add(
            InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:test:view:{data['lesson_id']}")
        )

        await call.message.edit_text(text, reply_markup=keyboard)
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)

    await state.finish()


# ============================================================
#                    SAVOL KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:question:view:")
async def view_question(call: types.CallbackQuery):
    """Savol tafsilotlarini ko'rish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    question_id = int(call.data.split(":")[-1])

    # Savolni olish (to'liq)
    result = user_db.execute(
        """SELECT q.id, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
                  q.correct_answer, q.order_num, t.lesson_id
           FROM Questions q
           JOIN Tests t ON q.test_id = t.id
           WHERE q.id = ?""",
        parameters=(question_id,),
        fetchone=True
    )

    if not result:
        await call.answer("❌ Savol topilmadi!", show_alert=True)
        return

    question = {
        'id': result[0],
        'question': result[1],
        'a': result[2],
        'b': result[3],
        'c': result[4],
        'd': result[5],
        'correct': result[6],
        'order_num': result[7],
        'lesson_id': result[8]
    }

    # Javoblar
    answers = f"🅰️ A: {question['a']}\n🅱️ B: {question['b']}"
    if question['c']:
        answers += f"\n🅲 C: {question['c']}"
    if question['d']:
        answers += f"\n🅳 D: {question['d']}"

    # To'g'ri javob belgisi
    correct_icons = {'A': '🅰️', 'B': '🅱️', 'C': '🅲', 'D': '🅳'}
    correct_icon = correct_icons.get(question['correct'], '❓')

    text = f"""
❓ <b>Savol #{question['order_num']}</b>

{question['question']}

<b>Javoblar:</b>
{answers}

✅ <b>To'g'ri javob:</b> {correct_icon} {question['correct']}

⬇️ Amal tanlang:
"""

    await call.message.edit_text(
        text,
        reply_markup=question_detail(question_id, question['lesson_id'])
    )
    await call.answer()


# ============================================================
#                    SAVOLNI O'CHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:question:delete:")
async def delete_question(call: types.CallbackQuery):
    """Savolni o'chirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    question_id = int(call.data.split(":")[-1])

    # Lesson ID ni olish
    result = user_db.execute(
        """SELECT t.lesson_id FROM Questions q
           JOIN Tests t ON q.test_id = t.id
           WHERE q.id = ?""",
        parameters=(question_id,),
        fetchone=True
    )

    if not result:
        await call.answer("❌ Savol topilmadi!", show_alert=True)
        return

    lesson_id = result[0]

    if user_db.delete_question(question_id):
        await call.answer("✅ Savol o'chirildi!", show_alert=True)

        # Savollar ro'yxatiga qaytish
        test = user_db.get_test_by_lesson(lesson_id)
        questions = user_db.get_test_questions(test['id']) if test else []
        lesson = user_db.get_lesson(lesson_id)

        text = f"""
📋 <b>Test savollari</b>

📹 Dars: {lesson['name']}
📊 Jami: {len(questions)} ta savol

⬇️ Savolni tanlang:
"""

        await call.message.edit_text(text, reply_markup=test_questions_list(lesson_id, questions))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


# ============================================================
#                    BARCHA SAVOLLARNI O'CHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:clear:")
async def clear_all_questions_confirm(call: types.CallbackQuery):
    """Barcha savollarni o'chirishni tasdiqlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])

    text = f"""
🗑 <b>Barcha savollarni o'chirish</b>

⚠️ Diqqat! Barcha savollar o'chib ketadi!

❓ Rostdan ham o'chirmoqchimisiz?
"""

    await call.message.edit_text(
        text,
        reply_markup=confirm_action("test_clear", lesson_id)
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:confirm:test_clear:")
async def clear_all_questions_execute(call: types.CallbackQuery):
    """Barcha savollarni o'chirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        await call.answer("❌ Test topilmadi!", show_alert=True)
        return

    if user_db.delete_all_test_questions(test['id']):
        await call.answer("✅ Barcha savollar o'chirildi!", show_alert=True)

        lesson = user_db.get_lesson(lesson_id)

        text = f"""
📋 <b>Test savollari</b>

📹 Dars: {lesson['name']}

📭 Hozircha savollar yo'q.
"""

        await call.message.edit_text(text, reply_markup=test_questions_list(lesson_id, []))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


# ============================================================
#                    TEST SOZLAMALARI
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:settings:")
async def show_test_settings(call: types.CallbackQuery):
    """Test sozlamalarini ko'rsatish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        await call.answer("❌ Test topilmadi!", show_alert=True)
        return

    text = f"""
⚙️ <b>Test sozlamalari</b>

📊 O'tish bali: {test['passing_score']}%
⏱ Vaqt chegarasi: {test.get('time_limit') or 'Yo`q'}

⬇️ O'zgartirish uchun tanlang:
"""

    await call.message.edit_text(text, reply_markup=test_settings(lesson_id, test['id']))
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:test:set:pass:")
async def set_passing_score(call: types.CallbackQuery, state: FSMContext):
    """O'tish balini o'zgartirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    test_id = int(call.data.split(":")[-1])

    # Lesson ID ni olish
    result = user_db.execute(
        "SELECT lesson_id FROM Tests WHERE id = ?",
        parameters=(test_id,),
        fetchone=True
    )

    if not result:
        await call.answer("❌ Test topilmadi!", show_alert=True)
        return

    await state.update_data(test_id=test_id, lesson_id=result[0])

    await call.message.edit_text(
        "📊 <b>O'tish balini o'zgartirish</b>\n\n"
        "Yangi o'tish balini kiriting (1-100):\n\n"
        "<i>Masalan: 60</i>"
    )

    await call.message.answer("⌨️ O'tish bali (%):", reply_markup=admin_cancel_button())
    await TestStates.edit_passing_score.set()
    await call.answer()


@dp.message_handler(state=TestStates.edit_passing_score)
async def edit_passing_score(message: types.Message, state: FSMContext):
    """O'tish balini yangilash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    try:
        new_score = int(message.text.strip())
        if new_score < 1 or new_score > 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri format! 1-100 orasida son kiriting")
        return

    data = await state.get_data()

    # Test jadvalida passing_score ni yangilash
    user_db.execute(
        "UPDATE Tests SET passing_score = ? WHERE id = ?",
        parameters=(new_score, data['test_id']),
        commit=True
    )

    await message.answer(
        f"✅ O'tish bali yangilandi!\n\n"
        f"📊 Yangi o'tish bali: <b>{new_score}%</b>",
        reply_markup=types.ReplyKeyboardRemove()
    )

    # Test menyusiga qaytish
    await message.answer(
        "📝 Test sozlamalari:",
        reply_markup=test_settings(data['lesson_id'], data['test_id'])
    )

    await state.finish()


# ============================================================
#                    TESTNI O'CHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:delete:")
async def delete_test_confirm(call: types.CallbackQuery):
    """Testni o'chirishni tasdiqlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        await call.answer("❌ Test topilmadi!", show_alert=True)
        return

    questions_count = user_db.count_test_questions(test['id'])

    text = f"""
🗑 <b>Testni o'chirish</b>

⚠️ Diqqat! Test o'chirilsa:
• {questions_count} ta savol
• Barcha test natijalari

ham o'chib ketadi!

❓ Rostdan ham o'chirmoqchimisiz?
"""

    await call.message.edit_text(
        text,
        reply_markup=confirm_action("test_delete", lesson_id)
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:confirm:test_delete:")
async def delete_test_execute(call: types.CallbackQuery):
    """Testni o'chirish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        await call.answer("❌ Test topilmadi!", show_alert=True)
        return

    if user_db.delete_test(test['id']):
        await call.answer("✅ Test o'chirildi!", show_alert=True)

        lesson = user_db.get_lesson(lesson_id)

        text = f"""
📝 <b>Test</b>

📹 Dars: {lesson['name']}

❌ Bu darsda test yo'q.
"""

        await call.message.edit_text(text, reply_markup=test_menu(lesson_id, False))
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)


@dp.callback_query_handler(text_startswith="admin:cancel:test_delete:")
async def cancel_delete_test(call: types.CallbackQuery):
    """Test o'chirishni bekor qilish"""
    lesson_id = int(call.data.split(":")[-1])
    lesson = user_db.get_lesson(lesson_id)
    test = user_db.get_test_by_lesson(lesson_id)

    if lesson and test:
        questions_count = user_db.count_test_questions(test['id'])

        text = f"""
📝 <b>Test</b>

📹 Dars: {lesson['name']}

📊 <b>Test ma'lumotlari:</b>
├ 📋 Savollar: {questions_count} ta
└ 🎯 O'tish bali: {test['passing_score']}%
"""

        await call.message.edit_text(text, reply_markup=test_menu(lesson_id, True))

    await call.answer("❌ Bekor qilindi")

# ============================================================
#                    EXCEL YUKLASH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:test:upload:")
async def upload_excel_start(call: types.CallbackQuery, state: FSMContext):
    """Excel faylni yuklashni boshlash"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    lesson_id = int(call.data.split(":")[-1])
    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        # Test yo'q - avtomatik yaratamiz
        test_id = user_db.add_test(lesson_id, passing_score=60)
        if not test_id:
            await call.answer("❌ Test yaratishda xatolik!", show_alert=True)
            return
    else:
        test_id = test['id']

    await state.update_data(lesson_id=lesson_id, test_id=test_id)

    text = """
📤 <b>Excel orqali savollar yuklash</b>

Excel fayl formati:
┌────────────────────────────────────────┐
│ Savol │ A │ B │ C │ D │ Togri │
├────────────────────────────────────────┤
│ ... │ ... │ ... │ ... │ ... │ A │
└────────────────────────────────────────┘

<b>Qoidalar:</b>
- Birinchi qator - sarlavhalar (o'tkazib yuboriladi)
- "Savol" - savol matni
- "A", "B", "C", "D" - javob variantlari
- "Togri" - to'g'ri javob (A, B, C yoki D)
- C va D variantlari bo'sh bo'lishi mumkin

📎 Excel faylni yuboring:
"""

    await call.message.edit_text(text)
    await call.message.answer("📎 Excel fayl yuboring:", reply_markup=admin_cancel_button())

    await QuestionStates.upload_excel.set()
    await call.answer()


@dp.message_handler(state=QuestionStates.upload_excel, content_types=['document'])
async def upload_excel_file(message: types.Message, state: FSMContext):
    """Excel faylni qabul qilish va savollarni qo'shish"""
    document = message.document

    if not document.file_name.endswith(('.xlsx', '.xls')):
        await message.answer("❌ Faqat Excel fayl (.xlsx, .xls) yuboring!")
        return

    await message.answer("⏳ Fayl yuklanmoqda...")

    data = await state.get_data()
    test_id = data.get('test_id')
    lesson_id = data.get('lesson_id')

    if not test_id or not lesson_id:
        await message.answer("❌ Xatolik: Test ma'lumotlari topilmadi!", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return

    try:
        import io
        import openpyxl

        # Faylni yuklab olish
        file = await bot.get_file(document.file_id)
        file_bytes = await bot.download_file(file.file_path)

        # Excel faylni o'qish
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes.read()))
        ws = wb.active

        # Savollarni qo'shish
        questions_added = 0
        errors = []

        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row[0]:  # Bo'sh qator
                continue

            try:
                question_text = str(row[0]).strip()
                option_a = str(row[1]).strip() if row[1] else None
                option_b = str(row[2]).strip() if row[2] else None
                option_c = str(row[3]).strip() if len(row) > 3 and row[3] else None
                option_d = str(row[4]).strip() if len(row) > 4 and row[4] else None
                correct = str(row[5]).strip().upper() if len(row) > 5 and row[5] else None

                if not all([question_text, option_a, option_b, correct]):
                    errors.append(f"Qator {row_num}: Ma'lumotlar to'liq emas")
                    continue

                if correct not in ['A', 'B', 'C', 'D']:
                    errors.append(f"Qator {row_num}: Noto'g'ri javob formati")
                    continue

                question_id = user_db.add_question(
                    test_id=test_id,
                    question_text=question_text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_answer=correct
                )

                if question_id:
                    questions_added += 1
                else:
                    errors.append(f"Qator {row_num}: Saqlashda xato")

            except Exception as e:
                errors.append(f"Qator {row_num}: {str(e)}")

        # Natija xabari
        result_text = f"✅ <b>Yuklash yakunlandi!</b>\n\n"
        result_text += f"📊 Qo'shilgan savollar: <b>{questions_added}</b> ta\n"

        if errors:
            result_text += f"\n⚠️ <b>Xatolar ({len(errors)}):</b>\n"
            for error in errors[:5]:
                result_text += f"• {error}\n"
            if len(errors) > 5:
                result_text += f"• ... va yana {len(errors) - 5} ta xato"

        await message.answer(result_text, reply_markup=types.ReplyKeyboardRemove())

        # Test menyusiga qaytish - XAVFSIZ usul
        questions = user_db.get_test_questions(test_id)

        await message.answer(
            f"📋 Jami savollar: {len(questions)} ta",
            reply_markup=test_questions_list(lesson_id, questions)
        )

    except ImportError:
        await message.answer(
            "❌ Excel fayllarni o'qish uchun openpyxl kutubxonasi kerak!\n\n"
            "Serverda `pip install openpyxl` buyrug'ini ishga tushiring.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except Exception as e:
        await message.answer(
            f"❌ Faylni o'qishda xato:\n{str(e)}",
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.finish()


@dp.message_handler(state=QuestionStates.upload_excel)
async def upload_excel_text(message: types.Message, state: FSMContext):
    """Excel o'rniga matn kelsa"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=types.ReplyKeyboardRemove())
        return

    await message.answer("❌ Iltimos, Excel fayl (.xlsx) yuboring!")