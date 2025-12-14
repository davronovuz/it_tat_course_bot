"""
Admin Start Handler
===================
Admin panel bosh menyu va kirish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import (
    admin_main_menu,
    courses_menu,
    users_menu,
    payments_menu,
    reports_menu,
    feedbacks_menu,
    settings_menu,
    broadcast_menu
)
from keyboards.default.admin_keyboards import admin_main_menu as admin_reply_menu
from states.admin_states import AdminMainState


# ============================================================
#                    ADMIN TEKSHIRISH DECORATOR
# ============================================================
def admin_required(func):
    from functools import wraps

    @wraps(func)
    async def wrapper(message_or_call, state: FSMContext = None, **kwargs):
        if isinstance(message_or_call, types.Message):
            telegram_id = message_or_call.from_user.id
        else:
            telegram_id = message_or_call.from_user.id

        if not user_db.is_admin(telegram_id):
            if isinstance(message_or_call, types.Message):
                await message_or_call.answer("⛔️ Sizda admin huquqi yo'q!")
            else:
                await message_or_call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
            return

        if state is not None:
            return await func(message_or_call, state=state, **kwargs)
        else:
            return await func(message_or_call, **kwargs)

    return wrapper


# ============================================================
#                    ADMIN PANEL KIRISH
# ============================================================
@dp.message_handler(Command("admin"))
async def admin_panel_command(message: types.Message, state: FSMContext):
    """Admin panel /admin buyrug'i"""
    telegram_id = message.from_user.id

    # ✅ DEBUG
    from data.config import ADMINS
    print(f"DEBUG admin_panel_command:")
    print(f"  telegram_id: {telegram_id}")
    print(f"  ADMINS: {ADMINS}")
    print(f"  in ADMINS: {telegram_id in ADMINS}")
    print(f"  is_admin: {user_db.is_admin(telegram_id)}")

    # Admin tekshirish
    if not user_db.is_admin(telegram_id):
        await message.answer("⛔️ Sizda admin huquqi yo'q!")
        return

    # Admin ma'lumotlari
    user = user_db.get_user(telegram_id)
    is_super = user_db.is_super_admin(telegram_id)

    # Statistika
    stats = user_db.get_dashboard_stats()

    text = f"""
👨‍💼 <b>Admin Panel</b>

👋 Xush kelibsiz, {user.get('full_name') or user.get('username') or 'Admin'}!
{"👑 Super Admin" if is_super else "👨‍💼 Admin"}

📊 <b>Qisqacha statistika:</b>
├ 👥 Foydalanuvchilar: {stats.get('total_users', 0)}
├ 📅 Bugun yangi: {stats.get('new_users_today', 0)}
├ 💰 Kutilayotgan to'lovlar: {stats.get('pending_payments', 0)}
└ 📚 Kurslar: {stats.get('total_courses', 0)}

⬇️ Quyidagi menyudan tanlang:
"""

    await message.answer(text, reply_markup=admin_reply_menu())
    await state.finish()


@dp.message_handler(Text(equals="👨‍💼 Admin panel"))
async def admin_panel_button(message: types.Message, state: FSMContext):
    """Admin panel tugmasi orqali"""
    await admin_panel_command(message, state)


# ============================================================
#                    ASOSIY MENYU HANDLERLARI
# ============================================================

@dp.message_handler(Text(equals="📚 Kurslar"))
async def admin_courses_menu(message: types.Message):
    """Kurslar bo'limi"""
    if not user_db.is_admin(message.from_user.id):
        return

    text = """
📚 <b>Kurslar boshqaruvi</b>

Bu yerda siz:
• Yangi kurs qo'shishingiz
• Mavjud kurslarni tahrirlashingiz
• Modullar va darslarni boshqarishingiz mumkin

⬇️ Tanlang:
"""

    await message.answer(text, reply_markup=courses_menu())


@dp.message_handler(Text(equals="👥 Foydalanuvchilar"))
async def admin_users_menu(message: types.Message):
    """Foydalanuvchilar bo'limi"""
    if not user_db.is_admin(message.from_user.id):
        return

    total_users = user_db.count_users()

    text = f"""
👥 <b>Foydalanuvchilar boshqaruvi</b>

📊 Jami: {total_users} ta foydalanuvchi

Bu yerda siz:
• Foydalanuvchilarni ko'rishingiz
• Qidirishingiz
• Dostup berishingiz mumkin

⬇️ Tanlang:
"""

    await message.answer(text, reply_markup=users_menu())


@dp.message_handler(Text(equals="💰 To'lovlar"))
async def admin_payments_menu(message: types.Message):
    """To'lovlar bo'limi"""
    if not user_db.is_admin(message.from_user.id):
        return

    pending_count = user_db.count_pending_payments()

    text = f"""
💰 <b>To'lovlar boshqaruvi</b>

📥 Kutilayotgan: {pending_count} ta

Bu yerda siz:
• To'lovlarni tasdiqlashingiz
• Rad etishingiz
• Statistikani ko'rishingiz mumkin

⬇️ Tanlang:
"""

    await message.answer(text, reply_markup=payments_menu())


@dp.message_handler(Text(equals="📊 Hisobotlar"))
async def admin_reports_menu(message: types.Message):
    """Hisobotlar bo'limi"""
    if not user_db.is_admin(message.from_user.id):
        return

    text = """
📊 <b>Hisobotlar</b>

Bu yerda siz:
• Umumiy statistikani
• Moliyaviy hisobotni
• Kurs statistikasini ko'rishingiz mumkin

⬇️ Tanlang:
"""

    await message.answer(text, reply_markup=reports_menu())


@dp.message_handler(Text(equals="💬 Fikrlar"))
async def admin_feedbacks_menu(message: types.Message):
    """Fikrlar bo'limi"""
    if not user_db.is_admin(message.from_user.id):
        return

    text = """
💬 <b>Fikr-mulohazalar</b>

Bu yerda siz:
• O'quvchilar fikrlarini
• Baholarni ko'rishingiz mumkin

⬇️ Tanlang:
"""

    await message.answer(text, reply_markup=feedbacks_menu())


@dp.message_handler(Text(equals="⚙️ Sozlamalar"))
async def admin_settings_menu(message: types.Message):
    """Sozlamalar bo'limi"""
    if not user_db.is_admin(message.from_user.id):
        return

    text = """
⚙️ <b>Sozlamalar</b>

Bu yerda siz:
• Test sozlamalarini
• Sertifikat sozlamalarini
• Adminlarni boshqarishingiz mumkin

⬇️ Tanlang:
"""

    await message.answer(text, reply_markup=settings_menu())


@dp.message_handler(Text(equals="🏠 Bosh menyu"))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Bosh menyuga qaytish"""
    await state.finish()

    # User yoki Admin menyusiga qaytish
    if user_db.is_admin(message.from_user.id):
        await admin_panel_command(message, state)
    else:
        # User main menu (bu keyinroq qo'shiladi)
        from keyboards.default.user_keyboards import main_menu
        await message.answer("🏠 Bosh menyu", reply_markup=main_menu())


@dp.message_handler(Text(equals="⬅️ Orqaga"))
async def back_button_handler(message: types.Message, state: FSMContext):
    """Orqaga tugmasi"""
    current_state = await state.get_state()

    if current_state:
        await state.finish()

    if user_db.is_admin(message.from_user.id):
        await admin_panel_command(message, state)


# ============================================================
#                    INLINE CALLBACK HANDLERS
# ============================================================

@dp.callback_query_handler(text="admin:main")
async def callback_admin_main(call: types.CallbackQuery, state: FSMContext):
    """Admin bosh menyusiga qaytish"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    await state.finish()

    user = user_db.get_user(call.from_user.id)
    stats = user_db.get_dashboard_stats()

    text = f"""
👨‍💼 <b>Admin Panel</b>

📊 <b>Qisqacha statistika:</b>
├ 👥 Foydalanuvchilar: {stats.get('total_users', 0)}
├ 📅 Bugun yangi: {stats.get('new_users_today', 0)}
├ 💰 Kutilayotgan to'lovlar: {stats.get('pending_payments', 0)}
└ 📚 Kurslar: {stats.get('total_courses', 0)}

⬇️ Quyidagi menyudan tanlang:
"""

    await call.message.edit_text(text, reply_markup=None)
    await call.answer()


@dp.callback_query_handler(text="admin:courses")
async def callback_admin_courses(call: types.CallbackQuery):
    """Kurslar menyusi callback"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    text = """
📚 <b>Kurslar boshqaruvi</b>

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=courses_menu())
    await call.answer()


@dp.callback_query_handler(text="admin:users")
async def callback_admin_users(call: types.CallbackQuery):
    """Foydalanuvchilar menyusi callback"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    total_users = user_db.count_users()

    text = f"""
👥 <b>Foydalanuvchilar boshqaruvi</b>

📊 Jami: {total_users} ta foydalanuvchi

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=users_menu())
    await call.answer()


@dp.callback_query_handler(text="admin:payments")
async def callback_admin_payments(call: types.CallbackQuery):
    """To'lovlar menyusi callback"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    pending_count = user_db.count_pending_payments()

    text = f"""
💰 <b>To'lovlar boshqaruvi</b>

📥 Kutilayotgan: {pending_count} ta

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=payments_menu())
    await call.answer()


@dp.callback_query_handler(text="admin:reports")
async def callback_admin_reports(call: types.CallbackQuery):
    """Hisobotlar menyusi callback"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    text = """
📊 <b>Hisobotlar</b>

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=reports_menu())
    await call.answer()


@dp.callback_query_handler(text="admin:feedbacks")
async def callback_admin_feedbacks(call: types.CallbackQuery):
    """Fikrlar menyusi callback"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    text = """
💬 <b>Fikr-mulohazalar</b>

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=feedbacks_menu())
    await call.answer()


@dp.callback_query_handler(text="admin:settings")
async def callback_admin_settings(call: types.CallbackQuery):
    """Sozlamalar menyusi callback"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    text = """
⚙️ <b>Sozlamalar</b>

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=settings_menu())
    await call.answer()


@dp.callback_query_handler(text="admin:broadcast")
async def callback_admin_broadcast(call: types.CallbackQuery):
    """Ommaviy xabar menyusi callback"""
    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    text = """
📢 <b>Ommaviy xabar</b>

Kimga xabar yubormoqchisiz?

⬇️ Tanlang:
"""

    await call.message.edit_text(text, reply_markup=broadcast_menu())
    await call.answer()


@dp.callback_query_handler(text="admin:close")
async def callback_close(call: types.CallbackQuery, state: FSMContext):
    """Yopish callback"""
    await state.finish()
    await call.message.delete()
    await call.answer()


# ============================================================
#                    BEKOR QILISH HANDLER
# ============================================================

@dp.message_handler(Text(equals="❌ Bekor qilish"), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    """Bekor qilish - barcha statelardan chiqish"""
    current_state = await state.get_state()

    if current_state is None:
        return

    await state.finish()
    await message.answer(
        "❌ Bekor qilindi",
        reply_markup=admin_reply_menu() if user_db.is_admin(message.from_user.id) else None
    )