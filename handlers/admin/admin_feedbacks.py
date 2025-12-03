"""
Admin Feedbacks Handler
=======================
Fikrlarni boshqarish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from datetime import datetime

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import feedbacks_menu, back_button
from handlers.admin.admin_start import admin_required


# ============================================================
#                    FIKRLAR MENYUSI
# ============================================================

@dp.callback_query_handler(text="admin:feedbacks")
@admin_required
async def show_feedbacks_menu(call: types.CallbackQuery):
    """Fikrlar menyusi"""

    # Statistika
    total = user_db.execute("SELECT COUNT(*) FROM Feedbacks", fetchone=True)

    avg = user_db.execute(
        "SELECT AVG(rating) FROM Feedbacks",
        fetchone=True
    )

    today = datetime.now().strftime('%Y-%m-%d')
    today_count = user_db.execute(
        "SELECT COUNT(*) FROM Feedbacks WHERE DATE(created_at) = ?",
        parameters=(today,),
        fetchone=True
    )

    # Yulduzlar taqsimoti
    stars = user_db.execute(
        """SELECT rating, COUNT(*) FROM Feedbacks GROUP BY rating ORDER BY rating DESC""",
        fetchall=True
    )

    stars_text = ""
    for s in (stars or []):
        stars_text += f"{'⭐️' * s[0]}: {s[1]} ta\n"

    avg_rating = avg[0] if avg and avg[0] else 0

    text = f"""
💬 <b>Fikrlar boshqaruvi</b>

📊 <b>Statistika:</b>
├ 💬 Jami: <b>{total[0] if total else 0}</b>
├ 📅 Bugun: <b>{today_count[0] if today_count else 0}</b>
└ ⭐️ O'rtacha: <b>{avg_rating:.1f}</b>

<b>Yulduzlar:</b>
{stars_text}
⬇️ Bo'limni tanlang:
"""

    await call.message.edit_text(text, reply_markup=feedbacks_menu())
    await call.answer()


# ============================================================
#                    SO'NGI FIKRLAR
# ============================================================

@dp.callback_query_handler(text="admin:feedbacks:recent")
@admin_required
async def show_recent_feedbacks(call: types.CallbackQuery):
    """So'nggi fikrlar"""

    feedbacks = user_db.execute(
        """SELECT f.id, f.rating, f.comment, f.created_at,
                  u.full_name, l.name as lesson_name
           FROM Feedbacks f
           JOIN Users u ON f.user_id = u.id
           JOIN Lessons l ON f.lesson_id = l.id
           ORDER BY f.created_at DESC
           LIMIT 15""",
        fetchall=True
    )

    if not feedbacks:
        await call.answer("📭 Fikrlar yo'q", show_alert=True)
        return

    text = f"""
💬 <b>So'nggi fikrlar</b>

"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for f in feedbacks:
        stars = "⭐️" * f[1]
        name = f[4] or "Noma'lum"
        lesson = f[5][:20] + "..." if len(f[5]) > 20 else f[5]
        date = f[3][:10] if f[3] else ""

        text += f"{stars}\n"
        text += f"👤 {name} | 📹 {lesson}\n"
        if f[2]:
            comment = f[2][:50] + "..." if len(f[2]) > 50 else f[2]
            text += f"💬 <i>{comment}</i>\n"
        text += f"📅 {date}\n\n"

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:feedbacks"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ============================================================
#                    YULDUZ BO'YICHA FIKRLAR
# ============================================================

@dp.callback_query_handler(text="admin:feedbacks:rating")
@admin_required
async def show_feedbacks_by_rating(call: types.CallbackQuery):
    """Yulduz bo'yicha fikrlar"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for i in range(5, 0, -1):
        count = user_db.execute(
            "SELECT COUNT(*) FROM Feedbacks WHERE rating = ?",
            parameters=(i,),
            fetchone=True
        )

        keyboard.add(types.InlineKeyboardButton(
            f"{'⭐️' * i} ({count[0] if count else 0} ta)",
            callback_data=f"admin:feedbacks:star:{i}"
        ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:feedbacks"
    ))

    await call.message.edit_text(
        "⭐️ <b>Yulduz bo'yicha fikrlar</b>\n\n"
        "Yulduzni tanlang:",
        reply_markup=keyboard
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:feedbacks:star:")
@admin_required
async def show_feedbacks_star(call: types.CallbackQuery):
    """Ma'lum yulduzli fikrlar"""
    rating = int(call.data.split(":")[-1])

    feedbacks = user_db.execute(
        """SELECT f.id, f.comment, f.created_at,
                  u.full_name, l.name as lesson_name, c.name as course_name
           FROM Feedbacks f
           JOIN Users u ON f.user_id = u.id
           JOIN Lessons l ON f.lesson_id = l.id
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE f.rating = ?
           ORDER BY f.created_at DESC
           LIMIT 15""",
        parameters=(rating,),
        fetchall=True
    )

    if not feedbacks:
        await call.answer("📭 Bu yulduzda fikrlar yo'q", show_alert=True)
        return

    stars = "⭐️" * rating

    text = f"""
{stars} <b>Fikrlar</b>

Jami: {len(feedbacks)} ta (so'nggi 15)

"""

    for f in feedbacks:
        name = f[3] or "Noma'lum"
        date = f[2][:10] if f[2] else ""

        text += f"👤 <b>{name}</b>\n"
        text += f"📚 {f[5]} → {f[4]}\n"
        if f[1]:
            comment = f[1][:100] + "..." if len(f[1]) > 100 else f[1]
            text += f"💬 <i>{comment}</i>\n"
        text += f"📅 {date}\n\n"

    await call.message.edit_text(
        text,
        reply_markup=back_button("admin:feedbacks:rating")
    )
    await call.answer()


# ============================================================
#                    FIKRLAR STATISTIKASI
# ============================================================

@dp.callback_query_handler(text="admin:feedbacks:stats")
@admin_required
async def show_feedbacks_stats(call: types.CallbackQuery):
    """Fikrlar statistikasi"""

    # Umumiy
    total = user_db.execute("SELECT COUNT(*), AVG(rating) FROM Feedbacks", fetchone=True)

    # Kurslar bo'yicha
    by_course = user_db.execute(
        """SELECT c.name, COUNT(f.id), AVG(f.rating)
           FROM Feedbacks f
           JOIN Lessons l ON f.lesson_id = l.id
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           GROUP BY c.id
           ORDER BY AVG(f.rating) DESC""",
        fetchall=True
    )

    # Eng ko'p fikr olgan darslar
    top_lessons = user_db.execute(
        """SELECT l.name, COUNT(f.id), AVG(f.rating)
           FROM Feedbacks f
           JOIN Lessons l ON f.lesson_id = l.id
           GROUP BY l.id
           ORDER BY COUNT(f.id) DESC
           LIMIT 5""",
        fetchall=True
    )

    # Eng past baholi darslar
    low_rated = user_db.execute(
        """SELECT l.name, AVG(f.rating), COUNT(f.id)
           FROM Feedbacks f
           JOIN Lessons l ON f.lesson_id = l.id
           GROUP BY l.id
           HAVING COUNT(f.id) >= 3
           ORDER BY AVG(f.rating) ASC
           LIMIT 5""",
        fetchall=True
    )

    text = f"""
📊 <b>Fikrlar statistikasi</b>

💬 Jami fikrlar: <b>{total[0] if total else 0}</b>
⭐️ O'rtacha baho: <b>{total[1]:.1f if total and total[1] else 0}</b>

<b>Kurslar bo'yicha:</b>
"""

    for c in (by_course or []):
        stars = "⭐️" * round(c[2]) if c[2] else ""
        text += f"📚 {c[0]}: {c[2]:.1f} ({c[1]} ta)\n"

    text += "\n<b>Eng faol darslar:</b>\n"
    for l in (top_lessons or []):
        text += f"📹 {l[0][:25]}: {l[1]} ta fikr\n"

    if low_rated:
        text += "\n<b>Eng past baholi:</b>\n"
        for l in low_rated:
            text += f"⚠️ {l[0][:25]}: {l[1]:.1f}⭐️\n"

    await call.message.edit_text(text, reply_markup=back_button("admin:feedbacks"))
    await call.answer()