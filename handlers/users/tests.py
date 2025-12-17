"""
User Tests Handler (TUZATILGAN - FINAL)
=======================================
Test yechish logikasi.
Eng muhim o'zgarish: Sertifikat olish tugmasiga 'course_id' to'g'ri biriktirildi.
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from datetime import datetime

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    test_start,
    test_question,
    test_result
)
from states.user_states import TestStates


# ============================================================
#                    TEST BOSHLASH
# ============================================================

@dp.callback_query_handler(text_startswith="user:test:")
async def start_test(call: types.CallbackQuery, state: FSMContext):
    """
    Testni boshlash
    """
    parts = call.data.split(":")

    # user:test:begin:{lesson_id} bo'lsa -> Testni boshlash
    if len(parts) > 2 and parts[2] == "begin":
        await begin_test(call, state)
        return

    # user:test:{lesson_id} bo'lsa -> Test infosini ko'rsatish
    lesson_id = int(parts[-1])
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Xatolik: Foydalanuvchi topilmadi", show_alert=True)
        return

    # Dars va Testni tekshirish
    lesson = user_db.get_lesson(lesson_id)
    if not lesson:
        await call.answer("❌ Dars topilmadi", show_alert=True)
        return

    test = user_db.get_test_by_lesson(lesson_id)
    if not test:
        await call.answer("❌ Bu darsda test yo'q", show_alert=True)
        return

    questions = user_db.get_test_questions(test['id'])
    if not questions:
        await call.answer("📭 Testda savollar yo'q", show_alert=True)
        return

    # Ma'lumotlarni State xotirasiga yuklash
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
📝 <b>Test: {lesson['name']}</b>

📊 Savollar soni: {len(questions)} ta
🎯 O'tish bali: {test.get('passing_score', 60)}%

⬇️ Tayyor bo'lsangiz, boshlash tugmasini bosing:
"""
    # Xabarni yangilash yoki yangisini yuborish
    try:
        await call.message.edit_text(text, reply_markup=test_start(lesson_id))
    except:
        await call.message.delete()
        await call.message.answer(text, reply_markup=test_start(lesson_id))

    await call.answer()


async def begin_test(call: types.CallbackQuery, state: FSMContext):
    """
    Birinchi savolni chiqarish
    """
    data = await state.get_data()
    if not data.get('questions'):
        await call.answer("❌ Xatolik: Test ma'lumotlari yo'qoldi", show_alert=True)
        return

    await TestStates.in_progress.set()
    await show_question(call.message, state, 0)
    await call.answer()


# ============================================================
#                    SAVOL KO'RSATISH
# ============================================================

async def show_question(message: types.Message, state: FSMContext, index: int):
    """
    Navbatdagi savolni ko'rsatish
    """
    import html
    data = await state.get_data()
    questions = data['questions']

    # Agar savollar tugagan bo'lsa -> Natijani hisoblash
    if index >= len(questions):
        await show_test_result(message, state)
        return

    # Hozirgi savolni olish
    question = questions[index]
    await state.update_data(current_index=index)

    # Variantlarni tayyorlash
    options = []
    options.append(('A', question.get('a', '')))
    options.append(('B', question.get('b', '')))
    if question.get('c'): options.append(('C', question['c']))
    if question.get('d'): options.append(('D', question['d']))

    question_text = html.escape(str(question.get('question', '')))

    text = f"""
📝 <b>Savol {index + 1}/{len(questions)}</b>

❓ {question_text}
"""
    for letter, option in options:
        text += f"\n<b>{letter})</b> {html.escape(str(option))}"

    # Tugmalarni chiqarish
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
    Foydalanuvchi javob berganda ishlaydi
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

    # Kichik feedback (Toast xabar)
    if answer.upper() == correct:
        msg = random.choice(["✅ To'g'ri!", "✅ Barakalla!", "✅ Ajoyib!"])
    else:
        msg = random.choice(["❌ Xato!", "❌ Afsuski xato", "❌ Noto'g'ri"])

    await call.answer(msg, show_alert=False)

    # Keyingi savolga o'tish
    await show_question(call.message, state, question_index + 1)


# ============================================================
#                    TEST NATIJASI (MUHIM QISM)
# ============================================================

async def show_test_result(message: types.Message, state: FSMContext):
    """
    Test tugadi, natijani hisoblash va darsni ochish/yopish
    """
    data = await state.get_data()

    questions = data.get('questions', [])
    answers = data.get('answers', {})
    passing_score = data.get('passing_score', 60)
    lesson_id = data.get('lesson_id')
    test_id = data.get('test_id')

    # To'g'ri javoblarni sanash
    correct_count = 0
    total_count = len(questions)

    for i, question in enumerate(questions):
        user_answer = answers.get(str(i))
        correct_answer = question.get('correct', '').upper()
        if user_answer and user_answer.upper() == correct_answer:
            correct_count += 1

    # Natija foizi
    percentage = (correct_count / total_count * 100) if total_count > 0 else 0
    passed = percentage >= passing_score

    # Bazaga yozish
    telegram_id = message.chat.id
    user = user_db.get_user(telegram_id)

    if user:
        # Natijani saqlash
        user_db.save_test_result(
            telegram_id=telegram_id,
            test_id=test_id,
            score=int(percentage),
            total_questions=total_count,
            correct_answers=correct_count,
            answers=answers
        )

        # Ball berish (har 10% uchun 1 ball)
        user_db.add_score(telegram_id, int(percentage / 10))

        # Agar o'tgan bo'lsa -> Darsni "Completed" qilish
        if passed:
            current_status = get_lesson_status(user['id'], lesson_id)
            if current_status != 'completed':
                complete_lesson_db(user['id'], lesson_id)
                user_db.add_score(telegram_id, 10)  # Dars tugagani uchun bonus

    # Keyingi darsni aniqlash
    next_lesson = get_next_lesson(lesson_id)
    is_last_lesson = next_lesson is None

    # --- ⚠️ MUHIM: COURSE ID NI ANIQLASH ---
    lesson_info = user_db.get_lesson(lesson_id)
    # Agar lesson_info topilsa course_id ni olamiz, aks holda 1
    course_id = lesson_info['course_id'] if lesson_info else 1
    # ----------------------------------------

    # Xabar matni
    if passed:
        text = f"""
🎉 <b>Tabriklaymiz! Testdan o'tdingiz!</b>

✅ To'g'ri javoblar: {correct_count}/{total_count}
📊 Natija: {percentage:.0f}%

🎁 Sizga ballar qo'shildi.
✅ Dars muvaffaqiyatli yakunlandi!
"""
        if is_last_lesson:
            text += "\n🎓 <b>Siz kursni to'liq tugatdingiz! Sertifikat olishingiz mumkin.</b>"
    else:
        text = f"""
😔 <b>Afsuski, yetarli ball to'play olmadingiz.</b>

📊 Natija: {percentage:.0f}%
🎯 Talab qilinadi: {passing_score}%

🔄 Iltimos, darsni qayta ko'rib chiqib, testni qayta topshiring.
"""

    await state.finish()

    try:
        await message.edit_text(
            text,
            reply_markup=test_result(
                lesson_id=lesson_id,
                passed=passed,
                next_lesson_id=next_lesson['id'] if next_lesson else None,
                is_last_lesson=is_last_lesson,
                course_id=course_id  # <--- TUZATILDI: course_id yuborilyapti
            )
        )
    except:
        await message.answer(
            text,
            reply_markup=test_result(
                lesson_id=lesson_id,
                passed=passed,
                next_lesson_id=next_lesson['id'] if next_lesson else None,
                is_last_lesson=is_last_lesson,
                course_id=course_id  # <--- TUZATILDI
            )
        )


# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def get_lesson_status(user_id: int, lesson_id: int) -> str:
    result = user_db.execute(
        "SELECT status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
        parameters=(user_id, lesson_id),
        fetchone=True
    )
    return result[0] if result else 'unlocked'


def complete_lesson_db(user_id: int, lesson_id: int):
    # Agar bor bo'lsa update, yo'q bo'lsa insert
    existing = user_db.execute(
        "SELECT id FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
        parameters=(user_id, lesson_id),
        fetchone=True
    )
    if existing:
        user_db.execute(
            "UPDATE UserProgress SET status = 'completed', completed_at = datetime('now') WHERE user_id = ? AND lesson_id = ?",
            parameters=(user_id, lesson_id), commit=True
        )
    else:
        user_db.execute(
            "INSERT INTO UserProgress (user_id, lesson_id, status, completed_at) VALUES (?, ?, 'completed', datetime('now'))",
            parameters=(user_id, lesson_id), commit=True
        )


def get_next_lesson(current_lesson_id: int) -> dict | None:
    """Keyingi darsni topish"""
    current = user_db.get_lesson(current_lesson_id)
    if not current: return None

    # 1. Shu modul ichidagi keyingi dars
    next_in_module = user_db.execute(
        "SELECT id, name FROM Lessons WHERE module_id = ? AND order_num > ? AND is_active = TRUE ORDER BY order_num LIMIT 1",
        parameters=(current['module_id'], current['order_num']), fetchone=True
    )
    if next_in_module: return {'id': next_in_module[0], 'name': next_in_module[1]}

    # 2. Keyingi modulning birinchi darsi
    module = user_db.get_module(current['module_id'])
    if not module: return None

    next_module = user_db.execute(
        "SELECT id FROM Modules WHERE course_id = ? AND order_num > ? AND is_active = TRUE ORDER BY order_num LIMIT 1",
        parameters=(module['course_id'], module['order_num']), fetchone=True
    )

    if next_module:
        first_lesson = user_db.execute(
            "SELECT id, name FROM Lessons WHERE module_id = ? AND is_active = TRUE ORDER BY order_num LIMIT 1",
            parameters=(next_module[0],), fetchone=True
        )
        if first_lesson: return {'id': first_lesson[0], 'name': first_lesson[1]}

    return None