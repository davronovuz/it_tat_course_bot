"""
User Progress Handler (YANGILANGAN)
===================================
Natijalar, kurs progressi va sertifikat olish tizimi.
Endi avtomatik rasm chizish tizimi (Pillow) bilan ulangan.
"""

from aiogram import types
from loader import dp, bot, user_db
from utils.cart_gen import create_certificate
from keyboards.inline.user_keyboards import (
    my_results_menu,
    course_progress_detail,
    certificates_list,
    back_button
)


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

    # Userdagi total_score ni olamiz
    total_score = user.get('total_score', 0)

    # Test natijalari statistikasi
    test_results = user_db.execute(
        """SELECT COUNT(*), SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END)
           FROM TestResults WHERE user_id = ?""",
        parameters=(user_id,),
        fetchone=True
    )
    total_tests = test_results[0] if test_results else 0
    passed_tests = test_results[1] if test_results and test_results[1] else 0

    # Tugatilgan darslar soni
    completed_lessons = user_db.execute(
        """SELECT COUNT(*) FROM UserProgress 
           WHERE user_id = ? AND status = 'completed'""",
        parameters=(user_id,),
        fetchone=True
    )
    completed_count = completed_lessons[0] if completed_lessons else 0

    # Sertifikatlar soni
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

    # Dostup bor kurslarni topish
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

📭 Sizda hozircha faol kurslar yo'q.
Kurs sotib olish uchun asosiy menyudan foydalaning.
"""
        await call.message.edit_text(text, reply_markup=back_button("user:results"))
        await call.answer()
        return

    text = f"""
📊 <b>Mening kurslarim</b>

Quyidagi kurslardan birini tanlang:
"""

    # Har bir kurs uchun progressni hisoblash
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
            icon = "✅" if percent == 100 else ("🔄" if percent > 0 else "📁")
            modules_text += f"{icon} {module['name']}: {completed}/{total}\n"

    percentage = progress.get('percentage', 0)
    completed_lessons = progress.get('completed', 0)
    total_lessons = progress.get('total', 0)

    # Progress bar chizish
    filled = int(percentage / 10)
    progress_bar = "▓" * filled + "░" * (10 - filled)

    text = f"""
📊 <b>{course['name']}</b>

<b>Umumiy progress:</b>
[{progress_bar}] {percentage:.0f}%

📹 Darslar: {completed_lessons}/{total_lessons}

<b>Modullar:</b>
{modules_text}
"""

    # Tugmalar
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Agar 100% bo'lsa -> Sertifikat olish
    if percentage >= 100:
        text += "\n🎉 <b>Tabriklaymiz! Kurs to'liq tugatildi!</b>"
        keyboard.add(InlineKeyboardButton(
            "🎓 Sertifikat olish",
            callback_data=f"user:certificate:get:{course_id}"
        ))
    else:
        # Davom etish
        keyboard.add(InlineKeyboardButton(
            "▶️ Darslarni davom ettirish",
            callback_data=f"user:lessons"  # Yoki darslar ro'yxatiga qaytish
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

    results = user_db.execute(
        """SELECT tr.score, tr.correct_answers, tr.passed, tr.created_at,
                  l.name as lesson_name
           FROM TestResults tr
           JOIN Tests t ON tr.test_id = t.id
           JOIN Lessons l ON t.lesson_id = l.id
           WHERE tr.user_id = ?
           ORDER BY tr.created_at DESC
           LIMIT 10""",
        parameters=(user_id,),
        fetchall=True
    )

    if not results:
        text = """
📝 <b>Test natijalari</b>

📭 Siz hali test yechmagansiz.
"""
    else:
        text = f"📝 <b>Test natijalari (Oxirgi 10 ta):</b>\n\n"
        for i, r in enumerate(results, 1):
            status = "✅" if r[2] else "❌"
            date = r[3][:10] if r[3] else ""
            text += f"{i}. {status} <b>{r[4]}</b>\n"
            text += f"   📊 {r[0]:.0f}% | 📅 {date}\n\n"

    await call.message.edit_text(text, reply_markup=back_button("user:results"))
    await call.answer()


# ============================================================
#                    SERTIFIKATLAR
# ============================================================

@dp.callback_query_handler(text="user:certificates")
async def show_certificates_list(call: types.CallbackQuery):
    """Sertifikatlar ro'yxati"""
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    certs = user_db.execute(
        """SELECT cert.id, cert.certificate_code, cert.grade, cert.percentage, 
                  c.name as course_name
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

📭 Sizda hozircha sertifikat yo'q.
Sertifikat olish uchun kursni 100% tugatishingiz kerak.
"""
        await call.message.edit_text(text, reply_markup=back_button("user:results"))
        await call.answer()
        return

    text = f"🎓 <b>Mening sertifikatlarim:</b>\nJami: {len(certs)} ta\n"

    certificates_data = []
    grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜'}

    for cert in certs:
        icon = grade_icons.get(cert[2], '📜')
        certificates_data.append({
            'id': cert[0],
            'code': cert[1],
            'grade': cert[2],
            'course_name': cert[4]
        })
        text += f"\n{icon} <b>{cert[4]}</b> ({cert[2]})"

    await call.message.edit_text(text, reply_markup=certificates_list(certificates_data))
    await call.answer()


# ============================================================
#                    SERTIFIKAT OLISH VA KORISH (MUHIM)
# ============================================================

@dp.callback_query_handler(text_startswith="user:certificate:get:")
async def generate_and_get_certificate(call: types.CallbackQuery):
    """
    Sertifikatni generatsiya qilish va yuborish
    """
    course_id = int(call.data.split(":")[-1])
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # 1. Progressni qayta tekshirish (Xavfsizlik uchun)
    progress = user_db.get_user_course_progress(user_id, course_id)
    if progress['percentage'] < 100:
        await call.answer("❌ Kurs hali 100% tugatilmagan!", show_alert=True)
        return

    await call.answer("⏳ Sertifikat tayyorlanmoqda...", show_alert=False)

    # 2. Bazada yaratish (yoki borini olish)
    # generate_certificate DICTIONARY qaytaradi: {'code':..., 'grade':..., 'total_score':...}
    cert_data = user_db.generate_certificate(telegram_id, course_id)

    if not cert_data:
        # Agar oldin yaratilgan bo'lsa, get_certificate orqali olamiz
        cert_data = user_db.get_certificate(telegram_id, course_id)

    if not cert_data:
        await call.message.answer("❌ Sertifikat ma'lumotlarini olishda xatolik!")
        return

    # 3. User ma'lumotlari
    user = user_db.get_user(telegram_id)
    course = user_db.get_course(course_id)

    # 4. Rasmni chizish (Pillow orqali)
    try:
        # Eski xabarni o'chirishga harakat qilamiz
        try:
            await call.message.delete()
        except:
            pass

        msg = await call.message.answer("🖌 <b>Sertifikat yozilmoqda...</b>")

        # Rasm yaratish (BytesIO obyekti qaytadi)
        cert_image = create_certificate(
            full_name=user['full_name'],
            course_name=course['name'],
            grade=cert_data['grade'],
            cert_code=cert_data['code']
        )

        if not cert_image:
            await msg.edit_text("❌ Shablon topilmadi! Admin bilan bog'laning.")
            return

        # 5. Rasmni yuborish
        caption = (
            f"🎉 <b>TABRIKLAYMIZ!</b>\n\n"
            f"Siz <b>{course['name']}</b> kursini muvaffaqiyatli tamomladingiz!\n\n"
            f"🏆 Daraja: <b>{cert_data['grade']}</b>\n"
            f"⭐️ Ball: <b>{cert_data['total_score']}</b>\n"
            f"🆔 ID: <code>{cert_data['code']}</code>\n\n"
            f"<i>Ushbu sertifikat rasmiy hisoblanadi.</i>"
        )

        await msg.delete()
        await call.message.answer_photo(cert_image, caption=caption)

    except Exception as e:
        await call.message.answer(f"❌ Xatolik yuz berdi: {e}")


@dp.callback_query_handler(text_startswith="user:certificate:view:")
async def view_existing_certificate(call: types.CallbackQuery):
    """
    Ro'yxatdan tanlangan sertifikatni qayta ko'rsatish
    """
    cert_id = int(call.data.split(":")[-1])

    # Bazadan ma'lumotlarni olamiz
    cert_row = user_db.execute(
        """SELECT c.certificate_code, c.grade, c.total_score, 
                  co.id, co.name, u.full_name
           FROM Certificates c
           JOIN Courses co ON c.course_id = co.id
           JOIN Users u ON c.user_id = u.id
           WHERE c.id = ?""",
        parameters=(cert_id,),
        fetchone=True
    )

    if not cert_row:
        await call.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return

    code, grade, score, course_id, course_name, full_name = cert_row

    await call.answer("⏳ Yuklanmoqda...")

    # Rasmni qayta generatsiya qilamiz (xotiradan joy olmasligi uchun saqlamasdan)
    try:
        cert_image = create_certificate(
            full_name=full_name,
            course_name=course_name,
            grade=grade,
            cert_code=code
        )

        caption = (
            f"🎓 <b>SERTIFIKAT</b>\n\n"
            f"👤 <b>{full_name}</b>\n"
            f"📚 Kurs: {course_name}\n"
            f"🏆 Daraja: {grade}\n"
            f"🆔 Kod: <code>{code}</code>"
        )

        # Eski menyuni o'chiramiz
        try:
            await call.message.delete()
        except:
            pass

        await call.message.answer_photo(cert_image, caption=caption)

        # Yana menyuni chiqarish
        from keyboards.default.user_keyboards import user_main_menu
        await call.message.answer("⬇️ Asosiy menyu", reply_markup=user_main_menu())

    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")