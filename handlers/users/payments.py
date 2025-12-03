"""
User Payments Handler
=====================
To'lov tarixi va holati handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from loader import dp, bot, user_db
from keyboards.inline.user_keyboards import back_button
from keyboards.default.user_keyboards import main_menu


# ============================================================
#                    TO'LOVLARIM
# ============================================================

@dp.message_handler(Text(equals="💳 To'lovlarim"))
async def my_payments(message: types.Message):
    """Mening to'lovlarim"""
    telegram_id = message.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    if not user_id:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start")
        return

    # To'lovlar
    payments = user_db.execute(
        """SELECT p.id, p.amount, p.status, p.created_at, c.name
           FROM Payments p
           JOIN Courses c ON p.course_id = c.id
           WHERE p.user_id = ?
           ORDER BY p.created_at DESC
           LIMIT 20""",
        parameters=(user_id,),
        fetchall=True
    )

    if not payments:
        text = """
💳 <b>Mening to'lovlarim</b>

📭 Sizda hozircha to'lovlar yo'q.

Kurs sotib olish uchun "🛒 Kurs sotib olish" tugmasini bosing.
"""
        await message.answer(text, reply_markup=main_menu())
        return

    # Statistika
    total_paid = user_db.execute(
        """SELECT SUM(amount) FROM Payments 
           WHERE user_id = ? AND status = 'approved'""",
        parameters=(user_id,),
        fetchone=True
    )

    pending_count = user_db.execute(
        """SELECT COUNT(*) FROM Payments 
           WHERE user_id = ? AND status = 'pending'""",
        parameters=(user_id,),
        fetchone=True
    )

    status_icons = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌'
    }

    status_names = {
        'pending': 'Kutilmoqda',
        'approved': 'Tasdiqlangan',
        'rejected': 'Rad etilgan'
    }

    text = f"""
💳 <b>Mening to'lovlarim</b>

💰 Jami to'langan: <b>{total_paid[0]:,.0f if total_paid and total_paid[0] else 0}</b> so'm
⏳ Kutilayotgan: <b>{pending_count[0] if pending_count else 0}</b> ta

<b>So'nggi to'lovlar:</b>

"""

    for p in payments:
        icon = status_icons.get(p[2], '❓')
        status = status_names.get(p[2], p[2])
        date = p[3][:10] if p[3] else ""

        text += f"{icon} <b>{p[4]}</b>\n"
        text += f"   💵 {p[1]:,.0f} so'm | {status}\n"
        text += f"   📅 {date}\n\n"

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    # Kutilayotgan to'lovlar bo'lsa
    if pending_count and pending_count[0] > 0:
        keyboard.add(types.InlineKeyboardButton(
            "⏳ Kutilayotgan to'lovlar",
            callback_data="user:payments:pending"
        ))

    keyboard.add(types.InlineKeyboardButton(
        "🛒 Yangi kurs sotib olish",
        callback_data="user:courses"
    ))

    await message.answer(text, reply_markup=keyboard)


# ============================================================
#                    KUTILAYOTGAN TO'LOVLAR
# ============================================================

@dp.callback_query_handler(text="user:payments:pending")
async def show_pending_payments(call: types.CallbackQuery):
    """Kutilayotgan to'lovlar"""
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    payments = user_db.execute(
        """SELECT p.id, p.amount, p.created_at, c.name
           FROM Payments p
           JOIN Courses c ON p.course_id = c.id
           WHERE p.user_id = ? AND p.status = 'pending'
           ORDER BY p.created_at DESC""",
        parameters=(user_id,),
        fetchall=True
    )

    if not payments:
        await call.answer("📭 Kutilayotgan to'lovlar yo'q", show_alert=True)
        return

    text = f"""
⏳ <b>Kutilayotgan to'lovlar</b>

Sizda {len(payments)} ta kutilayotgan to'lov bor.

"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for p in payments:
        date = p[2][:10] if p[2] else ""
        text += f"📚 <b>{p[3]}</b>\n"
        text += f"   💵 {p[1]:,.0f} so'm | 📅 {date}\n\n"

        keyboard.add(types.InlineKeyboardButton(
            f"#{p[0]} - {p[3]}",
            callback_data=f"user:payment:view:{p[0]}"
        ))

    text += "\n⏳ Admin tez orada tekshiradi. Sabr qiling!"

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:payments"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ============================================================
#                    TO'LOVNI KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="user:payment:view:")
async def view_payment(call: types.CallbackQuery):
    """To'lovni ko'rish"""
    payment_id = int(call.data.split(":")[-1])

    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    payment = user_db.execute(
        """SELECT p.id, p.amount, p.status, p.created_at, p.approved_at,
                  p.admin_note, c.name as course_name
           FROM Payments p
           JOIN Courses c ON p.course_id = c.id
           WHERE p.id = ? AND p.user_id = ?""",
        parameters=(payment_id, user_id),
        fetchone=True
    )

    if not payment:
        await call.answer("❌ To'lov topilmadi!", show_alert=True)
        return

    status_icons = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌'
    }

    status_names = {
        'pending': 'Kutilmoqda',
        'approved': 'Tasdiqlangan',
        'rejected': 'Rad etilgan'
    }

    icon = status_icons.get(payment[2], '❓')
    status = status_names.get(payment[2], payment[2])

    text = f"""
{icon} <b>To'lov #{payment[0]}</b>

📚 <b>Kurs:</b> {payment[6]}
💵 <b>Summa:</b> {payment[1]:,.0f} so'm
📊 <b>Holat:</b> {status}

📅 <b>Yuborilgan:</b> {payment[3][:16] if payment[3] else 'Nomalum'}
"""

    if payment[2] == 'approved':
        text += f"\n✅ <b>Tasdiqlangan:</b> {payment[4][:16] if payment[4] else ''}"
        text += "\n\n🎉 Kursga kirish ochilgan!"

    elif payment[2] == 'rejected':
        text += f"\n❌ <b>Rad etilgan:</b> {payment[4][:16] if payment[4] else ''}"
        if payment[5]:
            text += f"\n📝 <b>Sabab:</b> {payment[5]}"
        text += "\n\n⚠️ Iltimos, qaytadan to'lov qiling."

    else:
        text += "\n\n⏳ Admin tekshirmoqda. Iltimos, kuting..."

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    if payment[2] == 'rejected':
        # Qayta to'lash
        course_id = user_db.execute(
            "SELECT course_id FROM Payments WHERE id = ?",
            parameters=(payment_id,),
            fetchone=True
        )
        if course_id:
            keyboard.add(types.InlineKeyboardButton(
                "🔄 Qayta to'lash",
                callback_data=f"user:buy:{course_id[0]}"
            ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:payments:pending"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ============================================================
#                    TO'LOVLAR CALLBACK (inline menu uchun)
# ============================================================

@dp.callback_query_handler(text="user:payments")
async def show_payments_inline(call: types.CallbackQuery):
    """To'lovlarni inline ko'rsatish"""
    telegram_id = call.from_user.id
    user_id = user_db.get_user_id(telegram_id)

    if not user_id:
        await call.answer("❌ Avval ro'yxatdan o'ting!", show_alert=True)
        return

    # To'lovlar
    payments = user_db.execute(
        """SELECT p.id, p.amount, p.status, p.created_at, c.name
           FROM Payments p
           JOIN Courses c ON p.course_id = c.id
           WHERE p.user_id = ?
           ORDER BY p.created_at DESC
           LIMIT 10""",
        parameters=(user_id,),
        fetchall=True
    )

    if not payments:
        text = """
💳 <b>Mening to'lovlarim</b>

📭 Sizda hozircha to'lovlar yo'q.
"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🛒 Kurs sotib olish",
            callback_data="user:courses"
        ))
        keyboard.add(types.InlineKeyboardButton(
            "⬅️ Orqaga",
            callback_data="user:main"
        ))

        await call.message.edit_text(text, reply_markup=keyboard)
        await call.answer()
        return

    status_icons = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌'
    }

    text = f"""
💳 <b>Mening to'lovlarim</b>

So'nggi {len(payments)} ta to'lov:

"""

    for p in payments:
        icon = status_icons.get(p[2], '❓')
        date = p[3][:10] if p[3] else ""
        text += f"{icon} {p[4]} | {p[1]:,.0f} | {date}\n"

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:main"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()