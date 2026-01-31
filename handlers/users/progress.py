"""
User Progress Handler (FINAL COMPLETE VERSION)
==============================================
Bu fayl sertifikat olish jarayonini to'liq boshqaradi:
1. Progressni tekshiradi (0/0 xatosiz).
2. Ismni tasdiqlatadi.
3. Ismni o'zgartirishga ruxsat beradi.
4. Sertifikat yaratadi va Userga yuboradi.
5. Adminlarga hisobot yuboradi.
6. Barcha natijalar menyularini chiqaradi.
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import dp, bot, user_db
from utils.cert_gen import create_certificate
from data.config import ADMINS
from states.user_states import CertificateStates
from keyboards.default.user_keyboards import user_main_menu
from keyboards.inline.user_keyboards import (
    my_results_menu,
    course_progress_detail,
    certificates_list,
    back_button,
    confirm_name_keyboard  # Yangi qo'shilgan tugma
)


# ============================================================
# 1. NATIJALAR MENYUSI (BOSH SAHIFA)
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
# 2. KURS PROGRESSI (RO'YXAT)
# ============================================================
@dp.callback_query_handler(text="user:my_progress")
async def show_my_courses_progress(call: types.CallbackQuery):
    """
    Foydalanuvchi qatnashayotgan kurslar ro'yxati
    """
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    # Kurslarni olish
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
        # Fallback: Agar UserProgress da biror dars bo'lsa
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

    await call.message.edit_text(text, reply_markup=course_progress_detail(courses_with_progress))
    await call.answer()


# ============================================================
# 3. KONKRET KURS PROGRESSI (BATAFSIL)
# ============================================================
@dp.callback_query_handler(text_startswith="user:progress:")
async def show_course_progress(call: types.CallbackQuery):
    course_id = int(call.data.split(":")[-1])
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    course = user_db.get_course(course_id)
    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    # Umumiy hisob
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

    # Modullar matni
    modules = user_db.get_course_modules(course_id, active_only=True)
    modules_text = ""

    for module in modules:
        mod_lessons = user_db.get_module_lessons(module['id'], active_only=True)
        mod_total = len(mod_lessons)
        mod_done = 0
        for lesson in mod_lessons:
            status_row = user_db.execute(
                "SELECT status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
                parameters=(user_id, lesson['id']), fetchone=True
            )
            if status_row and status_row[0] == 'completed':
                mod_done += 1

        if mod_total > 0:
            modules_text += f"✅ <b>{module['name']}</b>: {mod_done}/{mod_total}\n"

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
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Agar 99% dan yuqori bo'lsa -> Sertifikat olish
    if percentage >= 99 and total_lessons > 0:
        text += "\n🎉 <b>Tabriklaymiz! Kurs to'liq tugatildi!</b>"
        keyboard.add(InlineKeyboardButton(
            "🎓 Sertifikat olish",
            callback_data=f"user:certificate:get:{course_id}"
        ))
    else:
        keyboard.add(InlineKeyboardButton("▶️ Darslarni davom ettirish", callback_data="user:lessons"))

    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="user:my_progress"))
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ============================================================
# 4. TEST NATIJALARI (TARIX)
# ============================================================
@dp.callback_query_handler(text="user:test_results")
async def show_test_results(call: types.CallbackQuery):
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
        text = "📝 <b>Test natijalari</b>\n\n📭 Siz hali test yechmagansiz."
    else:
        text = f"📝 <b>Test natijalari (Oxirgi 10 ta):</b>\n\n"
        for i, r in enumerate(results, 1):
            status = "✅" if r[2] else "❌"
            date = r[3][:10] if r[3] else ""
            text += f"{i}. {status} <b>{r[4]}</b>\n   📊 {r[0]:.0f}% | 📅 {date}\n\n"

    await call.message.edit_text(text, reply_markup=back_button("user:results"))
    await call.answer()


# ============================================================
# 5. SERTIFIKATLAR RO'YXATI
# ============================================================
@dp.callback_query_handler(text="user:certificates")
async def show_certificates_list(call: types.CallbackQuery):
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
        text = "🎓 <b>Sertifikatlar</b>\n\n📭 Sizda hozircha sertifikat yo'q."
        await call.message.edit_text(text, reply_markup=back_button("user:results"))
        return

    text = f"🎓 <b>Mening sertifikatlarim:</b>\nJami: {len(certs)} ta\n"
    certificates_data = []
    grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜', 'EXPERT': '💎'}

    for cert in certs:
        grade = cert[2]
        icon = grade_icons.get(grade, '📜')
        certificates_data.append({
            'id': cert[0], 'code': cert[1], 'grade': grade, 'course_name': cert[4]
        })
        text += f"\n{icon} <b>{cert[4]}</b> ({grade})"

    await call.message.edit_text(text, reply_markup=certificates_list(certificates_data))
    await call.answer()


# ============================================================
# 6. SERTIFIKAT OLISH JARAYONI (1-QADAM: TEKSHIRISH VA SO'RASH)
# ============================================================
@dp.callback_query_handler(text_startswith="user:certificate:get:")
async def check_and_ask_name(call: types.CallbackQuery):
    try:
        parts = call.data.split(":")
        course_id = int(parts[-1])
        telegram_id = call.from_user.id
        user_id = user_db.get_user_id(telegram_id)

        # 1. Agar oldin olgan bo'lsa -> Darhol beramiz
        existing = user_db.get_certificate(telegram_id, course_id)
        if existing:
            await generate_and_send_final(call, telegram_id, course_id, existing)
            return

        # 2. PROGRESSNI HISOBLASH
        # ----------------------------------------------------
        # Jami darslar soni (faqat aktiv darslar)
        res_total = user_db.execute(
            "SELECT COUNT(*) FROM Lessons l JOIN Modules m ON l.module_id = m.id WHERE m.course_id = ? AND l.is_active = 1",
            parameters=(course_id,), fetchone=True
        )
        total = res_total[0] if res_total else 0

        # Agar darslar soni 0 bo'lsa (xatolik bo'lmasligi uchun default 1 ga o'tamiz)
        if total == 0:
            course_id = 1
            res_total = user_db.execute(
                "SELECT COUNT(*) FROM Lessons l JOIN Modules m ON l.module_id = m.id WHERE m.course_id = 1",
                fetchone=True)
            total = res_total[0] if res_total else 0

        # Tugatilgan darslar soni
        res_done = user_db.execute(
            """SELECT COUNT(*) FROM UserProgress up 
               JOIN Lessons l ON up.lesson_id = l.id
               JOIN Modules m ON l.module_id = m.id
               WHERE up.user_id = ? AND m.course_id = ? AND up.status = 'completed'""",
            parameters=(user_id, course_id), fetchone=True
        )
        done = res_done[0] if res_done else 0

        # Foizni hisoblash
        percent = (done / total * 100) if total > 0 else 0

        # --- 🔥 MUAMMONI HAL QILADIGAN QISM ---

        is_ready = False
        missed_details = []

        # A) Agar 98% dan yuqori bo'lsa -> So'zsiz ruxsat beramiz
        if percent >= 98:
            is_ready = True

        # B) Agar foiz kam bo'lsa ham (masalan 92%), TESTLARDAN O'TGANINI tekshiramiz
        else:
            all_tests_passed = True
            # Kursdagi barcha darslarni olamiz
            lessons = user_db.get_course_lessons(course_id)
            test_found = False

            for lesson in lessons:
                if lesson['has_test']:
                    test_found = True
                    test = user_db.get_test_by_lesson(lesson['id'])
                    # Agar test bor va user o'tmagan bo'lsa
                    if test and not user_db.has_passed_test(telegram_id, test['id']):
                        all_tests_passed = False
                        # Nima qolib ketganini ro'yxatga yozamiz
                        missed_details.append(f"📝 {lesson['name']}")

            # Agar kursda testlar bor bo'lsa va hammasidan o'tgan bo'lsa -> TAYYOR!
            if test_found and all_tests_passed:
                is_ready = True
            # Agar kursda umuman test yo'q bo'lsa, demak videolarni ko'rmagan
            elif not test_found:
                is_ready = False
                missed_details.append("Videolarni oxirigacha ko'rmagansiz")
            else:
                is_ready = False

        # 3. NATIJA: Agar tayyor bo'lmasa -> Xatolik chiqaradi
        if not is_ready:
            msg = f"❌ <b>Kurs to'liq tugatilmagan! ({percent:.0f}%)</b>\n\n"

            if missed_details:
                msg += "Siz quyidagi testlarni topshirmagansiz:\n"
                msg += "\n".join(missed_details[:3])  # Faqat 3 tasini ko'rsatamiz
                if len(missed_details) > 3: msg += "\n..."
            else:
                msg += "Iltimos, barcha darslarni ko'rib chiqing."

            await call.answer("Tugatmagansiz", show_alert=False)
            await call.message.answer(msg)
            return

        # 4. TAYYOR BO'LSA -> ISMNI TASDIQLASHGA O'TAMIZ
        user = user_db.get_user(telegram_id)
        full_name = user['full_name']

        text = f"""
🎓 <b>Sertifikat ma'lumotlarini tasdiqlang</b>

Sertifikatga quyidagi ism-familiya yoziladi:
👤 <b>{full_name}</b>

<i>Agar ismingiz xato bo'lsa, "✏️ Ismni o'zgartirish" tugmasini bosing.</i>
"""
        await call.message.edit_text(text, reply_markup=confirm_name_keyboard(course_id))

    except Exception as e:
        print(f"Error in certificate check: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)


# ============================================================
# 8. TASDIQLASH VA GENERATSIYA (YAKUNIY BOSQICH)
# ============================================================
@dp.callback_query_handler(text_startswith="cert:confirm:")
async def confirm_generation(call: types.CallbackQuery):
    course_id = int(call.data.split(":")[-1])
    telegram_id = call.from_user.id

    await call.answer("⏳ Sertifikat tayyorlanmoqda...", show_alert=False)

    # Bazada yaratish
    cert_data = user_db.generate_certificate(telegram_id, course_id)

    if not cert_data:
        cert_data = user_db.get_certificate(telegram_id, course_id)

    # Yuborish funksiyasini chaqiramiz
    await generate_and_send_final(call, telegram_id, course_id, cert_data)


# ============================================================
# 9. RASM YASASH, USERGA VA ADMINGA YUBORISH
# ============================================================
async def generate_and_send_final(call: types.CallbackQuery, telegram_id, course_id, cert_data):
    try:
        user = user_db.get_user(telegram_id)
        course = user_db.get_course(course_id)
        course_name = course['name'] if course else "Maxsus Kurs"
        full_name = user['full_name']

        # Xabarni tozalash
        try:
            await call.message.delete()
        except:
            pass

        msg = await call.message.answer("🖌 <b>Sertifikat yozilmoqda...</b>")

        # Rasm chizish
        cert_image = create_certificate(
            full_name=full_name,
            course_name=course_name,
            grade=cert_data['grade'],
            cert_code=cert_data['code']
        )

        caption = (
            f"🎉 <b>TABRIKLAYMIZ!</b>\n\n"
            f"Siz <b>{course_name}</b> kursini muvaffaqiyatli tamomladingiz!\n\n"
            f"👤 <b>{full_name}</b>\n"
            f"🆔 ID: <code>{cert_data['code']}</code>\n\n"
            f"<i>Ushbu sertifikat rasmiy hisoblanadi.</i>"
        )

        await msg.delete()

        # Userga yuborish
        sent_msg = await call.message.answer_photo(cert_image, caption=caption)
        await call.message.answer("⬇️ Asosiy menyu", reply_markup=user_main_menu())

        # ----------------------------------------------
        # 🔥 ADMINLARGA XABAR YUBORISH
        # ----------------------------------------------
        admin_text = (
            f"🎓 <b>YANGI SERTIFIKAT BERILDI!</b>\n\n"
            f"👤 User: <b>{full_name}</b>\n"
            f"🆔 Telegram ID: <code>{telegram_id}</code>\n"
            f"📚 Kurs: {course_name}\n"
            f"🔢 Sertifikat ID: {cert_data['code']}\n"
        )

        # Adminlarga yuborish
        for admin in ADMINS:
            try:
                await bot.send_photo(
                    chat_id=admin,
                    photo=sent_msg.photo[-1].file_id,
                    caption=admin_text
                )
            except Exception as e:
                print(f"Adminga yuborishda xato: {e}")

    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")


# ============================================================
# 10. MAVJUD SERTIFIKATNI OCHISH
# ============================================================
@dp.callback_query_handler(text_startswith="user:certificate:view:")
async def view_existing_certificate(call: types.CallbackQuery):
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
        await call.message.answer("⬇️ Menyuga qaytish", reply_markup=user_main_menu())

    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")



# ============================================================
# 7. ISMNI O'ZGARTIRISH (2-QADAM)
# ============================================================
@dp.callback_query_handler(text_startswith="cert:edit:")
async def change_name_start(call: types.CallbackQuery, state: FSMContext):
    """
    Ism o'zgartirish tugmasi bosilganda
    """
    try:
        parts = call.data.split(":")
        course_id = int(parts[-1])

        # Eski xabarni o'chirib tashlaymiz
        try:
            await call.message.delete()
        except:
            pass

        await call.message.answer(
            "📝 <b>Yangi ism va familiyangizni yozib yuboring:</b>\n\n"
            "<i>Masalan: Olimov Botir</i>"
        )

        # Qaysi kurs uchunligini eslab qolamiz
        await state.update_data(cert_course_id=course_id)

        # State ga o'tkazamiz (Foydalanuvchidan matn kutish rejimi)
        await CertificateStates.NewName.set()

    except Exception as e:
        print(f"Error changing name: {e}")
        await call.answer("Xatolik bo'ldi", show_alert=True)


@dp.message_handler(state=CertificateStates.NewName)
async def change_name_save(message: types.Message, state: FSMContext):
    """
    Yangi ismni saqlash
    """
    new_name = message.text.strip()

    # Ism juda qisqa bo'lsa
    if len(new_name) < 3:
        await message.answer("❌ Ism juda qisqa. Iltimos, to'liq ism-familiyani yozing:")
        return

    # Bazani yangilash
    user_db.execute(
        "UPDATE Users SET full_name = ? WHERE telegram_id = ?",
        parameters=(new_name, message.from_user.id),
        commit=True
    )

    # State dan ma'lumot olish
    data = await state.get_data()
    course_id = data.get('cert_course_id', 1)

    # State ni yopish
    await state.finish()

    text = f"""
✅ <b>Ism o'zgartirildi!</b>

Sertifikatga yoziladi:
👤 <b>{new_name}</b>

Tasdiqlaysizmi?
"""
    await message.answer(text, reply_markup=confirm_name_keyboard(course_id))