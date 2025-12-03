"""
User Feedback Handler
=====================
Fikr qoldirish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    feedback_rating,
    feedback_skip_comment,
    feedback_thanks,
    back_button
)
from keyboards.default.user_keyboards import main_menu, cancel_button
from states.user_states import FeedbackStates


# ============================================================
#                    FIKR QOLDIRISH BOSHLASH
# ============================================================

@dp.callback_query_handler(text_startswith="user:feedback:")
async def start_feedback(call: types.CallbackQuery, state: FSMContext):
    """Fikr qoldirishni boshlash"""
    lesson_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    # Allaqachon fikr qoldirganmi
    if user_db.has_feedback(user_id, lesson_id):
        await call.answer("✅ Siz allaqachon fikr qoldirgansiz!", show_alert=True)
        return

    await state.update_data(
        lesson_id=lesson_id,
        lesson_name=lesson['name']
    )

    text = f"""
💬 <b>Fikr qoldirish</b>

📹 Dars: {lesson['name']}

⭐️ Bu darsni qanday baholaysiz?

1 ⭐️ - Yomon
2 ⭐️ - Qoniqarsiz
3 ⭐️ - O'rtacha
4 ⭐️ - Yaxshi
5 ⭐️ - A'lo

⬇️ Bahoni tanlang:
"""

    await call.message.edit_text(text, reply_markup=feedback_rating(lesson_id))
    await FeedbackStates.rating.set()
    await call.answer()


# ============================================================
#                    BAHO TANLASH
# ============================================================

@dp.callback_query_handler(text_startswith="user:rate:", state=FeedbackStates.rating)
async def select_rating(call: types.CallbackQuery, state: FSMContext):
    """Baho tanlash"""
    rating = int(call.data.split(":")[-1])

    await state.update_data(rating=rating)

    data = await state.get_data()

    # Yulduzlar
    stars = "⭐️" * rating + "☆" * (5 - rating)

    text = f"""
💬 <b>Fikr qoldirish</b>

📹 Dars: {data['lesson_name']}
⭐️ Baho: {stars}

📝 Izoh qoldirmoqchimisiz?

<i>Bu ixtiyoriy. O'tkazib yuborishingiz mumkin.</i>
"""

    await call.message.edit_text(text, reply_markup=feedback_skip_comment(data['lesson_id']))
    await call.message.answer("✍️ Izoh yozing yoki o'tkazib yuboring:", reply_markup=cancel_button())
    await FeedbackStates.comment.set()
    await call.answer()


# ============================================================
#                    IZOH YOZISH
# ============================================================

@dp.message_handler(state=FeedbackStates.comment)
async def write_comment(message: types.Message, state: FSMContext):
    """Izoh yozish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=main_menu())
        return

    comment = message.text.strip()

    if len(comment) > 500:
        await message.answer("❌ Izoh 500 belgidan oshmasligi kerak!")
        return

    await state.update_data(comment=comment)

    # Fikrni saqlash
    await save_feedback(message.from_user.id, state)


@dp.callback_query_handler(text_startswith="user:feedback:skip:", state=FeedbackStates.comment)
async def skip_comment(call: types.CallbackQuery, state: FSMContext):
    """Izohni o'tkazib yuborish"""
    await state.update_data(comment=None)

    # Fikrni saqlash
    await save_feedback(call.from_user.id, state, call.message)
    await call.answer()


# ============================================================
#                    FIKRNI SAQLASH
# ============================================================

async def save_feedback(telegram_id: int, state: FSMContext, message: types.Message = None):
    """Fikrni saqlash"""
    data = await state.get_data()

    user_id = user_db.get_user_id(telegram_id)

    # Fikr uchun ball
    feedback_score = user_db.get_setting('feedback_score')
    score_to_add = int(feedback_score) if feedback_score and feedback_score.isdigit() else 5

    # Fikrni qo'shish
    feedback_id = user_db.add_feedback(
        user_id=user_id,
        lesson_id=data['lesson_id'],
        rating=data['rating'],
        comment=data.get('comment'),
        score_given=score_to_add
    )

    if feedback_id:
        # Ball qo'shish
        user_db.add_score(telegram_id, score_to_add)

        stars = "⭐️" * data['rating']

        text = f"""
✅ <b>Rahmat fikringiz uchun!</b>

📹 Dars: {data['lesson_name']}
{stars}
{f"💬 {data['comment']}" if data.get('comment') else ""}

🏆 +{score_to_add} ball qo'shildi!
"""

        if message:
            await message.edit_text(text, reply_markup=feedback_thanks(data['lesson_id']))
        else:
            # Handler message.answer orqali
            await bot.send_message(telegram_id, text, reply_markup=main_menu())

    else:
        text = "❌ Xatolik yuz berdi! Qaytadan urinib ko'ring."

        if message:
            await message.edit_text(text)
        else:
            await bot.send_message(telegram_id, text, reply_markup=main_menu())

    await state.finish()


# ============================================================
#                    FIKRLAR KO'RISH (USER)
# ============================================================

@dp.callback_query_handler(text_startswith="user:feedbacks:lesson:")
async def show_lesson_feedbacks(call: types.CallbackQuery):
    """Dars fikrlarini ko'rish"""
    lesson_id = int(call.data.split(":")[-1])

    lesson = user_db.get_lesson(lesson_id)

    if not lesson:
        await call.answer("❌ Dars topilmadi!", show_alert=True)
        return

    # Fikrlarni olish
    feedbacks = user_db.get_lesson_feedbacks(lesson_id, limit=10)
    avg_rating = user_db.get_lesson_average_rating(lesson_id)

    if not feedbacks:
        await call.answer("📭 Bu darsda hali fikrlar yo'q", show_alert=True)
        return

    # O'rtacha baho
    avg_stars = "⭐️" * round(avg_rating) if avg_rating else ""

    text = f"""
💬 <b>Dars fikrlari</b>

📹 {lesson['name']}
📊 O'rtacha baho: {avg_rating:.1f} {avg_stars}

<b>So'nggi fikrlar:</b>
"""

    for fb in feedbacks:
        stars = "⭐️" * fb['rating']
        date = fb['created_at'][:10] if fb.get('created_at') else ""

        text += f"\n{stars}"
        if fb.get('comment'):
            text += f"\n<i>{fb['comment'][:100]}{'...' if len(fb.get('comment', '')) > 100 else ''}</i>"
        text += f"\n<code>{date}</code>\n"

    await call.message.edit_text(
        text,
        reply_markup=back_button(f"user:lesson:view:{lesson_id}")
    )
    await call.answer()