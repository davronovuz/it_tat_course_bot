"""
Admin Reports Handler
=====================
Hisobotlar va statistika handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from datetime import datetime, timedelta

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import reports_menu, back_button
from handlers.admin.admin_start import admin_required


# ============================================================
#                    HISOBOTLAR MENYUSI
# ============================================================

@dp.callback_query_handler(text="admin:reports")
@admin_required
async def show_reports_menu(call: types.CallbackQuery):
    """Hisobotlar menyusi"""

    text = f"""
📊 <b>Hisobotlar</b>

Quyidagi hisobotlardan birini tanlang:

📈 <b>Umumiy</b> - Bot statistikasi
👥 <b>Foydalanuvchilar</b> - Foydalanuvchilar tahlili
💰 <b>Moliyaviy</b> - Daromadlar tahlili
📚 <b>Kurslar</b> - Kurslar statistikasi

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=reports_menu())
    await call.answer()


# ============================================================
#                    UMUMIY HISOBOT
# ============================================================

@dp.callback_query_handler(text="admin:report:general")
@admin_required
async def show_general_report(call: types.CallbackQuery):
    """Umumiy hisobot"""

    # Foydalanuvchilar
    total_users = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)

    today = datetime.now().strftime('%Y-%m-%d')
    today_users = user_db.execute(
        "SELECT COUNT(*) FROM Users WHERE DATE(created_at) = ?",
        parameters=(today,),
        fetchone=True
    )

    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_users = user_db.execute(
        "SELECT COUNT(*) FROM Users WHERE DATE(created_at) >= ?",
        parameters=(week_ago,),
        fetchone=True
    )

    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    month_users = user_db.execute(
        "SELECT COUNT(*) FROM Users WHERE DATE(created_at) >= ?",
        parameters=(month_ago,),
        fetchone=True
    )

    # Kurslar
    total_courses = user_db.execute(
        "SELECT COUNT(*) FROM Courses WHERE is_active = TRUE",
        fetchone=True
    )
    total_lessons = user_db.execute(
        "SELECT COUNT(*) FROM Lessons WHERE is_active = TRUE",
        fetchone=True
    )

    # To'lovlar
    total_payments = user_db.execute(
        "SELECT COUNT(*), SUM(amount) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    pending_payments = user_db.execute(
        "SELECT COUNT(*) FROM Payments WHERE status = 'pending'",
        fetchone=True
    )

    # Testlar
    total_tests = user_db.execute(
        "SELECT COUNT(*) FROM TestResults",
        fetchone=True
    )
    passed_tests = user_db.execute(
        "SELECT COUNT(*) FROM TestResults WHERE passed = TRUE",
        fetchone=True
    )

    # Fikrlar
    total_feedbacks = user_db.execute(
        "SELECT COUNT(*), AVG(rating) FROM Feedbacks",
        fetchone=True
    )

    # Qiymatlarni oldindan hisoblash
    payments_sum = total_payments[1] if total_payments and total_payments[1] else 0
    feedbacks_avg = total_feedbacks[1] if total_feedbacks and total_feedbacks[1] else 0

    text = f"""
📊 <b>Umumiy hisobot</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: <b>{total_users[0] if total_users else 0}</b>
├ Bugun: <b>{today_users[0] if today_users else 0}</b>
├ Shu hafta: <b>{week_users[0] if week_users else 0}</b>
└ Shu oy: <b>{month_users[0] if month_users else 0}</b>

📚 <b>Kontent:</b>
├ Kurslar: <b>{total_courses[0] if total_courses else 0}</b>
└ Darslar: <b>{total_lessons[0] if total_lessons else 0}</b>

💰 <b>To'lovlar:</b>
├ Tasdiqlangan: <b>{total_payments[0] if total_payments else 0}</b>
├ Summa: <b>{payments_sum:,.0f}</b> so'm
└ Kutilayotgan: <b>{pending_payments[0] if pending_payments else 0}</b>

📝 <b>Testlar:</b>
├ Jami: <b>{total_tests[0] if total_tests else 0}</b>
└ Muvaffaqiyatli: <b>{passed_tests[0] if passed_tests else 0}</b>

💬 <b>Fikrlar:</b>
├ Jami: <b>{total_feedbacks[0] if total_feedbacks else 0}</b>
└ O'rtacha: <b>{feedbacks_avg:.1f}</b> ⭐️
"""

    await call.message.edit_text(text, reply_markup=back_button("admin:reports"))
    await call.answer()


# ============================================================
#                    FOYDALANUVCHILAR HISOBOTI
# ============================================================

@dp.callback_query_handler(text="admin:report:users")
@admin_required
async def show_users_report(call: types.CallbackQuery):
    """Foydalanuvchilar hisoboti"""

    # Kunlik dinamika (so'nggi 7 kun)
    daily_stats = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        count = user_db.execute(
            "SELECT COUNT(*) FROM Users WHERE DATE(created_at) = ?",
            parameters=(date,),
            fetchone=True
        )
        daily_stats.append((date[5:], count[0] if count else 0))

    # Faol foydalanuvchilar (oxirgi 7 kunda) — last_active ustunidan
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    active_users = user_db.execute(
        "SELECT COUNT(*) FROM Users WHERE DATE(last_active) >= ?",
        parameters=(week_ago,),
        fetchone=True
    )

    # Pullik va bepul
    paid_users = user_db.execute(
        "SELECT COUNT(DISTINCT user_id) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    total_users = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)

    # O'rtacha ball
    avg_score = user_db.execute(
        "SELECT AVG(total_score) FROM Users WHERE total_score > 0",
        fetchone=True
    )

    # Eng faol foydalanuvchilar
    top_users = user_db.execute(
        """SELECT full_name, total_score FROM Users 
           WHERE total_score > 0 
           ORDER BY total_score DESC LIMIT 5""",
        fetchall=True
    )

    text = """
👥 <b>Foydalanuvchilar hisoboti</b>

📈 <b>So'nggi 7 kun:</b>
"""

    for date, count in daily_stats:
        bar = "▓" * min(count, 10) + "░" * (10 - min(count, 10))
        text += f"{date}: [{bar}] {count}\n"

    total_count = total_users[0] if total_users else 0
    paid_count = paid_users[0] if paid_users else 0
    free_users = total_count - paid_count
    active_count = active_users[0] if active_users else 0
    avg_score_val = avg_score[0] if avg_score and avg_score[0] else 0

    text += f"""
📊 <b>Statistika:</b>
├ Faol (7 kun): <b>{active_count}</b>
├ Pullik: <b>{paid_count}</b>
├ Bepul: <b>{free_users}</b>
└ O'rtacha ball: <b>{avg_score_val:.0f}</b>

🏆 <b>Top foydalanuvchilar:</b>
"""

    for i, u in enumerate(top_users or [], 1):
        text += f"{i}. {u[0] or 'Nomalum'} - {u[1]} ball\n"

    await call.message.edit_text(text, reply_markup=back_button("admin:reports"))
    await call.answer()


# ============================================================
#                    MOLIYAVIY HISOBOT
# ============================================================

@dp.callback_query_handler(text="admin:report:finance")
@admin_required
async def show_finance_report(call: types.CallbackQuery):
    """Moliyaviy hisobot"""

    # Kunlik daromad (so'nggi 7 kun) — updated_at ustunidan
    daily_income = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        income = user_db.execute(
            """SELECT SUM(amount) FROM Payments 
               WHERE status = 'approved' AND DATE(updated_at) = ?""",
            parameters=(date,),
            fetchone=True
        )
        daily_income.append((date[5:], income[0] if income and income[0] else 0))

    # Haftalik
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_income = user_db.execute(
        """SELECT SUM(amount), COUNT(*) FROM Payments 
           WHERE status = 'approved' AND DATE(updated_at) >= ?""",
        parameters=(week_ago,),
        fetchone=True
    )

    # Oylik
    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    month_income = user_db.execute(
        """SELECT SUM(amount), COUNT(*) FROM Payments 
           WHERE status = 'approved' AND DATE(updated_at) >= ?""",
        parameters=(month_ago,),
        fetchone=True
    )

    # Umumiy
    total_income = user_db.execute(
        "SELECT SUM(amount), COUNT(*) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    # O'rtacha chek
    avg_check = user_db.execute(
        "SELECT AVG(amount) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    # Kurslar bo'yicha
    by_course = user_db.execute(
        """SELECT c.name, COUNT(p.id), SUM(p.amount)
           FROM Payments p
           JOIN Courses c ON p.course_id = c.id
           WHERE p.status = 'approved'
           GROUP BY c.id
           ORDER BY SUM(p.amount) DESC
           LIMIT 5""",
        fetchall=True
    )

    text = """
💰 <b>Moliyaviy hisobot</b>

📈 <b>So'nggi 7 kun:</b>
"""

    max_income = max([x[1] for x in daily_income]) if daily_income else 1
    if max_income == 0:
        max_income = 1

    for date, income in daily_income:
        bar_len = int((income / max_income) * 10)
        bar = "▓" * bar_len + "░" * (10 - bar_len)
        text += f"{date}: [{bar}] {income:,.0f}\n"

    # Qiymatlarni oldindan hisoblash
    week_sum = week_income[0] if week_income and week_income[0] else 0
    week_count = week_income[1] if week_income and week_income[1] else 0
    month_sum = month_income[0] if month_income and month_income[0] else 0
    month_count = month_income[1] if month_income and month_income[1] else 0
    total_sum = total_income[0] if total_income and total_income[0] else 0
    avg_check_val = avg_check[0] if avg_check and avg_check[0] else 0

    text += f"""
📊 <b>Daromadlar:</b>
├ Shu hafta: <b>{week_sum:,.0f}</b> so'm ({week_count} ta)
├ Shu oy: <b>{month_sum:,.0f}</b> so'm ({month_count} ta)
├ Jami: <b>{total_sum:,.0f}</b> so'm
└ O'rtacha chek: <b>{avg_check_val:,.0f}</b> so'm

📚 <b>Kurslar bo'yicha:</b>
"""

    for c in (by_course or []):
        course_sum = c[2] if c[2] else 0
        text += f"• {c[0]}: {course_sum:,.0f} so'm ({c[1]} ta)\n"

    if not by_course:
        text += "📭 To'lovlar yo'q\n"

    await call.message.edit_text(text, reply_markup=back_button("admin:reports"))
    await call.answer()


# ============================================================
#                    KURSLAR HISOBOTI
# ============================================================

@dp.callback_query_handler(text="admin:report:courses")
@admin_required
async def show_courses_report(call: types.CallbackQuery):
    """Kurslar hisoboti"""

    # Kurslar statistikasi
    courses = user_db.execute(
        """SELECT c.id, c.name,
                  (SELECT COUNT(*) FROM Modules m WHERE m.course_id = c.id AND m.is_active = TRUE) as modules,
                  (SELECT COUNT(*) FROM Lessons l 
                   JOIN Modules m ON l.module_id = m.id 
                   WHERE m.course_id = c.id AND l.is_active = TRUE) as lessons,
                  (SELECT COUNT(DISTINCT p.user_id) FROM Payments p 
                   WHERE p.course_id = c.id AND p.status = 'approved') as students,
                  (SELECT SUM(p.amount) FROM Payments p 
                   WHERE p.course_id = c.id AND p.status = 'approved') as income
           FROM Courses c
           WHERE c.is_active = TRUE
           ORDER BY income DESC NULLS LAST""",
        fetchall=True
    )

    text = """
📚 <b>Kurslar hisoboti</b>

"""

    for c in (courses or []):
        income = c[5] if c[5] else 0
        students = c[4] if c[4] else 0

        # Tugatish foizi
        completed = user_db.execute(
            """SELECT COUNT(DISTINCT up.user_id) 
               FROM UserProgress up
               JOIN Lessons l ON up.lesson_id = l.id
               JOIN Modules m ON l.module_id = m.id
               WHERE m.course_id = ? AND up.status = 'completed'
               GROUP BY up.user_id
               HAVING COUNT(*) = (
                   SELECT COUNT(*) FROM Lessons l2
                   JOIN Modules m2 ON l2.module_id = m2.id
                   WHERE m2.course_id = ? AND l2.is_active = TRUE
               )""",
            parameters=(c[0], c[0]),
            fetchall=True
        )

        completed_count = len(completed) if completed else 0
        completion_rate = (completed_count / students * 100) if students > 0 else 0

        text += f"""
📚 <b>{c[1]}</b>
├ 📁 Modullar: {c[2]}
├ 📹 Darslar: {c[3]}
├ 👥 O'quvchilar: {students}
├ 💰 Daromad: {income:,.0f} so'm
└ ✅ Tugatgan: {completed_count} ({completion_rate:.0f}%)

"""

    if not courses:
        text += "📭 Faol kurslar yo'q"

    await call.message.edit_text(text, reply_markup=back_button("admin:reports"))
    await call.answer()