"""
User Progress Handler
=====================
Natijalar, progress va sertifikat handlerlari
"""

from aiogram import types

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import (
    my_results_menu,
    course_progress_detail,
    certificates_list,
    back_button
)
from keyboards.default.user_keyboards import main_menu


# ============================================================
#                    NATIJALAR MENYUSI
# ============================================================

@dp.callback_query_handler(text="user:results")
async def show_results_menu(call: types.CallbackQuery):
    """Natijalar menyusi"""
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
        return

    user_id = user['id']
    total_score = user.get('total_score', 0)

    # Test natijalari
    test_results = user_db.execute(
        """SELECT COUNT(*), SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END)
           FROM TestResults WHERE user_id = ?""",
        parameters=(user_id,),
        fetchone=True
    )
    total_tests = test_results[0] if test_results else 0
    passed_tests = test_results[1] if test_results and test_results[1] else 0

    # Tugatilgan darslar
    completed_lessons = user_db.execute(
        """SELECT COUNT(*) FROM UserProgress 
           WHERE user_id = ? AND status = 'completed'""",
        parameters=(user_id,),
        fetchone=True
    )
    completed_count = completed_lessons[0] if completed_lessons else 0

    # Sertifikatlar
    certificates = user_db.execute(
        """SELECT COUNT(*) FROM Certificates WHERE user_id = ?""",
        parameters=(user_id,),
        fetchone=True
    )
    cert_count = certificates[0] if certificates else 0

    text = f"""
📊 <b>Mening natijalarim</b>

🏆 <b>Umumiy statistika:</b>
├ ⭐️ Jami ball: <b>{total_score}</b>
├ 📹 Tugatilgan darslar: <b>{completed_count}</b>
├ 📝 Yechilgan testlar: <b>{total_tests}</b>
├ ✅ Muvaffaqiyatli: <b>{passed_tests}</b>
└ 🎓 Sertifikatlar: <b>{cert_count}</b>

⬇️ Batafsil ko'rish uchun tanlang:
"""

    await call.message.edit_text(text, reply_markup=my_results_menu())
    await call.answer()


# ============================================================
#                    KURS PROGRESSI
# ============================================================

@dp.callback_query_handler(text="user:my_progress")
async def show_my_courses_progress(call: types.CallbackQuery):
    """Mening kurslarim progressi"""
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # Dostup bor kurslar
    result = user_db.execute(
        """SELECT DISTINCT c.id, c.name
           FROM Courses c
           LEFT JOIN Payments p ON c.id = p.course_id AND p.user_id = ? AND p.status = 'approved'
           LEFT JOIN ManualAccess ma ON c.id = ma.course_id AND ma.user_id = ? 
               AND (ma.expires_at IS NULL OR ma.expires_at > datetime('now'))
           WHERE c.is_active = TRUE 
               AND (p.id IS NOT NULL OR ma.id IS NOT NULL)
           ORDER BY c.order_num""",
        parameters=(user_id, user_id),
        fetchall=True
    )

    if not result:
        text = """
📊 <b>Kurs progressi</b>

📭 Sizda hozircha kurslar yo'q.

Kurs sotib olish uchun "🛒 Kurs sotib olish" tugmasini bosing.
"""
        await call.message.edit_text(text, reply_markup=back_button("user:results"))
        await call.answer()
        return

    text = f"""
📊 <b>Kurs progressi</b>

{len(result)} ta kurs mavjud.

⬇️ Kursni tanlang:
"""

    # Har bir kurs uchun progress
    courses_with_progress = []
    for row in result:
        course_id = row[0]
        course_name = row[1]

        progress = user_db.get_user_course_progress(user_id, course_id)
        percentage = progress.get('percentage', 0) if progress else 0

        courses_with_progress.append({
            'id': course_id,
            'name': course_name,
            'percentage': percentage
        })

    await call.message.edit_text(
        text,
        reply_markup=course_progress_detail(courses_with_progress)
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="user:progress:")
async def show_course_progress(call: types.CallbackQuery):
    """Kurs progressini batafsil ko'rish"""
    course_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    # Progress ma'lumotlari
    progress = user_db.get_user_course_progress(user_id, course_id)

    # Modullar bo'yicha progress
    modules = user_db.get_course_modules(course_id, active_only=True)

    modules_text = ""
    for module in modules:
        lessons = user_db.get_module_lessons(module['id'], active_only=True)
        completed = 0

        for lesson in lessons:
            status = user_db.get_lesson_status(user_id, lesson['id'])
            if status == 'completed':
                completed += 1

        total = len(lessons)
        if total > 0:
            percent = (completed / total) * 100
            if percent == 100:
                icon = "✅"
            elif percent > 0:
                icon = "🔄"
            else:
                icon = "📁"

            modules_text += f"{icon} {module['name']}: {completed}/{total}\n"

    percentage = progress.get('percentage', 0) if progress else 0
    completed_lessons = progress.get('completed', 0) if progress else 0
    total_lessons = progress.get('total', 0) if progress else 0

    # Progress bar
    filled = int(percentage / 10)
    progress_bar = "▓" * filled + "░" * (10 - filled)

    text = f"""
📊 <b>Kurs progressi</b>

📚 {course['name']}

<b>Umumiy progress:</b>
[{progress_bar}] {percentage:.0f}%

📹 Darslar: {completed_lessons}/{total_lessons}

<b>Modullar bo'yicha:</b>
{modules_text}
"""

    # Kurs tugaganmi
    if percentage >= 100:
        text += "\n🎉 <b>Tabriklaymiz! Kurs tugallandi!</b>"

        # Sertifikat bormi tekshirish
        cert = user_db.execute(
            """SELECT id, grade FROM Certificates 
               WHERE user_id = ? AND course_id = ?""",
            parameters=(user_id, course_id),
            fetchone=True
        )

        if cert:
            grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜'}
            text += f"\n\n🎓 Sertifikat: {grade_icons.get(cert[1], '📜')} {cert[1]}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(row_width=1)

    if percentage >= 100:
        # Sertifikat olish
        keyboard.add(InlineKeyboardButton(
            "🎓 Sertifikat olish",
            callback_data=f"user:certificate:get:{course_id}"
        ))
    else:
        # Davom etish
        keyboard.add(InlineKeyboardButton(
            "▶️ Davom etish",
            callback_data=f"user:modules:{course_id}"
        ))

    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="user:my_progress"))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ============================================================
#                    TEST NATIJALARI
# ============================================================

@dp.callback_query_handler(text="user:test_results")
async def show_test_results(call: types.CallbackQuery):
    """Test natijalari ro'yxati"""
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # Barcha test natijalari
    results = user_db.execute(
        """SELECT tr.score, tr.correct_answers, tr.passed, tr.created_at,
                  l.name as lesson_name, c.name as course_name
           FROM TestResults tr
           JOIN Tests t ON tr.test_id = t.id
           JOIN Lessons l ON t.lesson_id = l.id
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE tr.user_id = ?
           ORDER BY tr.created_at DESC
           LIMIT 20""",
        parameters=(user_id,),
        fetchall=True
    )

    if not results:
        text = """
📝 <b>Test natijalari</b>

📭 Siz hali test topshirmagansiz.
"""
        await call.message.edit_text(text, reply_markup=back_button("user:results"))
        await call.answer()
        return

    text = f"""
📝 <b>Test natijalari</b>

📊 So'nggi {len(results)} ta natija:

"""

    for i, r in enumerate(results, 1):
        status = "✅" if r[2] else "❌"
        date = r[3][:10] if r[3] else ""
        text += f"{i}. {status} <b>{r[4]}</b>\n"
        text += f"   {r[0]:.0f}% | {date}\n\n"

    await call.message.edit_text(text, reply_markup=back_button("user:results"))
    await call.answer()


# ============================================================
#                    SERTIFIKATLAR
# ============================================================

@dp.callback_query_handler(text="user:certificates")
async def show_certificates(call: types.CallbackQuery):
    """Sertifikatlar ro'yxati"""
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # Sertifikatlar
    certs = user_db.execute(
        """SELECT cert.id, cert.certificate_code, cert.grade, cert.total_score,
                  cert.percentage, cert.created_at, c.name as course_name
           FROM Certificates cert
           JOIN Courses c ON cert.course_id = c.id
           WHERE cert.user_id = ?
           ORDER BY cert.created_at DESC""",
        parameters=(user_id,),
        fetchall=True
    )

    if not certs:
        text = """
🎓 <b>Sertifikatlar</b>

📭 Sizda hozircha sertifikatlar yo'q.

Sertifikat olish uchun kursni to'liq tugating.
"""
        await call.message.edit_text(text, reply_markup=back_button("user:results"))
        await call.answer()
        return

    grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜'}

    text = f"""
🎓 <b>Mening sertifikatlarim</b>

Jami: {len(certs)} ta sertifikat

"""

    certificates = []
    for cert in certs:
        icon = grade_icons.get(cert[2], '📜')
        text += f"{icon} <b>{cert[6]}</b>\n"
        text += f"   {cert[2]} | {cert[4]:.0f}%\n\n"

        certificates.append({
            'id': cert[0],
            'code': cert[1],
            'grade': cert[2],
            'course_name': cert[6]
        })

    await call.message.edit_text(text, reply_markup=certificates_list(certificates))
    await call.answer()


@dp.callback_query_handler(text_startswith="user:certificate:view:")
async def view_certificate(call: types.CallbackQuery):
    """Sertifikatni ko'rish"""
    cert_id = int(call.data.split(":")[-1])

    cert = user_db.execute(
        """SELECT cert.*, c.name as course_name
           FROM Certificates cert
           JOIN Courses c ON cert.course_id = c.id
           WHERE cert.id = ?""",
        parameters=(cert_id,),
        fetchone=True
    )

    if not cert:
        await call.answer("❌ Sertifikat topilmadi!", show_alert=True)
        return

    grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜'}
    grade_names = {'GOLD': 'Oltin', 'SILVER': 'Kumush', 'BRONZE': 'Bronza', 'PARTICIPANT': 'Ishtirokchi'}

    # cert tuple indekslari:
    # 0-id, 1-user_id, 2-course_id, 3-certificate_code, 4-certificate_file_id
    # 5-total_score, 6-percentage, 7-grade, 8-created_at, 9-course_name

    icon = grade_icons.get(cert[7], '📜')
    grade_name = grade_names.get(cert[7], 'Ishtirokchi')

    text = f"""
🎓 <b>Sertifikat</b>

{icon} <b>{cert[9]}</b>

📊 <b>Ma'lumotlar:</b>
├ 🏅 Daraja: {grade_name}
├ 📈 Ball: {cert[5]}
├ 📊 Foiz: {cert[6]:.0f}%
├ 🔢 Kod: <code>{cert[3]}</code>
└ 📅 Sana: {cert[8][:10] if cert[8] else 'Noma`lum'}

"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(row_width=1)

    # Agar fayl bo'lsa
    if cert[4]:
        keyboard.add(InlineKeyboardButton(
            "📥 Yuklab olish",
            callback_data=f"user:certificate:download:{cert_id}"
        ))

    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="user:certificates"))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text_startswith="user:certificate:download:")
async def download_certificate(call: types.CallbackQuery):
    """Sertifikatni yuklab olish"""
    cert_id = int(call.data.split(":")[-1])

    cert = user_db.execute(
        """SELECT certificate_file_id, certificate_code FROM Certificates WHERE id = ?""",
        parameters=(cert_id,),
        fetchone=True
    )

    if not cert or not cert[0]:
        await call.answer("❌ Sertifikat fayli mavjud emas!", show_alert=True)
        return

    await call.answer("📥 Sertifikat yuborilmoqda...")

    try:
        await bot.send_document(
            call.from_user.id,
            cert[0],
            caption=f"🎓 Sertifikat\n🔢 Kod: {cert[1]}"
        )
    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")


@dp.callback_query_handler(text_startswith="user:certificate:get:")
async def get_certificate(call: types.CallbackQuery):
    """Sertifikat olish"""
    course_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # Allaqachon sertifikat bormi
    existing = user_db.execute(
        """SELECT id FROM Certificates WHERE user_id = ? AND course_id = ?""",
        parameters=(user_id, course_id),
        fetchone=True
    )

    if existing:
        await call.answer("✅ Sertifikat allaqachon mavjud!", show_alert=True)
        call.data = f"user:certificate:view:{existing[0]}"
        await view_certificate(call)
        return

    # Kurs tugallanganmi tekshirish
    progress = user_db.get_user_course_progress(user_id, course_id)

    if not progress or progress.get('percentage', 0) < 100:
        await call.answer("❌ Avval kursni to'liq tugating!", show_alert=True)
        return

    # Sertifikat yaratish
    user = user_db.get_user(telegram_id)

    # Ball va daraja hisoblash
    total_score = user.get('total_score', 0)

    # Test natijalari bo'yicha foiz
    test_results = user_db.execute(
        """SELECT AVG(tr.score) FROM TestResults tr
           JOIN Tests t ON tr.test_id = t.id
           JOIN Lessons l ON t.lesson_id = l.id
           JOIN Modules m ON l.module_id = m.id
           WHERE tr.user_id = ? AND m.course_id = ? AND tr.passed = 1""",
        parameters=(user_id, course_id),
        fetchone=True
    )

    avg_score = test_results[0] if test_results and test_results[0] else 70

    # Daraja aniqlash
    gold_threshold = int(user_db.get_setting('gold_threshold') or 90)
    silver_threshold = int(user_db.get_setting('silver_threshold') or 75)
    bronze_threshold = int(user_db.get_setting('bronze_threshold') or 60)

    if avg_score >= gold_threshold:
        grade = 'GOLD'
    elif avg_score >= silver_threshold:
        grade = 'SILVER'
    elif avg_score >= bronze_threshold:
        grade = 'BRONZE'
    else:
        grade = 'PARTICIPANT'

    # Sertifikat yaratish
    cert_id = user_db.generate_certificate(
        user_id=user_id,
        course_id=course_id,
        total_score=total_score,
        percentage=avg_score,
        grade=grade
    )

    if cert_id:
        grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜'}
        icon = grade_icons.get(grade, '📜')

        await call.answer(f"🎉 Sertifikat yaratildi! {icon}", show_alert=True)

        call.data = f"user:certificate:view:{cert_id}"
        await view_certificate(call)
    else:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)