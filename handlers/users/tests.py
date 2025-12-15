"""
User Tests Handler (SODDALASHTIRILGAN)
======================================
Test yechish → 60%+ = Dars tugaydi → Keyingi dars ochiladi
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from datetime import datetime

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    test_start,
    test_question,
    test_result,
    back_to_lessons
)
from states.user_states import TestStates


# ============================================================
#                    TEST BOSHLASH
# ============================================================

@dp.callback_query_handler(text_startswith="user:test:")
async def start_test(call: types.CallbackQuery, state: FSMContext):
    """
    Testni boshlash
    user:test:{lesson_id}
    """
    parts = call.data.split(":")

    # user:test:begin:{lesson_id} yoki user:test:{lesson_id}
    if parts[2] == "begin":
        # Testni haqiqatda boshlash
        await begin_test(call, state)
        return

    lesson_id = int(parts[-1])

    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    # Dars ma'lumotlari
    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi", show_alert=True)
        return

    # Test mavjudmi
    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        await call.answer("❌ Bu darsda test yo'q", show_alert=True)
        return

    # Savollarni olish
    questions = user_db.get_test_questions(test['id'])

    if not questions:
        await call.answer("📭 Testda savollar yo'q", show_alert=True)
        return

    # State ga saqlash
    await state.update_data(
        test_id=test['id'],
        lesson_id=lesson_id,
        lesson_name=lesson['name'],
        questions=questions,
        current_index=0,
        answers={},
        passing_score=test.get('passing_score', 60),
        start_time=datetime.now().isoformat()
    )

    text = f"""
📝 <b>Test</b>

📹 Dars: {lesson['name']}
📊 Savollar: {len(questions)} ta
🎯 O'tish bali: {test.get('passing_score', 60)}%

⬇️ Boshlash uchun tugmani bosing:
"""

    try:
        await call.message.edit_text(text, reply_markup=test_start(lesson_id))
    except:
        await call.message.delete()
        await call.message.answer(text, reply_markup=test_start(lesson_id))

    await call.answer()


async def begin_test(call: types.CallbackQuery, state: FSMContext):
    """
    Testni haqiqatda boshlash - birinchi savol
    """
    data = await state.get_data()

    if not data.get('questions'):
        await call.answer("❌ Avval testni tanlang", show_alert=True)
        return

    await TestStates.in_progress.set()

    # Birinchi savol
    await show_question(call.message, state, 0)
    await call.answer()


# ============================================================
#                    SAVOL KO'RSATISH
# ============================================================

async def show_question(message: types.Message, state: FSMContext, index: int):
    """
    Savolni ko'rsatish
    """
    import html

    data = await state.get_data()
    questions = data['questions']

    if index >= len(questions):
        # Test tugadi
        await show_test_result(message, state)
        return

    question = questions[index]
    await state.update_data(current_index=index)

    # Javob variantlari
    options = []
    options.append(('A', question.get('a', '')))
    options.append(('B', question.get('b', '')))
    if question.get('c'):
        options.append(('C', question['c']))
    if question.get('d'):
        options.append(('D', question['d']))

    # Savol matni
    question_text = html.escape(str(question.get('question', '')))

    text = f"""
📝 <b>Savol {index + 1}/{len(questions)}</b>

❓ {question_text}

"""

    for letter, option in options:
        escaped_option = html.escape(str(option))
        text += f"<b>{letter})</b> {escaped_option}\n"

    try:
        await message.edit_text(
            text,
            reply_markup=test_question(index, [opt[0] for opt in options])
        )
    except:
        await message.answer(
            text,
            reply_markup=test_question(index, [opt[0] for opt in options])
        )


# ============================================================
#                    JAVOB BERISH
# ============================================================
@dp.callback_query_handler(text_startswith="user:answer:", state=TestStates.in_progress)
async def answer_question(call: types.CallbackQuery, state: FSMContext):
    """
    Savolga javob berish
    """
    import random

    parts = call.data.split(":")
    question_index = int(parts[2])
    answer = parts[3]

    data = await state.get_data()
    questions = data['questions']
    question = questions[question_index]
    correct = question.get('correct', '').upper()

    # Javobni saqlash
    answers = data.get('answers', {})
    answers[str(question_index)] = answer
    await state.update_data(answers=answers)

    # Motivatsion fikrlar
    correct_messages = [
        "✅ Xuddi shunday davom eting ! 🎉",
        "✅ Barakalla! 💪",
        "✅ Ajoyib! Davom eting! 🔥",
        "✅ To'g'ri javob! 👏",
        "✅ Zo'r! Siz uddalayapsiz! ⭐",
    ]

    wrong_messages = [
        f"❌ Noto'g'ri!\nTo'g'ri javob: {correct}",
        f"❌ Xato ketdi!\nJavob: {correct} edi",
        f"❌ Afsuski noto'g'ri!\nTo'g'risi: {correct}",
    ]

    if answer.upper() == correct:
        msg = random.choice(correct_messages)
    else:
        msg = random.choice(wrong_messages)

    await call.answer(msg, show_alert=True)

    # Keyingi savol
    await show_question(call.message, state, question_index + 1)


# ============================================================
#                    TEST NATIJASI
# ============================================================
# ============================================================
#                    TEST NATIJASI (TUZATILGAN)
# ============================================================

async def show_test_result(message: types.Message, state: FSMContext):
    """
    Test natijasini ko'rsatish
    60%+ = Dars tugaydi
    """
    data = await state.get_data()

    questions = data.get('questions', [])
    answers = data.get('answers', {})

    # --- TUZATILGAN JOY ---
    # Xato berayotgan qator o'rniga, start_test da saqlangan balni olamiz
    passing_score = data.get('passing_score', 60)
    # ----------------------

    lesson_id = data.get('lesson_id')
    test_id = data.get('test_id')

    # Natijani hisoblash
    correct_count = 0
    total_count = len(questions)

    for i, question in enumerate(questions):
        user_answer = answers.get(str(i))
        correct_answer = question.get('correct', '').upper()

        # Agar user_answer bo'lsa va to'g'ri bo'lsa
        if user_answer and user_answer.upper() == correct_answer:
            correct_count += 1

    # Foiz
    percentage = (correct_count / total_count * 100) if total_count > 0 else 0
    passed = percentage >= passing_score

    # Bazaga saqlash
    telegram_id = message.chat.id
    user = user_db.get_user(telegram_id)
    user_id = user['id'] if user else None

    if user_id:
        # Test natijasini saqlash
        user_db.save_test_result(
            telegram_id=telegram_id,
            test_id=test_id,
            score=int(percentage),
            total_questions=total_count,
            correct_answers=correct_count,
            answers=answers
        )

        # Ball qo'shish (har doim)
        score_to_add = int(percentage / 10)  # Har 10% = 1 ball
        user_db.add_score(telegram_id, score_to_add)

        # Agar o'tgan bo'lsa - DARSNI TUGATISH
        if passed:
            # Dars allaqachon completed emasligini tekshirish
            current_status = get_lesson_status(user_id, lesson_id)

            if current_status != 'completed':
                # Darsni tugatish
                complete_lesson_db(user_id, lesson_id)

                # Qo'shimcha +10 ball dars uchun
                user_db.add_score(telegram_id, 10)

    # Keyingi dars
    next_lesson = get_next_lesson(lesson_id)

    # Oxirgi darsmi?
    is_last_lesson = next_lesson is None

    # Natija xabari
    if passed:
        text = f"""
🎉 <b>Tabriklaymiz!</b>

✅ To'g'ri javoblar: {correct_count}/{total_count}
📊 Natija: {percentage:.0f}%

✅ Dars tugallandi!
🏆 +{int(percentage / 10) + 10} ball qo'shildi!
"""
        if is_last_lesson:
            text += "\n\n🎓 Siz kursni tugatdingiz! Sertifikat olishingiz mumkin."
    else:
        text = f"""
😔 <b>Afsuski, o'ta olmadingiz</b>

✅ To'g'ri javoblar: {correct_count}/{total_count}
📊 Natija: {percentage:.0f}%
🎯 O'tish bali: {passing_score}%

🔄 Qaytadan urinib ko'ring!
"""

    await state.finish()

    try:
        await message.edit_text(
            text,
            reply_markup=test_result(
                lesson_id=lesson_id,
                passed=passed,
                next_lesson_id=next_lesson['id'] if next_lesson else None,
                is_last_lesson=is_last_lesson
            )
        )
    except:
        await message.answer(
            text,
            reply_markup=test_result(
                lesson_id=lesson_id,
                passed=passed,
                next_lesson_id=next_lesson['id'] if next_lesson else None,
                is_last_lesson=is_last_lesson
            )
        )

# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def get_lesson_status(user_id: int, lesson_id: int) -> str:
    """
    Dars statusini olish
    """
    result = user_db.execute(
        "SELECT status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
        parameters=(user_id, lesson_id),
        fetchone=True
    )

    return result[0] if result else 'unlocked'


def complete_lesson_db(user_id: int, lesson_id: int):
    """
    Darsni tugatish (bazada)
    """
    existing = user_db.execute(
        "SELECT id FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
        parameters=(user_id, lesson_id),
        fetchone=True
    )

    if existing:
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