"""
Admin Settings Handler
======================
Sozlamalar va admin boshqaruvi handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from data.config import ADMINS
from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import settings_menu, back_button
from keyboards.default.admin_keyboards import admin_cancel_button, admin_confirm_keyboard, remove_keyboard
from states.admin_states import SettingsStates, AdminManageStates
from handlers.admin.admin_start import admin_required


# ============================================================
#                    SOZLAMALAR MENYUSI
# ============================================================

@dp.callback_query_handler(text="admin:settings")
@admin_required
async def show_settings_menu(call: types.CallbackQuery):
    """Sozlamalar menyusi"""

    text = f"""
⚙️ <b>Sozlamalar</b>

Quyidagi sozlamalarni boshqarishingiz mumkin:

💬 <b>Fikr sozlamalari</b> - Fikr uchun ball
📝 <b>Test sozlamalari</b> - O'tish bali
🎓 <b>Sertifikat sozlamalari</b> - Daraja chegaralari
👨‍💼 <b>Adminlar</b> - Admin qo'shish/o'chirish

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=settings_menu())
    await call.answer()


# ============================================================
#                    FIKR SOZLAMALARI
# ============================================================

@dp.callback_query_handler(text="admin:settings:feedback")
@admin_required
async def show_feedback_settings(call: types.CallbackQuery):
    """Fikr sozlamalari"""

    feedback_score = user_db.get_setting('feedback_score') or '5'
    feedback_required = user_db.get_setting('feedback_required') or 'false'

    required_text = "✅ Ha" if feedback_required == 'true' else "❌ Yo'q"

    text = f"""
💬 <b>Fikr sozlamalari</b>

<b>Joriy sozlamalar:</b>
├ ⭐️ Fikr uchun ball: <b>{feedback_score}</b>
└ 📝 Fikr majburiy: <b>{required_text}</b>

⬇️ O'zgartirish uchun tanlang:
"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(types.InlineKeyboardButton(
        "⭐️ Ball miqdorini o'zgartirish",
        callback_data="admin:setting:feedback_score"
    ))

    if feedback_required == 'true':
        keyboard.add(types.InlineKeyboardButton(
            "❌ Majburiylikni o'chirish",
            callback_data="admin:setting:feedback_required:false"
        ))
    else:
        keyboard.add(types.InlineKeyboardButton(
            "✅ Majburiy qilish",
            callback_data="admin:setting:feedback_required:true"
        ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:settings"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text="admin:setting:feedback_score")
@admin_required
async def change_feedback_score(call: types.CallbackQuery, state: FSMContext):
    """Fikr balini o'zgartirish"""

    await call.message.edit_text(
        "⭐️ <b>Fikr uchun ball</b>\n\n"
        "Yangi ball miqdorini kiriting (1-100):"
    )

    await call.message.answer(
        "✍️ Ball kiriting:",
        reply_markup=admin_cancel_button()
    )

    await SettingsStates.feedback_score.set()
    await call.answer()


@dp.message_handler(state=SettingsStates.feedback_score)
async def save_feedback_score(message: types.Message, state: FSMContext):
    """Fikr balini saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    try:
        score = int(message.text.strip())
        if score < 1 or score > 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1 dan 100 gacha son kiriting!")
        return

    user_db.set_setting('feedback_score', str(score))

    await state.finish()
    await message.answer(
        f"✅ Fikr uchun ball <b>{score}</b> ga o'zgartirildi!",
        reply_markup=remove_keyboard()
    )


@dp.callback_query_handler(text_startswith="admin:setting:feedback_required:")
@admin_required
async def toggle_feedback_required(call: types.CallbackQuery):
    """Fikr majburiyligini o'zgartirish"""
    value = call.data.split(":")[-1]

    user_db.set_setting('feedback_required', value)

    status = "yoqildi ✅" if value == 'true' else "o'chirildi ❌"
    await call.answer(f"Fikr majburiyligi {status}", show_alert=True)

    # Sahifani yangilash
    await show_feedback_settings(call)


# ============================================================
#                    TEST SOZLAMALARI
# ============================================================

@dp.callback_query_handler(text="admin:settings:test")
@admin_required
async def show_test_settings(call: types.CallbackQuery):
    """Test sozlamalari"""

    passing_score = user_db.get_setting('default_passing_score') or '60'

    text = f"""
📝 <b>Test sozlamalari</b>

<b>Joriy sozlamalar:</b>
└ 🎯 Standart o'tish bali: <b>{passing_score}%</b>

<i>Har bir test uchun alohida o'tish bali belgilash mumkin.</i>

⬇️ O'zgartirish uchun tanlang:
"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(types.InlineKeyboardButton(
        "🎯 Standart o'tish balini o'zgartirish",
        callback_data="admin:setting:passing_score"
    ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:settings"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text="admin:setting:passing_score")
@admin_required
async def change_passing_score(call: types.CallbackQuery, state: FSMContext):
    """O'tish balini o'zgartirish"""

    await call.message.edit_text(
        "🎯 <b>Standart o'tish bali</b>\n\n"
        "Yangi foizni kiriting (1-100):"
    )

    await call.message.answer(
        "✍️ Foiz kiriting:",
        reply_markup=admin_cancel_button()
    )

    await SettingsStates.test_passing_score.set()
    await call.answer()


@dp.message_handler(state=SettingsStates.test_passing_score)
async def save_passing_score(message: types.Message, state: FSMContext):
    """O'tish balini saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    try:
        score = int(message.text.strip())
        if score < 1 or score > 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1 dan 100 gacha son kiriting!")
        return

    user_db.set_setting('default_passing_score', str(score))

    await state.finish()
    await message.answer(
        f"✅ Standart o'tish bali <b>{score}%</b> ga o'zgartirildi!",
        reply_markup=remove_keyboard()
    )


# ============================================================
#                    SERTIFIKAT SOZLAMALARI
# ============================================================

@dp.callback_query_handler(text="admin:settings:cert")
@admin_required
async def show_cert_settings(call: types.CallbackQuery):
    """Sertifikat sozlamalari"""

    gold = user_db.get_setting('gold_threshold') or '90'
    silver = user_db.get_setting('silver_threshold') or '75'
    bronze = user_db.get_setting('bronze_threshold') or '60'

    text = f"""
🎓 <b>Sertifikat sozlamalari</b>

<b>Daraja chegaralari:</b>
├ 🥇 Oltin: <b>{gold}%</b> va yuqori
├ 🥈 Kumush: <b>{silver}% - {int(gold) - 1}%</b>
├ 🥉 Bronza: <b>{bronze}% - {int(silver) - 1}%</b>
└ 📜 Ishtirokchi: <b>{int(bronze) - 1}%</b> va past

⬇️ O'zgartirish uchun tanlang:
"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(types.InlineKeyboardButton(
        f"🥇 Oltin chegarasi ({gold}%)",
        callback_data="admin:setting:cert:gold"
    ))
    keyboard.add(types.InlineKeyboardButton(
        f"🥈 Kumush chegarasi ({silver}%)",
        callback_data="admin:setting:cert:silver"
    ))
    keyboard.add(types.InlineKeyboardButton(
        f"🥉 Bronza chegarasi ({bronze}%)",
        callback_data="admin:setting:cert:bronze"
    ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:settings"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:setting:cert:")
@admin_required
async def change_cert_threshold(call: types.CallbackQuery, state: FSMContext):
    """Sertifikat chegarasini o'zgartirish"""
    grade = call.data.split(":")[-1]

    grade_names = {'gold': 'Oltin', 'silver': 'Kumush', 'bronze': 'Bronza'}
    grade_icons = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}

    await state.update_data(grade=grade)

    await call.message.edit_text(
        f"{grade_icons[grade]} <b>{grade_names[grade]} chegarasi</b>\n\n"
        f"Yangi foizni kiriting (1-100):"
    )

    await call.message.answer(
        "✍️ Foiz kiriting:",
        reply_markup=admin_cancel_button()
    )

    if grade == 'gold':
        await SettingsStates.cert_gold.set()
    elif grade == 'silver':
        await SettingsStates.cert_silver.set()
    else:
        await SettingsStates.cert_bronze.set()

    await call.answer()


@dp.message_handler(state=[SettingsStates.cert_gold, SettingsStates.cert_silver, SettingsStates.cert_bronze])
async def save_cert_threshold(message: types.Message, state: FSMContext):
    """Sertifikat chegarasini saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    try:
        threshold = int(message.text.strip())
        if threshold < 1 or threshold > 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1 dan 100 gacha son kiriting!")
        return

    data = await state.get_data()
    grade = data.get('grade', 'bronze')

    user_db.set_setting(f'{grade}_threshold', str(threshold))

    grade_names = {'gold': 'Oltin', 'silver': 'Kumush', 'bronze': 'Bronza'}

    await state.finish()
    await message.answer(
        f"✅ {grade_names[grade]} chegarasi <b>{threshold}%</b> ga o'zgartirildi!",
        reply_markup=remove_keyboard()
    )


# ============================================================
#                    ADMINLAR BOSHQARUVI
# ============================================================

@dp.callback_query_handler(text="admin:settings:admins")
@admin_required
async def show_admins_list(call: types.CallbackQuery):
    """Adminlar ro'yxati"""

    # Super admin tekshirish
    is_main_admin = call.from_user.id in ADMINS
    current_admin = user_db.get_admin(call.from_user.id)
    is_db_super = current_admin and current_admin.get('is_super')
    if not is_main_admin and not is_db_super:
        await call.answer("⚠️ Faqat super admin bu bo'limga kira oladi!", show_alert=True)
        return

    admins = user_db.get_all_admins()

    text = f"""
👨‍💼 <b>Adminlar boshqaruvi</b>

Jami: {len(admins)} ta admin

"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for admin in admins:
        is_super = "👑" if admin.get('is_super') else "👨‍💼"
        name = admin.get('name') or str(admin.get('telegram_id'))

        keyboard.add(types.InlineKeyboardButton(
            f"{is_super} {name}",
            callback_data=f"admin:admin:view:{admin['id']}"
        ))

    keyboard.add(types.InlineKeyboardButton(
        "➕ Admin qo'shish",
        callback_data="admin:admin:add"
    ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:settings"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:admin:view:")
@admin_required
async def view_admin(call: types.CallbackQuery):
    """Adminni ko'rish"""
    admin_id = int(call.data.split(":")[-1])

    admin = user_db.execute(
        "SELECT * FROM Admins WHERE id = ?",
        parameters=(admin_id,),
        fetchone=True
    )

    if not admin:
        await call.answer("❌ Admin topilmadi!", show_alert=True)
        return

    # admin: 0-id, 1-telegram_id, 2-name, 3-is_super, 4-created_at

    is_super = "👑 Super admin" if admin[3] else "👨‍💼 Admin"

    text = f"""
{is_super}

🆔 Telegram ID: <code>{admin[1]}</code>
👤 Ism: <b>{admin[2] or 'Nomalum'}</b>
📅 Qo'shilgan: {admin[4][:10] if admin[4] else 'Nomalum'}
"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    # O'zini o'chira olmaydi
    if admin[1] != call.from_user.id:
        keyboard.add(types.InlineKeyboardButton(
            "🗑 O'chirish",
            callback_data=f"admin:admin:delete:{admin_id}"
        ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:settings:admins"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text="admin:admin:add")
@admin_required
async def add_admin_start(call: types.CallbackQuery, state: FSMContext):
    """Admin qo'shish"""

    # Super admin tekshirish
    current_admin = user_db.get_admin(call.from_user.id)
    if not current_admin or not current_admin.get('is_super'):
        await call.answer("⚠️ Faqat super admin qo'sha oladi!", show_alert=True)
        return

    await call.message.edit_text(
        "➕ <b>Admin qo'shish</b>\n\n"
        "Yangi adminning Telegram ID sini kiriting:"
    )

    await call.message.answer(
        "✍️ Telegram ID kiriting:",
        reply_markup=admin_cancel_button()
    )

    await AdminManageStates.add_telegram_id.set()
    await call.answer()


@dp.message_handler(state=AdminManageStates.add_telegram_id)
async def add_admin_telegram_id(message: types.Message, state: FSMContext):
    """Admin Telegram ID"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Son kiriting.")
        return

    # Mavjudligini tekshirish
    existing = user_db.execute(
        "SELECT id FROM Admins WHERE telegram_id = ?",
        parameters=(telegram_id,),
        fetchone=True
    )

    if existing:
        await message.answer("❌ Bu foydalanuvchi allaqachon admin!")
        return

    await state.update_data(telegram_id=telegram_id)

    await message.answer(
        f"✅ Telegram ID: <code>{telegram_id}</code>\n\n"
        "Endi admin ismini kiriting:",
        reply_markup=admin_cancel_button()
    )

    await AdminManageStates.add_name.set()


@dp.message_handler(state=AdminManageStates.add_name)
async def add_admin_name(message: types.Message, state: FSMContext):
    """Admin ismi"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Ism juda qisqa!")
        return

    await state.update_data(name=name)

    await message.answer(
        f"👤 Ism: <b>{name}</b>\n\n"
        "Super admin qilsinmi?",
        reply_markup=admin_confirm_keyboard()
    )

    await AdminManageStates.add_is_super.set()


@dp.message_handler(state=AdminManageStates.add_is_super)
async def add_admin_is_super(message: types.Message, state: FSMContext):
    """Super admin tanlash"""
    if message.text == "❌ Bekor qilish" or message.text == "❌ Yo'q":
        is_super = False
    elif message.text == "✅ Ha":
        is_super = True
    else:
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")
        return

    data = await state.get_data()

    # Admin qo'shish
    user_db.execute(
        """INSERT INTO Admins (telegram_id, name, is_super, created_at)
           VALUES (?, ?, ?, datetime('now'))""",
        parameters=(data['telegram_id'], data['name'], is_super)
    )

    await state.finish()

    role = "Super admin" if is_super else "Admin"
    await message.answer(
        f"✅ <b>{role} qo'shildi!</b>\n\n"
        f"👤 {data['name']}\n"
        f"🆔 <code>{data['telegram_id']}</code>",
        reply_markup=remove_keyboard()
    )

    # Yangi adminga xabar
    try:
        await bot.send_message(
            data['telegram_id'],
            f"🎉 Siz {role} sifatida tayinlandingiz!\n\n"
            f"Admin panelga kirish: /admin"
        )
    except:
        pass


@dp.callback_query_handler(text_startswith="admin:admin:delete:")
@admin_required
async def delete_admin(call: types.CallbackQuery):
    """Adminni o'chirish"""
    admin_id = int(call.data.split(":")[-1])

    admin = user_db.execute(
        "SELECT telegram_id, name FROM Admins WHERE id = ?",
        parameters=(admin_id,),
        fetchone=True
    )

    if not admin:
        await call.answer("❌ Admin topilmadi!", show_alert=True)
        return

    # O'zini o'chira olmaydi
    if admin[0] == call.from_user.id:
        await call.answer("❌ O'zingizni o'chira olmaysiz!", show_alert=True)
        return

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Ha, o'chirish",
            callback_data=f"admin:confirm:admin_delete:{admin_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Yo'q",
            callback_data="admin:settings:admins"
        )
    )

    await call.message.edit_text(
        f"⚠️ <b>Adminni o'chirish</b>\n\n"
        f"👤 {admin[1]}\n"
        f"🆔 <code>{admin[0]}</code>\n\n"
        f"Rostdan o'chirmoqchimisiz?",
        reply_markup=keyboard
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:confirm:admin_delete:")
@admin_required
async def confirm_delete_admin(call: types.CallbackQuery):
    """Adminni o'chirishni tasdiqlash"""
    admin_id = int(call.data.split(":")[-1])

    admin = user_db.execute(
        "SELECT telegram_id, name FROM Admins WHERE id = ?",
        parameters=(admin_id,),
        fetchone=True
    )

    if admin:
        user_db.execute(
            "DELETE FROM Admins WHERE id = ?",
            parameters=(admin_id,)
        )

        await call.message.edit_text(
            f"✅ <b>Admin o'chirildi!</b>\n\n"
            f"👤 {admin[1]}",
            reply_markup=back_button("admin:settings:admins")
        )

        # O'chirilgan adminga xabar
        try:
            await bot.send_message(
                admin[0],
                "⚠️ Sizning admin huquqlaringiz bekor qilindi."
            )
        except:
            pass
    else:
        await call.answer("❌ Admin topilmadi!", show_alert=True)

    await call.answer()

# ============================================================
#                    TO'LOV SOZLAMALARI
# ============================================================

@dp.callback_query_handler(text="admin:settings:payment")
@admin_required
async def show_payment_settings(call: types.CallbackQuery):
    card_number = user_db.get_setting('card_number') or '8600 0000 0000 0000'
    card_holder = user_db.get_setting('card_holder') or 'ISMI FAMILIYASI'

    text = f"""
💳 <b>To'lov sozlamalari</b>

<b>Joriy sozlamalar:</b>
├ 💳 Karta: <code>{card_number}</code>
└ 👤 Egasi: <b>{card_holder}</b>

⬇️ O'zgartirish uchun tanlang:
"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("💳 Karta raqamini o'zgartirish", callback_data="admin:setting:card_number"),
        types.InlineKeyboardButton("👤 Karta egasini o'zgartirish", callback_data="admin:setting:card_holder"),
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:settings")
    )

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text="admin:setting:card_number")
@admin_required
async def change_card_number(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "💳 <b>Karta raqami</b>\n\n"
        "Yangi karta raqamini kiriting:\n"
        "<i>Masalan: 8600 1234 5678 9012</i>"
    )
    await call.message.answer("✍️ Karta raqami:", reply_markup=admin_cancel_button())
    await SettingsStates.card_number.set()
    await call.answer()


@dp.message_handler(state=SettingsStates.card_number)
async def save_card_number(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    card = message.text.strip()
    card_digits = ''.join(filter(str.isdigit, card))

    if len(card_digits) < 16:
        await message.answer("❌ Karta raqami 16 ta raqamdan iborat bo'lishi kerak!")
        return

    formatted = ' '.join([card_digits[i:i+4] for i in range(0, 16, 4)])
    user_db.set_setting('card_number', formatted)

    await state.finish()
    await message.answer(f"✅ Karta raqami o'zgartirildi:\n<code>{formatted}</code>", reply_markup=remove_keyboard())


@dp.callback_query_handler(text="admin:setting:card_holder")
@admin_required
async def change_card_holder(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "👤 <b>Karta egasi</b>\n\n"
        "Karta egasining ismini kiriting:\n"
        "<i>Masalan: ALIYEV ALI</i>"
    )
    await call.message.answer("✍️ Ism:", reply_markup=admin_cancel_button())
    await SettingsStates.card_holder.set()
    await call.answer()


@dp.message_handler(state=SettingsStates.card_holder)
async def save_card_holder(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    name = message.text.strip().upper()
    user_db.set_setting('card_holder', name)

    await state.finish()
    await message.answer(f"✅ Karta egasi o'zgartirildi: <b>{name}</b>", reply_markup=remove_keyboard())


# ============================================================
#                    ESLATMA SOZLAMALARI
# ============================================================

@dp.callback_query_handler(text="admin:settings:reminder")
@admin_required
async def show_reminder_settings(call: types.CallbackQuery):
    reminder_days = user_db.get_setting('reminder_days') or '3'

    text = f"""
⏰ <b>Eslatma sozlamalari</b>

<b>Joriy sozlamalar:</b>
└ 📅 Eslatma kunlari: <b>{reminder_days} kun</b>

<i>Agar foydalanuvchi {reminder_days} kun davomida faol bo'lmasa, eslatma yuboriladi.</i>

⬇️ O'zgartirish uchun tanlang:
"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📅 Kun sonini o'zgartirish", callback_data="admin:setting:reminder_days"),
        types.InlineKeyboardButton("📤 Hozir eslatma yuborish", callback_data="admin:setting:send_reminders"),
        types.InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:settings")
    )

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text="admin:setting:reminder_days")
@admin_required
async def change_reminder_days(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "📅 <b>Eslatma kunlari</b>\n\n"
        "Necha kundan keyin eslatma yuborilsin? (1-30):"
    )
    await call.message.answer("✍️ Kun soni:", reply_markup=admin_cancel_button())
    await SettingsStates.reminder_days.set()
    await call.answer()


@dp.message_handler(state=SettingsStates.reminder_days)
async def save_reminder_days(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    try:
        days = int(message.text.strip())
        if not 1 <= days <= 30:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1-30 orasida son kiriting!")
        return

    user_db.set_setting('reminder_days', str(days))

    await state.finish()
    await message.answer(f"✅ Eslatma <b>{days} kun</b> ga o'zgartirildi!", reply_markup=remove_keyboard())


@dp.callback_query_handler(text="admin:setting:send_reminders")
@admin_required
async def send_reminders_now(call: types.CallbackQuery):
    reminder_days = int(user_db.get_setting('reminder_days') or '3')
    inactive_users = user_db.get_inactive_users(days=reminder_days)

    if not inactive_users:
        await call.answer(f"📭 {reminder_days} kundan ortiq faol bo'lmagan foydalanuvchilar yo'q", show_alert=True)
        return

    await call.answer(f"📤 {len(inactive_users)} ta foydalanuvchiga eslatma yuborilmoqda...")

    success = 0
    failed = 0

    for user in inactive_users:
        try:
            await bot.send_message(
                user['telegram_id'],
                "👋 <b>Salom!</b>\n\n"
                "Sizni sog'indik! Darslaringizni davom ettiring va yangi bilimlar oling. 📚\n\n"
                "Davom etish uchun /start buyrug'ini yuboring."
            )
            success += 1
        except:
            failed += 1

    await call.message.answer(
        f"✅ <b>Eslatmalar yuborildi!</b>\n\n"
        f"📤 Yuborildi: {success}\n"
        f"❌ Xato: {failed}"
    )