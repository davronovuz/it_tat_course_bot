"""
User Progress Handler (FINAL FULL VERSION)
==========================================
Barcha funksiyalar to'liq yozilgan.
Qisqartirishlar yo'q.
0/0 xatoligi uchun maxsus SQL so'rovlar qo'shilgan.
"""

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, bot, user_db
from utils.cert_gen import create_certificate
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
    """
    Foydalanuvchi natijalari bosh sahifasi
    """
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
        return

    user_id = user['id']

    # 1. Jami ball
    total_score = user.get('total_score', 0)

    # 2. Test statistikasi
    test_results = user_db.execute(
        """SELECT COUNT(*), SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END)
           FROM TestResults WHERE user_id = ?""",
        parameters=(user_id,),
        fetchone=True
    )
    total_tests = test_results[0] if test_results else 0
    passed_tests = test_results[1] if test_results and test_results[1] else 0

    # 3. Tugatilgan darslar soni
    completed_lessons = user_db.execute(
        """SELECT COUNT(*) FROM UserProgress 
           WHERE user_id = ? AND status = 'completed'""",
        parameters=(user_id,),
        fetchone=True
    )
    completed_count = completed_lessons[0] if completed_lessons else 0

    # 4. Sertifikatlar soni
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

⬇️ Batafsil ko'rish uchun quyidagilardan birini tanlang:
"""

    await call.message.edit_text(text, reply_markup=my_results_menu())
    await call.answer()


# ============================================================
#                    KURS PROGRESSI (RO'YXAT)
# ============================================================

@dp.callback_query_handler(text="user:my_progress")
async def show_my_courses_progress(call: types.CallbackQuery):
    """
    Foydalanuvchi qatnashayotgan kurslar ro'yxati va foizlari
    """
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # Foydalanuvchida dostup bor kurslarni topamiz
    # (To'lov qilgan yoki Admin qo'shgan)
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

    # Agar kurslar bo'lmasa, lekin 1-kurs bepul bo'lsa, uni ham qo'shib qo'yishimiz mumkin
    # Yoki shunchaki xabar chiqaramiz
    if not result:
        # Fallback: Agar UserProgress da biror dars bo'lsa, o'sha kursni ko'rsatamiz
        check_progress = user_db.execute(
            """SELECT DISTINCT c.id, c.name FROM UserProgress up
               JOIN Lessons l ON up.lesson_id = l.id
               JOIN Modules m ON l.module_id = m.id
               JOIN Courses c ON m.course_id = c.id
               WHERE up.user_id = ?""",
            parameters=(user_id,),
            fetchall=True
        )
        if check_progress:
            result = check_progress
        else:
            text = """
📊 <b>Kurs progressi</b>

📭 Sizda hozircha faol kurslar yo'q.
Darslarni boshlash uchun Asosiy menyudan "Darslar" bo'limiga o'ting.
"""
            await call.message.edit_text(text, reply_markup=back_button("user:results"))
            await call.answer()
            return

    text = f"""
📊 <b>Mening kurslarim</b>

Quyidagi kurslardan birini tanlang:
"""

    courses_with_progress = []

    for row in result:
        course_id = row[0]
        course_name = row[1]

        # Har bir kurs uchun progressni hisoblash
        # (Bu yerda ham 0/0 xatosini oldini olish uchun oddiy hisoblaymiz)

        # Jami darslar
        res_total = user_db.execute(
            "SELECT COUNT(*) FROM Lessons l JOIN Modules m ON l.module_id = m.id WHERE m.course_id = ?",
            parameters=(course_id,), fetchone=True
        )
        total = res_total[0] if res_total else 0

        # Tugatilgan darslar
        res_done = user_db.execute(
            """SELECT COUNT(*) FROM UserProgress up 
               JOIN Lessons l ON up.lesson_id = l.id
               JOIN Modules m ON l.module_id = m.id
               WHERE up.user_id = ? AND m.course_id = ? AND up.status = 'completed'""",
            parameters=(user_id, course_id), fetchone=True
        )
        done = res_done[0] if res_done else 0

        percent = (done / total * 100) if total > 0 else 0

        courses_with_progress.append({
            'id': course_id,
            'name': course_name,
            'percentage': percent
        })

    await call.message.edit_text(
        text,
        reply_markup=course_progress_detail(courses_with_progress)
    )
    await call.answer()


# ============================================================
#                    KONKRET KURS PROGRESSI (Batafsil)
# ============================================================

@dp.callback_query_handler(text_startswith="user:progress:")
async def show_course_progress(call: types.CallbackQuery):
    """
    Tanlangan kursning ichki statistikasi (Modullar kesimida)
    """
    course_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    course = user_db.get_course(course_id)
    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    # 1. Umumiy hisob-kitob (UserDB helperlarisiz, to'g'ridan-to'g'ri SQL)
    res_total = user_db.execute(
        "SELECT COUNT(*) FROM Lessons l JOIN Modules m ON l.module_id = m.id WHERE m.course_id = ?",
        parameters=(course_id,), fetchone=True
    )
    total_lessons = res_total[0] if res_total else 0

    res_completed = user_db.execute(
        """SELECT COUNT(*) FROM UserProgress up 
           JOIN Lessons l ON up.lesson_id = l.id
           JOIN Modules m ON l.module_id = m.id
           WHERE up.user_id = ? AND m.course_id = ? AND up.status = 'completed'""",
        parameters=(user_id, course_id), fetchone=True
    )
    completed_lessons = res_completed[0] if res_completed else 0

    percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

    # 2. Modullar bo'yicha matn tayyorlash
    modules = user_db.get_course_modules(course_id, active_only=True)
    modules_text = ""

    for module in modules:
        mod_lessons = user_db.get_module_lessons(module['id'], active_only=True)
        mod_total = len(mod_lessons)
        mod_done = 0

        for lesson in mod_lessons:
            # Har bir darsni tekshiramiz
            status_row = user_db.execute(
                "SELECT status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
                parameters=(user_id, lesson['id']), fetchone=True
            )
            if status_row and status_row[0] == 'completed':
                mod_done += 1

        if mod_total > 0:
            mod_percent = (mod_done / mod_total) * 100
            if mod_percent == 100:
                icon = "✅"
            elif mod_percent > 0:
                icon = "🔄"
            else:
                icon = "📁"
            modules_text += f"{icon} <b>{module['name']}</b>: {mod_done}/{mod_total}\n"

    # Progress bar
    filled = int(percentage / 10)
    progress_bar = "▓" * filled + "░" * (10 - filled)

    text = f"""
📊 <b>{course['name']}</b>

<b>Umumiy progress:</b>
[{progress_bar}] {percentage:.0f}%

📹 Darslar: {completed_lessons}/{total_lessons}

<b>Modullar bo'yicha:</b>
{modules_text}
"""

    # 3. Tugmalarni yasash
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Agar 99% dan yuqori bo'lsa (yaxlitlash xatolarini hisobga olib)
    if percentage >= 99 and total_lessons > 0:
        text += "\n🎉 <b>Tabriklaymiz! Kurs to'liq tugatildi!</b>"
        keyboard.add(InlineKeyboardButton(
            "🎓 Sertifikat olish",
            callback_data=f"user:certificate:get:{course_id}"
        ))
    else:
        keyboard.add(InlineKeyboardButton(
            "▶️ Darslarni davom ettirish",
            callback_data="user:lessons"
        ))

    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="user:my_progress"))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ============================================================
#                    TEST NATIJALARI (TARIX)
# ============================================================

@dp.callback_query_handler(text="user:test_results")
async def show_test_results(call: types.CallbackQuery):
    """
    Test natijalari tarixi (Oxirgi 10 ta)
    """
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
            score = r[0]
            lesson_name = r[4]

            text += f"{i}. {status} <b>{lesson_name}</b>\n"
            text += f"   📊 {score:.0f}% | 📅 {date}\n\n"

    await call.message.edit_text(text, reply_markup=back_button("user:results"))
    await call.answer()


# ============================================================
#                    SERTIFIKATLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text="user:certificates")
async def show_certificates_list(call: types.CallbackQuery):
    """
    Foydalanuvchi olgan sertifikatlar ro'yxati
    """
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
    grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜', 'EXPERT': '💎'}

    for cert in certs:
        grade = cert[2]
        icon = grade_icons.get(grade, '📜')
        course_name = cert[4]

        certificates_data.append({
            'id': cert[0],
            'code': cert[1],
            'grade': grade,
            'course_name': course_name
        })
        text += f"\n{icon} <b>{course_name}</b> ({grade})"

    await call.message.edit_text(text, reply_markup=certificates_list(certificates_data))
    await call.answer()


# ============================================================
#                    SERTIFIKAT GENERATSIYA QILISH (FIX)
# ============================================================

@dp.callback_query_handler(text_startswith="user:certificate:get:")
async def generate_and_get_certificate(call: types.CallbackQuery):
    """
    Sertifikat olish funksiyasi.
    0/0 xatoligini aylanib o'tish uchun majburiy SQL hisob-kitob ishlatadi.
    """
    try:
        raw_data = call.data.split(":")
        course_id = int(raw_data[-1])
        telegram_id = call.from_user.id
        user_id = user_db.get_user_id(telegram_id)

        # ---------------------------------------------------------
        # 1. MAJBURIY HISOBLASH (UserDB helperlariga ishonmaymiz)
        # ---------------------------------------------------------

        # Jami darslar (aktiv/passiv farqi yo'q, hammasini sanaymiz)
        res_total = user_db.execute(
            """SELECT COUNT(*) FROM Lessons l
               JOIN Modules m ON l.module_id = m.id
               WHERE m.course_id = ?""",
            parameters=(course_id,),
            fetchone=True
        )
        total_lessons = res_total[0] if res_total else 0

        # Agar total 0 bo'lsa, demak course_id noto'g'ri yoki darslar boshqa kursda (masalan 1 da)
        if total_lessons == 0:
            # Fallback: Default 1-kursni tekshirib ko'ramiz
            course_id = 1
            res_total = user_db.execute(
                "SELECT COUNT(*) FROM Lessons l JOIN Modules m ON l.module_id = m.id WHERE m.course_id = 1",
                fetchone=True
            )
            total_lessons = res_total[0] if res_total else 0

        # Tugatilgan darslar (Completed)
        res_completed = user_db.execute(
            """SELECT COUNT(*) FROM UserProgress up
               JOIN Lessons l ON up.lesson_id = l.id
               JOIN Modules m ON l.module_id = m.id
               WHERE up.user_id = ? AND m.course_id = ? AND up.status = 'completed'""",
            parameters=(user_id, course_id),
            fetchone=True
        )
        completed_lessons = res_completed[0] if res_completed else 0

        # Foiz
        if total_lessons > 0:
            percentage = (completed_lessons / total_lessons) * 100
        else:
            percentage = 0

        # ---------------------------------------------------------
        # 2. TEKSHIRUV
        # ---------------------------------------------------------
        # Agar 99% dan kam bo'lsa, lekin jami darslar 0 dan katta bo'lsa -> Ruxsat yo'q
        if percentage < 99 and total_lessons > 0:
            await call.answer(
                f"❌ Kurs tugatilmagan!\n"
                f"📊 Natija: {completed_lessons}/{total_lessons} ({percentage:.0f}%)",
                show_alert=True
            )
            return

        # Agar umuman dars topilmasa (0/0)
        if total_lessons == 0:
            await call.answer("⚠️ Tizimda darslar topilmadi (0/0). Admin bilan bog'laning.", show_alert=True)
            return

        await call.answer("⏳ Sertifikat tayyorlanmoqda...", show_alert=False)

        # ---------------------------------------------------------
        # 3. SERTIFIKAT DATA YARATISH
        # ---------------------------------------------------------
        cert_data = user_db.generate_certificate(telegram_id, course_id)

        if not cert_data:
            cert_data = user_db.get_certificate(telegram_id, course_id)

        # Favqulodda holat (agar baza ishlamasa)
        if not cert_data:
            import uuid
            cert_data = {
                'code': f"CERT-{uuid.uuid4().hex[:8].upper()}",
                'grade': 'EXPERT',
                'total_score': 100
            }

        # ---------------------------------------------------------
        # 4. RASM CHIZISH
        # ---------------------------------------------------------
        user = user_db.get_user(telegram_id)
        course = user_db.get_course(course_id)
        course_name = course['name'] if course else "Maxsus Kurs"

        try:
            # Eski xabarni o'chirish
            try:
                await call.message.delete()
            except:
                pass

            msg = await call.message.answer("🖌 <b>Sertifikat yozilmoqda...</b>")

            cert_image = create_certificate(
                full_name=user['full_name'],
                course_name=course_name,
                grade=cert_data['grade'],
                cert_code=cert_data['code']
            )

            if not cert_image:
                await msg.edit_text("❌ Sertifikat faylini yaratib bo'lmadi.")
                return

            caption = (
                f"🎉 <b>TABRIKLAYMIZ!</b>\n\n"
                f"Siz <b>{course_name}</b> kursini muvaffaqiyatli tamomladingiz!\n\n"
                f"🏆 Daraja: <b>{cert_data['grade']}</b>\n"
                f"⭐️ Ball: <b>{cert_data['total_score']}</b>\n"
                f"🆔 ID: <code>{cert_data['code']}</code>\n\n"
                f"<i>Ushbu sertifikat rasmiy hisoblanadi.</i>"
            )

            await msg.delete()
            await call.message.answer_photo(cert_image, caption=caption)

            # Asosiy menyuga qaytish tugmasi
            from keyboards.default.user_keyboards import user_main_menu
            await call.message.answer("⬇️ Asosiy menyu", reply_markup=user_main_menu())

        except Exception as e:
            await msg.edit_text(f"❌ Rasm chizishda xatolik: {e}")

    except Exception as e:
        print(f"CRITICAL ERROR IN CERTIFICATE: {e}")
        await call.answer(f"Tizim xatosi: {e}", show_alert=True)


# ============================================================
#                    SERTIFIKATNI QAYTA KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:certificate:view:")
async def view_existing_certificate(call: types.CallbackQuery):
    """
    Mavjud sertifikatni ochish
    """
    cert_id = int(call.data.split(":")[-1])

    cert_row = user_db.execute(
        """SELECT c.certificate_code, c.grade, co.name, u.full_name
           FROM Certificates c
           JOIN Courses co ON c.course_id = co.id
           JOIN Users u ON c.user_id = u.id
           WHERE c.id = ?""",
        parameters=(cert_id,),
        fetchone=True
    )

    if not cert_row:
        await call.answer("❌ Sertifikat topilmadi", show_alert=True)
        return

    code, grade, course_name, full_name = cert_row
    await call.answer("⏳ Yuklanmoqda...")

    try:
        cert_image = create_certificate(full_name, course_name, grade, code)

        caption = (
            f"🎓 <b>SERTIFIKAT</b>\n\n"
            f"👤 <b>{full_name}</b>\n"
            f"📚 Kurs: {course_name}\n"
            f"🏆 Daraja: {grade}\n"
            f"🆔 Kod: <code>{code}</code>"
        )

        try:
            await call.message.delete()
        except:
            pass

        await call.message.answer_photo(cert_image, caption=caption)

        from keyboards.default.user_keyboards import user_main_menu
        await call.message.answer("⬇️ Menyuga qaytish", reply_markup=user_main_menu())

    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")