"""
User Tests Handler
==================
Test yechish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
import json
from datetime import datetime

from loader import dp, user_db
from keyboards.inline.user_keyboards import (
    test_start,
    test_question,
    test_result,
    back_button
)
from keyboards.default.user_keyboards import main_menu
from states.user_states import TestStates


# ============================================================
#                    TEST BOSHLASH
# ============================================================

@dp.callback_query_handler(text_startswith="user:test:start:")
async def start_test(call: types.CallbackQuery, state: FSMContext):
    """Testni boshlash"""
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        await call.answer("❌ Bu darsda test yo'q!", show_alert=True)
        return

    module = user_db.get_module(lesson['module_id'])

    # Dostup tekshirish
    has_access = user_db.has_course_access(user_id, module['course_id']) if user_id else False

    if not lesson['is_free'] and not has_access:
        await call.answer("🔒 Testni yechish uchun kursni sotib oling!", show_alert=True)
        return

    # Savollarni olish
    questions = user_db.get_test_questions(test['id'])

    if not questions:
        await call.answer("📭 Bu testda savollar yo'q!", show_alert=True)
        return

    # Test ma'lumotlarini saqlash
    await state.update_data(
        test_id=test['id'],
        lesson_id=lesson_id,
        lesson_name=lesson['name'],
        questions=questions,
        current_index=0,
        answers={},
        passing_score=test['passing_score'],
        start_time=datetime.now().isoformat()
    )

    text = f"""
📝 <b>Test</b>

📹 Dars: {lesson['name']}
📊 Savollar: {len(questions)} ta
🎯 O'tish bali: {test['passing_score']}%

⚠️ <b>Qoidalar:</b>
• Har bir savolga bitta javob
• Qaytib o'zgartirish mumkin emas
• Testni yakunlaganingizdan so'ng natija ko'rsatiladi

⬇️ Boshlash uchun tugmani bosing:
"""

    await call.message.edit_text(text, reply_markup=test_start(lesson_id))
    await call.answer()


@dp.callback_query_handler(text_startswith="user:test:begin:")
async def begin_test(call: types.CallbackQuery, state: FSMContext):
    """Testni haqiqatda boshlash"""
    data = await state.get_data()

    if not data.get('questions'):
        await call.answer("❌ Xatolik! Testni qaytadan boshlang.", show_alert=True)
        return

    await TestStates.in_progress.set()

    # Birinchi savolni ko'rsatish
    await show_question(call.message, state, 0)
    await call.answer()


# ============================================================
#                    SAVOL KO'RSATISH
# ============================================================

async def show_question(message: types.Message, state: FSMContext, index: int):
    """Savolni ko'rsatish"""
    data = await state.get_data()
    questions = data['questions']

    if index >= len(questions):
        # Test tugadi - natijani ko'rsatish
        await show_test_result(message, state)
        return

    question = questions[index]
    await state.update_data(current_index=index)

    # Javob variantlari
    options = []
    options.append(('A', question['option_a']))
    options.append(('B', question['option_b']))
    if question.get('option_c'):
        options.append(('C', question['option_c']))
    if question.get('option_d'):
        options.append(('D', question['option_d']))

    # Savol matni
    text = f"""
📝 <b>Savol {index + 1}/{len(questions)}</b>

❓ {question['question_text']}

"""

    for letter, option in options:
        text += f"🔘 <b>{letter})</b> {option}\n"

    text += f"\n⬇️ Javobni tanlang:"

    await message.edit_text(
        text,
        reply_markup=test_question(
            data['test_id'],
            index,
            [opt[0] for opt in options]  # Faqat harflar
        )
    )


# ============================================================
#                    JAVOB BERISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:test:answer:", state=TestStates.in_progress)
async def answer_question(call: types.CallbackQuery, state: FSMContext):
    """Savolga javob berish"""
    parts = call.data.split(":")
    question_index = int(parts[3])
    answer = parts[4]  # A, B, C, yoki D

    data = await state.get_data()

    # Javobni saqlash
    answers = data.get('answers', {})
    answers[str(question_index)] = answer
    await state.update_data(answers=answers)

    # Keyingi savolga o'tish
    next_index = question_index + 1

    await show_question(call.message, state, next_index)
    await call.answer()


# ============================================================
#                    TEST NATIJASI
# ============================================================

async def show_test_result(message: types.Message, state: FSMContext):
    """Test natijasini ko'rsatish"""
    data = await state.get_data()

    questions = data['questions']
    answers = data.get('answers', {})
    passing_score = data['passing_score']

    # Natijalarni hisoblash
    correct_count = 0
    total_count = len(questions)

    results_detail = []

    for i, question in enumerate(questions):
        user_answer = answers.get(str(i))
        correct_answer = question['correct_answer']

        is_correct = user_answer == correct_answer

        if is_correct:
            correct_count += 1
            results_detail.append(f"✅ Savol {i + 1}: To'g'ri")
        else:
            results_detail.append(f"❌ Savol {i + 1}: Noto'g'ri (To'g'ri: {correct_answer})")

    # Foiz
    percentage = (correct_count / total_count * 100) if total_count > 0 else 0
    passed = percentage >= passing_score

    # Natijani bazaga saqlash
    telegram_id = message.chat.id
    user_id = user_db.get_user_id(telegram_id)

    user_db.save_test_result(
        user_id=user_id,
        test_id=data['test_id'],
        score=percentage,
        correct_answers=correct_count,
        total_questions=total_count,
        passed=passed,
        answers_json=json.dumps(answers)
    )

    # Ball qo'shish (agar o'tgan bo'lsa)
    if passed:
        user_db.add_score(telegram_id, int(percentage / 10))  # Har 10% uchun 1 ball

    # Natija xabari
    if passed:
        status_emoji = "🎉"
        status_text = "Tabriklaymiz! Siz testdan o'tdingiz!"
    else:
        status_emoji = "😔"
        status_text = "Afsuski, siz testdan o'ta olmadingiz. Qaytadan urinib ko'ring!"

    text = f"""
{status_emoji} <b>Test natijasi</b>

📹 Dars: {data['lesson_name']}

📊 <b>Natijalar:</b>
├ ✅ To'g'ri javoblar: {correct_count}/{total_count}
├ 📈 Foiz: {percentage:.1f}%
├ 🎯 O'tish bali: {passing_score}%
└ {"✅ O'tdingiz' if passed else '❌ O'tmadingiz"}

{status_text}
"""

    if passed:
        text += f"\n🏆 +{int(percentage / 10)} ball qo'shildi!"

    await state.finish()

    await message.edit_text(
        text,
        reply_markup=test_result(
            data['lesson_id'],
            passed,
            can_retry=not passed
        )
    )


# ============================================================
#                    QAYTA TOPSHIRISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:test:retry:")
async def retry_test(call: types.CallbackQuery, state: FSMContext):
    """Testni qayta topshirish"""
    lesson_id = int(call.data.split(":")[-1])

    # start_test funksiyasini chaqirish
    call.data = f"user:test:start:{lesson_id}"
    await start_test(call, state)


# ============================================================
#                    TEST TARIXI
# ============================================================

@dp.callback_query_handler(text_startswith="user:test:history:")
async def show_test_history(call: types.CallbackQuery):
    """Test tarixini ko'rsatish"""
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    test = user_db.get_test_by_lesson(lesson_id)

    if not test:
        await call.answer("❌ Test topilmadi!", show_alert=True)
        return

    # Barcha urinishlar
    results = user_db.execute(
        """SELECT score, correct_answers, passed, created_at 
           FROM TestResults 
           WHERE user_id = ? AND test_id = ?
           ORDER BY created_at DESC
           LIMIT 10""",
        parameters=(user_id, test['id']),
        fetchall=True
    )

    if not results:
        await call.answer("📭 Siz hali test topshirmagansiz", show_alert=True)
        return

    lesson = user_db.get_lesson(lesson_id)

    text = f"""
📊 <b>Test tarixi</b>

📹 Dars: {lesson['name']}

<b>So'nggi urinishlar:</b>
"""

    for i, result in enumerate(results, 1):
        status = "✅" if result[2] else "❌"
        date = result[3][:10] if result[3] else "Noma'lum"
        text += f"\n{i}. {status} {result[0]:.1f}% ({result[1]} to'g'ri) - {date}"

    await call.message.edit_text(
        text,
        reply_markup=back_button(f"user:lesson:view:{lesson_id}")
    )
    await call.answer()


# ============================================================
#                    TESTNI BEKOR QILISH
# ============================================================

@dp.callback_query_handler(text="user:test:cancel", state=TestStates.in_progress)
async def cancel_test(call: types.CallbackQuery, state: FSMContext):
    """Testni bekor qilish"""
    data = await state.get_data()
    lesson_id = data.get('lesson_id')

    await state.finish()

    await call.answer("❌ Test bekor qilindi", show_alert=True)

    if lesson_id:
        # Dars sahifasiga qaytish
        lesson = user_db.get_lesson(lesson_id)

        text = f"""
📹 <b>{lesson['name']}</b>

❌ Test bekor qilindi.

⬇️ Qaytadan boshlash uchun tanlang:
"""

        await call.message.edit_text(
            text,
            reply_markup=test_start(lesson_id)
        )
    else:
        await call.message.edit_text("❌ Test bekor qilindi")