"""
Admin Reports Handler (Fixed)
=============================
Vaqt mintaqasi va mantiqiy xatolar to'g'irlangan versiya
"""

from aiogram import types
import pytz  # <--- MUHIM: Vaqt mintaqasi uchun
from datetime import datetime, timedelta

from loader import dp, user_db
from keyboards.inline.admin_keyboards import reports_menu, back_button
from handlers.admin.admin_start import admin_required

# O'zbekiston vaqti
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


# ============================================================
#                    HISOBOTLAR MENYUSI
# ============================================================

@dp.callback_query_handler(text="admin:reports")
@admin_required
async def show_reports_menu(call: types.CallbackQuery):
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
    # Hozirgi vaqtni Toshkent vaqti bilan olamiz
    now = datetime.now(TASHKENT_TZ)

    today = now.strftime('%Y-%m-%d')
    week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    month_ago = (now - timedelta(days=30)).strftime('%Y-%m-%d')

    # SQL so'rovlarda DATE() funksiyasi server vaqtiga emas, saqlangan matnga qaraydi
    # SQLite da 'created_at' to'g'ri formatda saqlangan bo'lishi kerak (ISO format)

    total_users = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)

    # Bugungi userlar (DATE funksiyasi orqali)
    today_users = user_db.execute(
        f"SELECT COUNT(*) FROM Users WHERE DATE(created_at) >= DATE('{today}')",
        fetchone=True
    )

    week_users = user_db.execute(
        f"SELECT COUNT(*) FROM Users WHERE DATE(created_at) >= DATE('{week_ago}')",
        fetchone=True
    )

    month_users = user_db.execute(
        f"SELECT COUNT(*) FROM Users WHERE DATE(created_at) >= DATE('{month_ago}')",
        fetchone=True
    )

    # Kurslar va Darslar
    total_courses = user_db.execute("SELECT COUNT(*) FROM Courses WHERE is_active = TRUE", fetchone=True)
    total_lessons = user_db.execute("SELECT COUNT(*) FROM Lessons WHERE is_active = TRUE", fetchone=True)

    # To'lovlar
    total_payments = user_db.execute("SELECT COUNT(*), SUM(amount) FROM Payments WHERE status = 'approved'",
                                     fetchone=True)
    pending_payments = user_db.execute("SELECT COUNT(*) FROM Payments WHERE status = 'pending'", fetchone=True)

    # Testlar
    total_tests = user_db.execute("SELECT COUNT(*) FROM TestResults", fetchone=True)
    passed_tests = user_db.execute("SELECT COUNT(*) FROM TestResults WHERE passed = TRUE", fetchone=True)

    # Fikrlar
    total_feedbacks = user_db.execute("SELECT COUNT(*), AVG(rating) FROM Feedbacks", fetchone=True)

    payments_sum = total_payments[1] if total_payments and total_payments[1] else 0
    feedbacks_avg = total_feedbacks[1] if total_feedbacks and total_feedbacks[1] else 0

    text = f"""
📊 <b>Umumiy hisobot</b> (Sana: {today})

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
    now = datetime.now(TASHKENT_TZ)

    # Kunlik dinamika (so'nggi 7 kun)
    daily_stats = []
    for i in range(6, -1, -1):
        date_obj = now - timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d')

        count = user_db.execute(
            f"SELECT COUNT(*) FROM Users WHERE DATE(created_at) = DATE('{date_str}')",
            fetchone=True
        )
        daily_stats.append((date_str[5:], count[0] if count else 0))

    week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d')

    # Active userlar (Agar last_active NULL bo'lsa hisoblanmaydi)
    active_users = user_db.execute(
        f"SELECT COUNT(*) FROM Users WHERE last_active IS NOT NULL AND DATE(last_active) >= DATE('{week_ago}')",
        fetchone=True
    )

    paid_users = user_db.execute(
        "SELECT COUNT(DISTINCT user_id) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    total_users = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)
    avg_score = user_db.execute("SELECT AVG(total_score) FROM Users WHERE total_score > 0", fetchone=True)

    top_users = user_db.execute(
        """SELECT full_name, total_score, username FROM Users 
           WHERE total_score > 0 
           ORDER BY total_score DESC LIMIT 5""",
        fetchall=True
    )

    text = """
👥 <b>Foydalanuvchilar hisoboti</b>

📈 <b>So'nggi 7 kun (Ro'yxatdan o'tish):</b>
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
├ Pullik kurs olganlar: <b>{paid_count}</b>
├ Hali xarid qilmaganlar: <b>{free_users}</b>
└ O'rtacha ball: <b>{avg_score_val:.0f}</b>

🏆 <b>Top reyting:</b>
"""
    for i, u in enumerate(top_users or [], 1):
        name = u[0] or u[2] or "Nomalum"
        text += f"{i}. {name} - {u[1]} ball\n"

    await call.message.edit_text(text, reply_markup=back_button("admin:reports"))
    await call.answer()


# ============================================================
#                    MOLIYAVIY HISOBOT
# ============================================================

@dp.callback_query_handler(text="admin:report:finance")
@admin_required
async def show_finance_report(call: types.CallbackQuery):
    now = datetime.now(TASHKENT_TZ)

    daily_income = []
    for i in range(6, -1, -1):
        date_obj = now - timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d')

        income = user_db.execute(
            f"""SELECT SUM(amount) FROM Payments 
               WHERE status = 'approved' AND DATE(updated_at) = DATE('{date_str}')""",
            fetchone=True
        )
        daily_income.append((date_str[5:], income[0] if income and income[0] else 0))

    week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    month_ago = (now - timedelta(days=30)).strftime('%Y-%m-%d')

    week_income = user_db.execute(
        f"""SELECT SUM(amount), COUNT(*) FROM Payments 
           WHERE status = 'approved' AND DATE(updated_at) >= DATE('{week_ago}')""",
        fetchone=True
    )

    month_income = user_db.execute(
        f"""SELECT SUM(amount), COUNT(*) FROM Payments 
           WHERE status = 'approved' AND DATE(updated_at) >= DATE('{month_ago}')""",
        fetchone=True
    )

    total_income = user_db.execute(
        "SELECT SUM(amount), COUNT(*) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    avg_check = user_db.execute(
        "SELECT AVG(amount) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

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

📈 <b>So'nggi 7 kun daromadi:</b>
"""
    max_income = max([x[1] for x in daily_income]) if daily_income else 1
    if max_income == 0: max_income = 1

    for date, income in daily_income:
        bar_len = int((income / max_income) * 10)
        bar = "▓" * bar_len + "░" * (10 - bar_len)
        text += f"{date}: {income:,.0f}\n"

    week_sum = week_income[0] if week_income and week_income[0] else 0
    month_sum = month_income[0] if month_income and month_income[0] else 0
    total_sum = total_income[0] if total_income and total_income[0] else 0
    avg_check_val = avg_check[0] if avg_check and avg_check[0] else 0

    text += f"""
📊 <b>Umumiy ko'rsatkichlar:</b>
├ Shu hafta: <b>{week_sum:,.0f}</b> so'm
├ Shu oy: <b>{month_sum:,.0f}</b> so'm
├ Jami daromad: <b>{total_sum:,.0f}</b> so'm
└ O'rtacha chek: <b>{avg_check_val:,.0f}</b> so'm

📚 <b>Kurslar ulushi:</b>
"""
    for c in (by_course or []):
        text += f"• {c[0]}: {c[2]:,.0f} so'm ({c[1]} ta)\n"

    if not by_course:
        text += "📭 To'lovlar tarixi bo'sh"

    await call.message.edit_text(text, reply_markup=back_button("admin:reports"))
    await call.answer()


# ============================================================
#                    KURSLAR HISOBOTI (OPTIMAL)
# ============================================================

@dp.callback_query_handler(text="admin:report:courses")
@admin_required
async def show_courses_report(call: types.CallbackQuery):
    """Kurslar hisoboti - Optimallashtirilgan"""

    # Bu yerda og'ir querylarni soddalashtiramiz
    courses = user_db.execute(
        """SELECT c.id, c.name,
                  (SELECT COUNT(*) FROM Modules m WHERE m.course_id = c.id AND m.is_active = TRUE) as modules,
                  (SELECT COUNT(*) FROM Lessons l 
                   JOIN Modules m ON l.module_id = m.id 
                   WHERE m.course_id = c.id AND l.is_active = TRUE) as lessons,
                  (SELECT COUNT(DISTINCT p.user_id) FROM Payments p 
                   WHERE p.course_id = c.id AND p.status = 'approved') as students,
                  (SELECT SUM(p.amount) FROM Payments p 
                   WHERE p.course_id = c.id AND p.status = 'approved') as income,
                  (SELECT COUNT(*) FROM Certificates cert WHERE cert.course_id = c.id) as graduates
           FROM Courses c
           WHERE c.is_active = TRUE
           ORDER BY income DESC NULLS LAST""",
        fetchall=True
    )

    text = """
📚 <b>Kurslar hisoboti</b>
"""
    for c in (courses or []):
        course_name = c[1]
        modules = c[2]
        lessons = c[3]
        students = c[4] if c[4] else 0
        income = c[5] if c[5] else 0
        graduates = c[6] if c[6] else 0  # Sertifikat olganlar soni (Aniqroq)

        # Foiz hisoblash
        completion_rate = (graduates / students * 100) if students > 0 else 0

        text += f"""
📘 <b>{course_name}</b>
├ 📁 Modullar: {modules} | Darslar: {lessons}
├ 👥 O'quvchilar: {students} ta
├ 🎓 Sertifikat olganlar: <b>{graduates}</b> ta
├ 📊 Tugatish ko'rsatkichi: {completion_rate:.1f}%
└ 💰 Jami daromad: {income:,.0f} so'm
"""
        text += "➖➖➖➖➖➖➖➖➖➖\n"

    if not courses:
        text += "\n📭 Hozircha faol kurslar yo'q"

    await call.message.edit_text(text, reply_markup=back_button("admin:reports"))
    await call.answer()