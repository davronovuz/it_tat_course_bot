"""
User Start Handler (SODDALASHTIRILGAN)
======================================
Oqim:
1. /start → Demo dars tugmasi
2. Demo dars → Video + Ro'yxatdan o'tish tugmasi
3. Ro'yxatdan o'tish → Ism, Telefon
4. Kursni boshlash → 1-dars
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import dp, user_db,bot
from keyboards.default.user_keyboards import phone_request, remove_keyboard, user_main_menu
from keyboards.inline.user_keyboards import (
    demo_lesson_button,
    after_demo_not_registered,
    after_demo_registered,
    simple_lessons_list,
    payment_info,
    payment_pending
)
from states.user_states import RegistrationStates, PaymentStates


# handlers/users/start.py oxiriga qo'shing:

@dp.message_handler(commands=['fix_my_progress'])
async def force_complete_all(message: types.Message):
    user_id = user_db.get_user_id(message.from_user.id)

    # 1. Barcha aktiv darslarni topamiz
    user_db.execute(
        """INSERT OR REPLACE INTO UserProgress (user_id, lesson_id, status, completed_at)
           SELECT ?, id, 'completed', datetime('now')
           FROM Lessons WHERE is_active = 1""",
        parameters=(user_id,),
        commit=True
    )

    await message.answer(
        "✅ **TUZATILDI!**\n\nBarcha darslar 'Tugatilgan' deb belgilandi.\nEndi bemalol Sertifikat olishingiz mumkin.")

# handlers/users/start.py oxiriga qo'shing

@dp.message_handler(commands=['check_my_progress'])
async def debug_progress(message: types.Message):
    user_id = user_db.get_user_id(message.from_user.id)

    # Barcha darslarni olamiz (faqat aktivlarini)
    # Hozircha 1-kurs deb hisoblaymiz
    lessons = user_db.execute(
        """SELECT l.id, l.name, l.order_num 
           FROM Lessons l 
           JOIN Modules m ON l.module_id = m.id 
           WHERE m.course_id = 1 AND l.is_active = 1
           ORDER BY l.order_num""",
        fetchall=True
    )

    text = "🔍 **DIAGNOSTIKA:**\n\n"
    count = 0

    for l in lessons:
        lid, name, order = l
        # Har bir dars uchun statusni tekshiramiz
        status = user_db.execute(
            "SELECT status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
            (user_id, lid), fetchone=True
        )
        st_text = status[0] if status else "❌ YO'Q (boshlanmagan)"

        if st_text == 'completed':
            icon = "✅"
            count += 1
        else:
            icon = "⚠️"

        text += f"{icon} {order}-dars: {name}\nStatus: <b>{st_text}</b>\n\n"

    total = len(lessons)
    percent = (count / total * 100) if total > 0 else 0
    text += f"📊 Jami: {count}/{total} ({percent}%)"

    await message.answer(text)


# ============================================================
#                    1. /START BUYRUG'I
# ============================================================

@dp.message_handler(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """
    /start buyrug'i (referal bilan)
    """
    await state.finish()

    telegram_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Referal kodni olish
    args = message.get_args()
    referral_code = args if args and args.startswith('REF_') else None

    # Foydalanuvchi bazada bormi?
    user = user_db.get_user(telegram_id)

    if not user:
        # Yangi user
        user_db.add_user(telegram_id, username=username, full_name=full_name)

        # Referal orqali kelgan bo'lsa
        if referral_code:
            referrer = user_db.get_user_by_referral_code(referral_code)
            if referrer and referrer['telegram_id'] != telegram_id:
                if user_db.register_referral(referrer['telegram_id'], telegram_id):
                    # Taklif qiluvchiga xabar
                    try:
                        bonus = user_db.get_setting('referral_bonus_register', '5')
                        await bot.send_message(
                            referrer['telegram_id'],
                            f"🎉 Yangi taklif!\n\n"
                            f"Havolangiz orqali kimdir ro'yxatdan o'tdi.\n"
                            f"🎁 <b>+{bonus} ball</b>"
                        )
                    except:
                        pass
    else:
        # Mavjud user
        user_db.update_user(telegram_id, username=username)
        user_db.update_last_active(telegram_id)

        if check_has_paid_course(user['id']):
            await show_lessons_list(message, user['id'])
            return

    text = """
    <b>IT TAT markazining Online Kompyuter Savodxonlik Kursiga xush kelibsiz!</b>

    Siz hozir o‘zingizni rivojlantirish, yangi ko‘nikmalar orttirish va kelajagingizga sarmoya qilish yo‘lida birinchi va eng muhim qadamni tashladingiz.

    Avval bepul demo darsni ko'rib chiqing 👇
    """

    await message.answer(text, reply_markup=demo_lesson_button())


# ============================================================
#                    2. DEMO DARS
# ============================================================
@dp.callback_query_handler(text="user:demo")
async def show_demo_lesson(call: types.CallbackQuery):
    """
    Demo darsni ko'rsatish - video + kurs info + tugma
    """
    demo = user_db.execute(
        """SELECT l.id, l.name, l.description, l.video_file_id
           FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE l.is_free = 1 AND l.is_active = 1 
               AND m.is_active = 1 AND c.is_active = 1
           ORDER BY c.order_num, m.order_num, l.order_num
           LIMIT 1""",
        fetchone=True
    )

    if not demo:
        await call.answer("❌ Demo dars topilmadi", show_alert=True)
        return

    lesson_id, name, description, video_file_id = demo

    caption = f"""📘 <b>Demo dars: {name}</b>

{description or "Bu darsda siz kompyuterning asosiy ishlashini ko'rasiz."}
"""

    # Avvalgi xabarni o'chirish
    try:
        await call.message.delete()
    except:
        pass

    # Video yuborish
    if video_file_id:
        try:
            await call.message.answer_video(video_file_id, caption=caption)
        except:
            await call.message.answer(caption)
    else:
        await call.message.answer(caption)

    # Kurs haqida ma'lumot
    course_info = get_course_info()
    user = user_db.get_user(call.from_user.id)

    if user and user.get('phone'):
        keyboard = after_demo_registered()
    else:
        keyboard = after_demo_not_registered()

    info_text = f"""
    📊 <b>Kurs haqida:</b>

    📚 Darslar soni: <b>{course_info['lessons_count']} ta</b>
    ⏱ Umumiy davomiylik: <b>{course_info['total_duration']}</b>
    📹 O'rtacha 1 dars: <b>{course_info['avg_duration']}</b>

    👥 <b>Kimlar uchun:</b>
    Kompyuterni noldan o'rganayotganlar va zamonaviy kasb egalari uchun.

    ✅ <b>Kurs davomida nimalarni o'rganasiz:</b>
    💻 <b>Windows & Asoslar:</b> Kompyuterda erkin va tez ishlash.
    📄 <b>Microsoft Office:</b> Word, Excel, PowerPoint dasturlari.
    ☁️ <b>Google Cloud:</b> Google Docs, Sheets va onlayn ofis.
    🤖 <b>Sun'iy Intellekt (AI):</b> ChatGPT va AI yordamida ishlarni osonlashtirish.
    🎓 <b>Natija:</b> Kurs yakunida Maxsus Sertifikat olasiz!
    """

    await call.message.answer(info_text, reply_markup=keyboard)
    await call.answer()





# ============================================================
#                    3. RO'YXATDAN O'TISH
# ============================================================

@dp.callback_query_handler(text="user:register")
async def start_registration(call: types.CallbackQuery, state: FSMContext):
    """
    Ro'yxatdan o'tishni boshlash - ism so'rash
    """
    # Video xabarni edit qilib bo'lmaydi, yangi xabar yuboramiz
    try:
        await call.message.delete()
    except:
        pass

    await call.message.answer(
        "📝 Ismingizni yuboring:\n\n"
        "<i>Masalan: Aliyev Ali</i>"
    )

    await RegistrationStates.full_name.set()
    await call.answer()


@dp.message_handler(state=RegistrationStates.full_name)
async def get_full_name(message: types.Message, state: FSMContext):
    """
    Ismni qabul qilish
    """
    full_name = message.text.strip()

    # Tekshirish
    if len(full_name) < 3:
        await message.answer("❌ Ism juda qisqa. Qaytadan kiriting:")
        return

    await state.update_data(full_name=full_name)

    await message.answer(
        f"👤 Ism: <b>{full_name}</b>\n\n"
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_request()
    )

    await RegistrationStates.phone.set()


@dp.message_handler(state=RegistrationStates.phone, content_types=['contact'])
async def get_phone_contact(message: types.Message, state: FSMContext):
    """
    Telefon raqamni contact orqali olish
    """
    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone

    await finish_registration(message, state, phone)


@dp.message_handler(state=RegistrationStates.phone)
async def get_phone_text(message: types.Message, state: FSMContext):
    """
    Telefon raqamni matn orqali olish
    """
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    phone = message.text.strip()
    phone_clean = ''.join(filter(str.isdigit, phone))

    if len(phone_clean) < 9:
        await message.answer(
            "❌ Telefon raqam noto'g'ri.\n\n"
            "📱 Qaytadan yuboring:",
            reply_markup=phone_request()
        )
        return

    # Formatlash
    if phone_clean.startswith('998'):
        phone = '+' + phone_clean
    elif len(phone_clean) == 9:
        phone = '+998' + phone_clean
    else:
        phone = '+998' + phone_clean[-9:]

    await finish_registration(message, state, phone)


async def finish_registration(message: types.Message, state: FSMContext, phone: str):
    """
    Ro'yxatdan o'tishni tugatish
    """
    data = await state.get_data()
    full_name = data.get('full_name', message.from_user.full_name)

    # Bazaga saqlash
    user_db.update_user(
        message.from_user.id,
        full_name=full_name,
        phone=phone
    )

    await state.finish()

    text = f"""
✅ Rahmat! Siz ro'yxatdan o'tdingiz.

👤 Ism: {full_name}
📱 Telefon: {phone}
"""

    await message.answer(text, reply_markup=user_main_menu())

    # Keyingi tugma - kursni boshlash yoki sotib olish
    course = get_main_course()

    if course and course.get('price', 0) > 0:
        # Pullik kurs - to'lov kerak
        price = course['price']
        price_text = f"{price:,.0f}".replace(",", " ")

        text2 = f"""
📚 <b>{course['name']}</b>

💰 Kurs narxi: <b>{price_text} so'm</b>

Kursni sotib oling:
"""
        await message.answer(text2, reply_markup=after_demo_registered())
    else:
        # Bepul kurs yoki narx yo'q - darslarni boshlash
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➡️ Kursni boshlash", callback_data="user:start_course"))

        await message.answer("Kursni boshlashingiz mumkin:", reply_markup=kb)


# ============================================================
#                    4. KURSNI BOSHLASH / TO'LOV
# ============================================================

@dp.callback_query_handler(text="user:start_course")
async def start_course(call: types.CallbackQuery):
    """
    Kursni boshlash - 1-darsni ko'rsatish
    """
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user:
        await call.answer("❌ Avval ro'yxatdan o'ting", show_alert=True)
        return

    user_id = user['id']

    # Darslar ro'yxatini ko'rsatish
    await show_lessons_list_callback(call, user_id)

@dp.callback_query_handler(text="user:buy")
async def buy_course(call: types.CallbackQuery, state: FSMContext):
    """
    Kursni sotib olish - to'lov ma'lumotlari
    """
    telegram_id = call.from_user.id
    user = user_db.get_user(telegram_id)

    if not user or not user.get('phone'):
        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer(
            "📝 Avval ro'yxatdan o'ting:",
            reply_markup=after_demo_not_registered()
        )
        await call.answer()
        return

    course = get_main_course()

    if not course:
        await call.answer("❌ Kurs topilmadi", show_alert=True)
        return

    # To'lov ma'lumotlari
    price = course.get('price', 0)
    price_text = f"{price:,.0f}".replace(",", " ")

    # Kurs info
    course_info = get_course_info()

    # TODO: Config dan olish
    card_number = user_db.get_setting('card_number') or "8600 1234 5678 9012"
    card_holder = user_db.get_setting('card_holder') or "ALIYEV ALI"

    text = f"""
💳 <b>To'lov</b>

📚 Kurs: {course['name']}
💰 Narxi: <b>{price_text} so'm</b>

📊 <b>Kurs tarkibi:</b>
- {course_info['lessons_count']} ta video dars
- Umumiy: {course_info['total_duration']}
- O'rtacha 1 dars: {course_info['avg_duration']}

━━━━━━━━━━━━━━━━━━━━

💳 Karta raqami:
<code>{card_number}</code>

👤 Egasi: {card_holder}

━━━━━━━━━━━━━━━━━━━━

✅ To'lovni amalga oshiring va chekni yuboring.
"""

    try:
        await call.message.delete()
    except:
        pass
    await call.message.answer(text, reply_markup=payment_info())
    await state.update_data(course_id=course['id'])
    await PaymentStates.receipt.set()
    await call.answer()


@dp.callback_query_handler(text="user:send_receipt", state=PaymentStates.receipt)
async def send_receipt_clicked(call: types.CallbackQuery):
    """
    To'ladim tugmasi bosildi
    """
    await call.message.answer("📸 Chek rasmini yuboring:")
    await call.answer()


@dp.message_handler(state=PaymentStates.receipt, content_types=['photo', 'document'])
async def receive_payment_receipt(message: types.Message, state: FSMContext):
    """
    Chek rasmini yoki hujjatni qabul qilish
    """
    # Photo yoki document
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        # Faqat rasm formatlarini qabul qilish
        mime = message.document.mime_type or ""
        if mime.startswith('image/') or mime == 'application/pdf':
            file_id = message.document.file_id
        else:
            await message.answer("❌ Faqat rasm yoki PDF yuboring!")
            return
    else:
        await message.answer("❌ Chek rasmini yuboring!")
        return

    data = await state.get_data()
    course_id = data.get('course_id')

    user = user_db.get_user(message.from_user.id)
    course = user_db.get_course(course_id)

    # To'lov yaratish
    payment_id = user_db.create_payment(
        telegram_id=message.from_user.id,
        course_id=course_id,
        amount=course['price'],
        receipt_file_id=file_id
    )

    await state.finish()

    if payment_id:
        await message.answer(
            f"✅ <b>Chek qabul qilindi!</b>\n\n"
            f"⏳ Admin tekshirmoqda...",
            reply_markup=payment_pending()
        )
        await notify_admin_new_payment(user, course_id, file_id, payment_id)
    else:
        await message.answer("❌ Xatolik yuz berdi!")






@dp.message_handler(state=PaymentStates.receipt)
async def receipt_invalid(message: types.Message):
    """
    Chek rasm emas
    """
    await message.answer("❌ Iltimos, chek <b>rasmini</b> yuboring!")


@dp.callback_query_handler(text="user:check_payment")
async def check_payment(call: types.CallbackQuery):
    """
    To'lov statusini tekshirish
    """
    user = user_db.get_user(call.from_user.id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    payment = user_db.execute(
        "SELECT status FROM Payments WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        parameters=(user['id'],),
        fetchone=True
    )

    if not payment:
        await call.answer("❌ To'lov topilmadi", show_alert=True)
        return

    status = payment[0]

    if status == 'approved':
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➡️ Kursni boshlash", callback_data="user:start_course"))

        await call.message.edit_text(
            "✅ <b>To'lov tasdiqlandi!</b>\n\n"
            "Endi darslarni boshlashingiz mumkin:",
            reply_markup=kb
        )
    elif status == 'rejected':
        await call.message.edit_text(
            "❌ <b>To'lov rad etildi</b>\n\n"
            "Qaytadan urinib ko'ring:",
            reply_markup=after_demo_registered()
        )
    else:
        await call.answer("⏳ Hali tekshirilmoqda...", show_alert=True)


# ============================================================
#                    DARSLAR RO'YXATI
# ============================================================

@dp.callback_query_handler(text="user:lessons")
async def show_lessons_callback(call: types.CallbackQuery):
    """
    Darslar ro'yxatini ko'rsatish (callback)
    """
    user = user_db.get_user(call.from_user.id)

    if not user:
        await call.answer("❌ Xatolik", show_alert=True)
        return

    await show_lessons_list_callback(call, user['id'])


async def show_lessons_list(message: types.Message, user_id: int):
    """
    Darslar ro'yxatini ko'rsatish (message)
    """
    from keyboards.default.user_keyboards import user_main_menu

    lessons = get_all_lessons_with_status(user_id)

    if not lessons:
        await message.answer("📭 Darslar topilmadi")
        return

    completed = sum(1 for l in lessons if l['status'] == 'completed')
    total = len(lessons)

    text = f"""
📚 <b>Darslar</b>

📊 Progress: {completed}/{total}
"""

    # Inline darslar + Reply menyu
    await message.answer(text, reply_markup=simple_lessons_list(lessons))
    await message.answer("⬇️", reply_markup=user_main_menu())

async def show_lessons_list_callback(call: types.CallbackQuery, user_id: int):
    """
    Darslar ro'yxatini ko'rsatish (callback)
    """
    lessons = get_all_lessons_with_status(user_id)

    if not lessons:
        await call.message.edit_text("📭 Darslar topilmadi")
        await call.answer()
        return

    completed = sum(1 for l in lessons if l['status'] == 'completed')
    total = len(lessons)

    text = f"""
📚 <b>Darslar</b>

📊 Progress: {completed}/{total}
"""

    await call.message.edit_text(text, reply_markup=simple_lessons_list(lessons))
    await call.answer()


# ============================================================
#                    YOPIQ DARS
# ============================================================

@dp.callback_query_handler(text_startswith="user:locked:")
async def locked_lesson(call: types.CallbackQuery):
    """
    Yopiq dars bosilganda
    """
    await call.answer(
        "🔒 Bu dars yopiq!\n\nAvvalgi darsni yakunlang.",
        show_alert=True
    )


# ============================================================
#                    BEKOR QILISH
# ============================================================

@dp.callback_query_handler(text="user:cancel", state="*")
async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    """
    Bekor qilish
    """
    await state.finish()

    await call.message.edit_text(
        "❌ Bekor qilindi\n\n"
        "Qaytadan boshlash uchun /start buyrug'ini yuboring."
    )
    await call.answer()


@dp.message_handler(Text(equals="❌ Bekor qilish"), state="*")
async def cancel_message(message: types.Message, state: FSMContext):
    """
    Bekor qilish (message)
    """
    await state.finish()
    await message.answer(
        "❌ Bekor qilindi",
        reply_markup=remove_keyboard()
    )


# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def get_main_course():
    """
    Asosiy kursni olish
    """
    result = user_db.execute(
        """SELECT id, name, description, price
           FROM Courses WHERE is_active = TRUE
           ORDER BY order_num LIMIT 1""",
        fetchone=True
    )

    if result:
        return {
            'id': result[0],
            'name': result[1],
            'description': result[2],
            'price': result[3]
        }
    return None


def check_has_paid_course(user_id: int) -> bool:
    """
    To'lov qilganmi?
    """
    # Payments tekshirish
    result = user_db.execute(
        "SELECT 1 FROM Payments WHERE user_id = ? AND status = 'approved' LIMIT 1",
        parameters=(user_id,),
        fetchone=True
    )
    if result:
        return True

    # ManualAccess tekshirish
    result = user_db.execute(
        """SELECT 1 FROM ManualAccess WHERE user_id = ? 
           AND (expires_at IS NULL OR expires_at > datetime('now')) LIMIT 1""",
        parameters=(user_id,),
        fetchone=True
    )
    return bool(result)


def get_all_lessons_with_status(user_id: int) -> list:
    """
    Barcha darslarni status bilan olish
    Modul ko'rinmaydi - ketma-ket darslar
    """
    lessons = user_db.execute(
        """SELECT l.id, l.name
           FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE l.is_active = TRUE AND m.is_active = TRUE AND c.is_active = TRUE
           ORDER BY c.order_num, m.order_num, l.order_num""",
        fetchall=True
    )

    if not lessons:
        return []

    # User progress
    progress = user_db.execute(
        "SELECT lesson_id, status FROM UserProgress WHERE user_id = ?",
        parameters=(user_id,),
        fetchall=True
    )
    progress_dict = {p[0]: p[1] for p in progress} if progress else {}

    result = []
    order = 0
    prev_completed = True

    for lesson in lessons:
        order += 1
        lesson_id = lesson[0]
        name = lesson[1]

        user_status = progress_dict.get(lesson_id)

        if user_status == 'completed':
            status = 'completed'
            prev_completed = True
        elif prev_completed:
            status = 'unlocked'
            prev_completed = False
        else:
            status = 'locked'

        result.append({
            'id': lesson_id,
            'order_num': order,
            'name': name,
            'status': status
        })

    return result


async def notify_admin_new_payment(user: dict, course_id: int, file_id: str, payment_id: int):
    """
    Adminga yangi to'lov haqida xabar (YANGILANGAN)
    """
    # Eski importni olib tashlaymiz: from data.config import ADMINS
    from loader import bot

    course = user_db.execute(
        "SELECT name, price FROM Courses WHERE id = ?",
        parameters=(course_id,),
        fetchone=True
    )

    course_name = course[0] if course else "Noma'lum"
    price = course[1] if course else 0
    price_text = f"{price:,.0f}".replace(",", " ")

    text = f"""
💰 <b>Yangi to'lov!</b>

👤 User: {user.get('full_name', "Nomalum")}
📱 Tel: {user.get('phone', 'Nomalum')}
🆔 @{user.get('username') or 'yoq'}


📚 Kurs: {course_name}
💵 Summa: <b>{price_text} so'm</b>

"""

    # Admin keyboard
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin:payment:approve:{payment_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"admin:payment:reject:{payment_id}")
    )

    # --- O'ZGARISH SHU YERDA ---
    # Configdagi adminlarni emas, barcha adminlarni olamiz (DB + Config)
    # Biz oldinroq db.py ga get_notification_admins funksiyasini qo'shgan edik
    try:
        admin_ids = user_db.get_notification_admins()
    except AttributeError:
        # Ehtiyot shart: Agar db da funksiya bo'lmasa, eski usulda ishlaydi
        from data.config import ADMINS
        admin_ids = ADMINS

    for admin_id in admin_ids:
        try:
            # Fayl turiga qarab yuborish (Rasm yoki Hujjat)
            # file_id uzunligiga qarab yoki try-except bilan aniqlash mumkin,
            # lekin odatda user_handlers da aniqlab kelgan ma'qul.
            # Hozircha oddiy send_photo/document try-except bilan:

            try:
                await bot.send_photo(admin_id, file_id, caption=text, reply_markup=kb)
            except:
                await bot.send_document(admin_id, file_id, caption=text, reply_markup=kb)

        except Exception as e:
            # Admin bloklagan bo'lsa
            pass




def get_course_info() -> dict:
    """
    Kurs haqida dinamik ma'lumotlar
    """
    # Darslar soni
    lessons_count = user_db.execute(
        """SELECT COUNT(*) FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE l.is_active = 1 AND m.is_active = 1 AND c.is_active = 1""",
        fetchone=True
    )

    # Umumiy va o'rtacha davomiylik
    duration_stats = user_db.execute(
        """SELECT SUM(video_duration), AVG(video_duration) FROM Lessons l
           JOIN Modules m ON l.module_id = m.id
           JOIN Courses c ON m.course_id = c.id
           WHERE l.is_active = 1 AND m.is_active = 1 AND c.is_active = 1
           AND video_duration IS NOT NULL""",
        fetchone=True
    )

    total_seconds = duration_stats[0] if duration_stats and duration_stats[0] else 0
    avg_seconds = duration_stats[1] if duration_stats and duration_stats[1] else 0

    # Sekundlarni formatlash
    def format_duration(seconds):
        if not seconds:
            return "Noma'lum"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours} soat {minutes} minut"
        return f"{minutes} minut"

    return {
        'lessons_count': lessons_count[0] if lessons_count else 0,
        'total_duration': format_duration(total_seconds),
        'avg_duration': format_duration(avg_seconds)
    }


@dp.message_handler(text="📢 Telegram kanal")
async def open_channel_handler(message: types.Message):
    # Kanal havolasi
    channel_url = "https://t.me/it_tat_samarkand"  # O'zingiznikini qo'ying

    # Chiroyli ko'rinishi uchun Inline tugma ham qo'shamiz
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("↗️ Kanalga o'tish", url=channel_url))

    await message.answer(
        "📢 <b>Bizning rasmiy kanalimiz:</b>\n\n"
        "Yangiliklardan xabardor bo'lish uchun obuna bo'ling!",
        reply_markup=kb
    )


@dp.message_handler(text="📞 Admin bilan aloqa")
async def contact_admin_menu(message: types.Message):
    """
    Admin aloqa ma'lumotlarini chiqarish
    """
    # Ma'lumotlarni o'zingizga moslang
    admin_phone = "+998 90 123 45 67"
    admin_username = "@AdminUsername"
    work_hours = "09:00 - 18:00"

    text = f"""
📞 <b>Admin bilan aloqa</b>

Savollaringiz bormi? Bizga bog'laning:

📱 <b>Telefon:</b> {admin_phone}
👤 <b>Telegram:</b> {admin_username}
🕰 <b>Ish vaqti:</b> {work_hours}

<i>Sizga tez orada javob beramiz!</i>
"""
    await message.answer(text)