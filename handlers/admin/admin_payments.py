"""
Admin Payments Handler
======================
To'lovlarni boshqarish handlerlari (FINAL)
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from datetime import datetime, timedelta

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import (
    payments_menu,
    back_button,
    confirm_action
)
from keyboards.default.admin_keyboards import admin_cancel_button, remove_keyboard
from states.admin_states import PaymentStates
from handlers.admin.admin_start import admin_required


# ============================================================
#                    TO'LOVLAR MENYUSI
# ============================================================

@dp.callback_query_handler(text="admin:payments")
@admin_required
async def show_payments_menu(call: types.CallbackQuery):
    """To'lovlar menyusi"""

    # Statistika
    pending = user_db.execute(
        "SELECT COUNT(*) FROM Payments WHERE status = 'pending'",
        fetchone=True
    )
    approved = user_db.execute(
        "SELECT COUNT(*) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )
    rejected = user_db.execute(
        "SELECT COUNT(*) FROM Payments WHERE status = 'rejected'",
        fetchone=True
    )

    # Bugungi daromad
    today = datetime.now().strftime('%Y-%m-%d')
    today_income = user_db.execute(
        """SELECT SUM(amount) FROM Payments 
           WHERE status = 'approved' AND DATE(approved_at) = ?""",
        parameters=(today,),
        fetchone=True
    )

    pending_count = pending[0] if pending else 0
    approved_count = approved[0] if approved else 0
    rejected_count = rejected[0] if rejected else 0
    today_sum = today_income[0] if today_income and today_income[0] else 0

    text = f"""
💰 <b>To'lovlar boshqaruvi</b>

📊 <b>Statistika:</b>
├ ⏳ Kutilayotgan: <b>{pending_count}</b>
├ ✅ Tasdiqlangan: <b>{approved_count}</b>
└ ❌ Rad etilgan: <b>{rejected_count}</b>

💵 Bugungi daromad: <b>{today_sum:,.0f}</b> so'm

⬇️ Bo'limni tanlang:
"""

    await call.message.edit_text(text, reply_markup=payments_menu())
    await call.answer()


# ============================================================
#                    KUTILAYOTGAN TO'LOVLAR
# ============================================================

@dp.callback_query_handler(text="admin:payments:pending")
@admin_required
async def show_pending_payments(call: types.CallbackQuery):
    """Kutilayotgan to'lovlar"""

    payments = user_db.execute(
        """SELECT p.id, p.amount, p.created_at, 
                  u.full_name, u.phone, u.telegram_id,
                  c.name as course_name
           FROM Payments p
           JOIN Users u ON p.user_id = u.id
           JOIN Courses c ON p.course_id = c.id
           WHERE p.status = 'pending'
           ORDER BY p.created_at ASC""",
        fetchall=True
    )

    if not payments:
        await call.answer("📭 Kutilayotgan to'lovlar yo'q", show_alert=True)
        return

    text = f"""
⏳ <b>Kutilayotgan to'lovlar</b>

Jami: {len(payments)} ta

"""

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for p in payments[:10]:  # Faqat 10 ta ko'rsatish
        date = p[2][:10] if p[2] else ""
        keyboard.add(types.InlineKeyboardButton(
            f"#{p[0]} | {p[3]} | {p[1]:,.0f} so'm",
            callback_data=f"admin:payment:view:{p[0]}"
        ))

    if len(payments) > 10:
        text += f"\n<i>Faqat 10 ta ko'rsatilmoqda. Jami: {len(payments)}</i>"

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:payments"
    ))

    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ============================================================
#                    TO'LOVNI KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:payment:view:")
@admin_required
async def view_payment(call: types.CallbackQuery):
    """To'lovni ko'rish"""
    payment_id = int(call.data.split(":")[-1])

    payment = user_db.execute(
        """SELECT p.*, u.full_name, u.phone, u.telegram_id, u.username,
                  c.name as course_name
           FROM Payments p
           JOIN Users u ON p.user_id = u.id
           JOIN Courses c ON p.course_id = c.id
           WHERE p.id = ?""",
        parameters=(payment_id,),
        fetchone=True
    )

    if not payment:
        await call.answer("❌ To'lov topilmadi!", show_alert=True)
        return

    # payment tuple:
    # 0-id, 1-user_id, 2-course_id, 3-amount, 4-receipt_file_id, 5-status
    # 6-admin_id, 7-admin_note, 8-created_at, 9-updated_at
    # 10-full_name, 11-phone, 12-telegram_id, 13-username, 14-course_name

    status_map = {
        'pending': '⏳ Kutilmoqda',
        'approved': '✅ Tasdiqlangan',
        'rejected': '❌ Rad etilgan'
    }

    status_text = status_map.get(payment[5], payment[5])

    text = f"""
💰 <b>To'lov #{payment[0]}</b>

<b>Status:</b> {status_text}

👤 <b>Foydalanuvchi:</b>
├ Ism: {payment[10]}
├ Telefon: {payment[11] or 'Yoq'}
├ Username: @{payment[13] or 'yoq'}
└ ID: <code>{payment[12]}</code>

📚 <b>Kurs:</b> {payment[14]}
💵 <b>Summa:</b> {payment[3]:,.0f} so'm

📅 <b>Yuborilgan:</b> {payment[8][:16] if payment[8] else 'Nomalum'}
"""

    if payment[5] == 'approved':
        text += f"\n✅ <b>Tasdiqlangan:</b> {payment[9][:16] if payment[9] else ''}"
    elif payment[5] == 'rejected' and payment[7]:
        text += f"\n❌ <b>Sabab:</b> {payment[7]}"

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # Chekni ko'rish
    if payment[4]:
        keyboard.add(types.InlineKeyboardButton(
            "🧾 Chekni ko'rish",
            callback_data=f"admin:payment:receipt:{payment_id}"
        ))

    # Agar kutilayotgan bo'lsa
    if payment[5] == 'pending':
        keyboard.add(
            types.InlineKeyboardButton(
                "✅ Tasdiqlash",
                callback_data=f"admin:payment:approve:{payment_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Rad etish",
                callback_data=f"admin:payment:reject:{payment_id}"
            )
        )

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:payments:pending"
    ))

    # Agar xabar rasm bo'lsa, o'chirib yangi yuboramiz
    try:
        await call.message.edit_text(text, reply_markup=keyboard)
    except:
        # Rasm xabarini o'chirib, yangi text yuboramiz
        try:
            await call.message.delete()
        except:
            pass
        await bot.send_message(call.from_user.id, text, reply_markup=keyboard)

    await call.answer()


# ============================================================
#                    CHEKNI KO'RISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:payment:receipt:")
@admin_required
async def view_receipt(call: types.CallbackQuery):
    """Chekni ko'rish"""
    payment_id = int(call.data.split(":")[-1])

    payment = user_db.execute(
        "SELECT receipt_file_id FROM Payments WHERE id = ?",
        parameters=(payment_id,),
        fetchone=True
    )

    if not payment or not payment[0]:
        await call.answer("❌ Chek topilmadi!", show_alert=True)
        return

    await call.answer("📸 Chek yuborilmoqda...")

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Tasdiqlash",
            callback_data=f"admin:payment:approve:{payment_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Rad etish",
            callback_data=f"admin:payment:reject:{payment_id}"
        )
    )
    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:payment:view:{payment_id}"
    ))

    try:
        await bot.send_photo(
            call.from_user.id,
            payment[0],
            caption=f"🧾 To'lov cheki #{payment_id}",
            reply_markup=keyboard
        )
    except:
        # Agar rasm bo'lmasa, document sifatida
        try:
            await bot.send_document(
                call.from_user.id,
                payment[0],
                caption=f"🧾 To'lov cheki #{payment_id}",
                reply_markup=keyboard
            )
        except Exception as e:
            await call.message.answer(f"❌ Chekni yuborishda xato: {e}")


# ============================================================
#                    TO'LOVNI TASDIQLASH (FINAL)
# ============================================================

@dp.callback_query_handler(text_startswith="admin:payment:approve:")
@admin_required
async def approve_payment(call: types.CallbackQuery):
    """To'lovni tasdiqlash"""
    payment_id = int(call.data.split(":")[-1])

    # 1. Bazadan ma'lumot olish
    # p.user_id -> index 1 (Bu bazadagi ichki ID)
    # u.telegram_id -> index 6 (Bu Telegram ID)
    payment = user_db.execute(
        """SELECT p.id, p.user_id, p.course_id, p.amount, p.receipt_file_id,
                  p.status, u.telegram_id, c.name as course_name, 
                  p.admin_id
           FROM Payments p
           JOIN Users u ON p.user_id = u.id
           JOIN Courses c ON p.course_id = c.id
           WHERE p.id = ?""",
        parameters=(payment_id,),
        fetchone=True
    )

    if not payment:
        await call.answer("❌ To'lov topilmadi!", show_alert=True)
        try:
            await call.message.delete()
        except:
            pass
        return

    # 2. Status tekshirish (Poyga holati)
    if payment[5] != 'pending':
        admin_name = "Boshqa admin"
        if payment[8]:
            admin_data = user_db.execute("SELECT name FROM Admins WHERE user_id = ?", (payment[8],), fetchone=True)
            if admin_data: admin_name = admin_data[0]

        status_text = "Tasdiqlangan ✅" if payment[5] == 'approved' else "Rad etilgan ❌"
        await call.answer(f"⚠️ Kech qoldingiz! {admin_name} tomonidan {status_text}!", show_alert=True)
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except:
            pass
        return

    # 3. Tasdiqlash
    result = user_db.approve_payment(payment_id, call.from_user.id)
    if not result:
        await call.answer("❌ Xatolik yuz berdi!", show_alert=True)
        return

    # 4. Admin xabarini yangilash
    await call.message.edit_caption(
        caption=call.message.caption + f"\n\n✅ <b>{call.from_user.full_name} tomonidan tasdiqlandi!</b>",
        reply_markup=None
    )
    await call.answer("✅ To'lov tasdiqlandi!", show_alert=True)

    # 5. Userga xabar (Telegram ID: payment[6])
    try:
        user_text = f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n📚 Kurs: {payment[7]}\n💰 Summa: {payment[3]:,.0f} so'm\n\n✅ Darslarni boshlashingiz mumkin!"
        user_kb = types.InlineKeyboardMarkup()
        user_kb.add(types.InlineKeyboardButton("📚 Darslarni ko'rish", callback_data="user:lessons"))
        await bot.send_message(payment[6], user_text, reply_markup=user_kb)
    except:
        pass

    # 6. REFERAL CASHBACK VA ADMINLARGA ESLATMA
    try:
        # Bazadagi user ID (payment[1]) ni yuboramiz.
        # Chunki bazada referal munosabatlari user_id bo'yicha bog'langan.
        ref_result = user_db.convert_referral(payment[1], payment[3])

        if ref_result['success']:
            referrer_tg_id = ref_result['referrer_tg_id']
            referrer_name = ref_result['referrer_name']
            referrer_phone = ref_result['referrer_phone']
            cashback_amount = ref_result['amount']

            cashback_text = f"{cashback_amount:,.0f}".replace(",", " ")

            # A) Foydalanuvchiga (Taklif qilganga) xabar
            try:
                await bot.send_message(
                    referrer_tg_id,
                    f"🎉 <b>Tabriklaymiz!</b>\n\n"
                    f"Siz taklif qilgan do'stingiz kurs sotib oldi!\n\n"
                    f"💰 Sizga <b>{cashback_text} so'm</b> mukofot yozildi.\n\n"
                    f"📞 Tez orada adminlarimiz bog'lanib, pulni kartangizga o'tkazib berishadi."
                )
            except:
                pass

            # B) Adminlarga eslatma
            admin_alert = (
                f"⚠️ <b>DIQQAT! CASHBACK TO'LASH KERAK!</b>\n\n"
                f"👤 Kimga: <b>{referrer_name}</b>\n"
                f"📞 Tel: <code>{referrer_phone}</code>\n"
                f"🆔 ID: <code>{referrer_tg_id}</code>\n\n"
                f"💵 To'lanishi kerak: <b>{cashback_text} so'm</b>\n\n"
                f"✅ <i>Iltimos, bog'lanib, pulni to'lab bering.</i>"
            )

            # Hozirgi adminga
            await call.message.answer(admin_alert)

            # Barcha adminlarga (o'zidan tashqari)
            try:
                all_admins = user_db.get_notification_admins()
                for admin_id in all_admins:
                    if admin_id != call.from_user.id:
                        try:
                            await bot.send_message(admin_id, admin_alert)
                        except:
                            pass
            except:
                pass

    except Exception as e:
        print(f"Referal Handler Xato: {e}")


# ============================================================
#                    TO'LOVNI RAD ETISH
# ============================================================

@dp.callback_query_handler(text_startswith="admin:payment:reject:")
async def reject_payment_start(call: types.CallbackQuery, state: FSMContext):
    """To'lovni rad etish - sabab so'rash"""

    if not user_db.is_admin(call.from_user.id):
        await call.answer("⛔️ Sizda admin huquqi yo'q!", show_alert=True)
        return

    payment_id = int(call.data.split(":")[-1])

    # 1. Statusni qayta tekshiramiz
    payment = user_db.execute(
        "SELECT status FROM Payments WHERE id = ?",
        parameters=(payment_id,),
        fetchone=True
    )

    if not payment:
        await call.answer("❌ To'lov topilmadi!", show_alert=True)
        try:
            await call.message.delete()
        except:
            pass
        return

    # 2. Agar pending bo'lmasa, demak kimdir ulgurdi
    if payment[0] != 'pending':
        status_text = "Tasdiqlangan ✅" if payment[0] == 'approved' else "Rad etilgan ❌"
        await call.answer(f"⚠️ Kech qoldingiz! Bu to'lov allaqachon {status_text}!", show_alert=True)

        # Tugmalarni olib tashlaymiz
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except:
            pass
        return

    await state.update_data(payment_id=payment_id)

    # 3. Sabab so'rash xabarini chiqaramiz
    try:
        await call.message.delete()
    except:
        pass

    await bot.send_message(
        call.from_user.id,
        f"❌ <b>To'lovni rad etish</b>\n\n"
        f"To'lov: #{payment_id}\n\n"
        f"📝 Rad etish sababini kiriting:"
    )

    await call.message.answer(
        "✍️ Sababni yozing:",
        reply_markup=admin_cancel_button()
    )

    await PaymentStates.reject_reason.set()
    await call.answer()


@dp.message_handler(state=PaymentStates.reject_reason)
async def reject_payment_reason(message: types.Message, state: FSMContext):
    """Rad etish sababini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    reason = message.text.strip()

    if len(reason) < 3:
        await message.answer("❌ Sabab juda qisqa!")
        return

    data = await state.get_data()
    payment_id = data['payment_id']

    payment = user_db.execute(
        """SELECT p.user_id, u.telegram_id, c.name as course_name, p.amount
           FROM Payments p
           JOIN Users u ON p.user_id = u.id
           JOIN Courses c ON p.course_id = c.id
           WHERE p.id = ?""",
        parameters=(payment_id,),
        fetchone=True
    )

    if not payment:
        await state.finish()
        await message.answer("❌ To'lov topilmadi!", reply_markup=remove_keyboard())
        return

    # To'lovni rad etish
    result = user_db.reject_payment(payment_id, message.from_user.id, reason)

    await state.finish()

    await message.answer(
        f"❌ To'lov #{payment_id} rad etildi!\n\nSabab: {reason}",
        reply_markup=remove_keyboard()
    )

    # Foydalanuvchiga xabar
    try:
        user_text = f"""
❌ <b>To'lovingiz rad etildi</b>

📚 Kurs: {payment[2]}
💰 Summa: {payment[3]:,.0f} so'm

📝 <b>Sabab:</b> {reason}

Iltimos, qaytadan to'g'ri to'lov qiling yoki admin bilan bog'laning.
"""
        await bot.send_message(payment[1], user_text)  # telegram_id
    except Exception as e:
        print(f"Foydalanuvchiga xabar yuborib bo'lmadi: {e}")


# ============================================================
#                    TASDIQLANGAN TO'LOVLAR
# ============================================================

@dp.callback_query_handler(text="admin:payments:approved")
@admin_required
async def show_approved_payments(call: types.CallbackQuery):
    """Tasdiqlangan to'lovlar"""

    payments = user_db.execute(
        """SELECT p.id, p.amount, p.approved_at, u.full_name, c.name
           FROM Payments p
           JOIN Users u ON p.user_id = u.id
           JOIN Courses c ON p.course_id = c.id
           WHERE p.status = 'approved'
           ORDER BY p.approved_at DESC
           LIMIT 20""",
        fetchall=True
    )

    if not payments:
        await call.answer("📭 Tasdiqlangan to'lovlar yo'q", show_alert=True)
        return

    text = f"""
✅ <b>Tasdiqlangan to'lovlar</b>

So'nggi 20 ta:

"""

    total = 0
    for p in payments:
        date = p[2][:10] if p[2] else ""
        text += f"#{p[0]} | {p[3]} | {p[1]:,.0f} | {date}\n"
        total += p[1]

    text += f"\n💰 <b>Jami:</b> {total:,.0f} so'm"

    await call.message.edit_text(text, reply_markup=back_button("admin:payments"))
    await call.answer()


# ============================================================
#                    RAD ETILGAN TO'LOVLAR
# ============================================================

@dp.callback_query_handler(text="admin:payments:rejected")
@admin_required
async def show_rejected_payments(call: types.CallbackQuery):
    """Rad etilgan to'lovlar"""

    payments = user_db.execute(
        """SELECT p.id, p.amount, p.approved_at, u.full_name, p.admin_note
           FROM Payments p
           JOIN Users u ON p.user_id = u.id
           WHERE p.status = 'rejected'
           ORDER BY p.approved_at DESC
           LIMIT 20""",
        fetchall=True
    )

    if not payments:
        await call.answer("📭 Rad etilgan to'lovlar yo'q", show_alert=True)
        return

    text = f"""
❌ <b>Rad etilgan to'lovlar</b>

So'nggi 20 ta:

"""

    for p in payments:
        date = p[2][:10] if p[2] else ""
        reason = p[4][:30] + "..." if p[4] and len(p[4]) > 30 else (p[4] or "")
        text += f"#{p[0]} | {p[3]} | {p[1]:,.0f}\n   └ {reason}\n"

    await call.message.edit_text(text, reply_markup=back_button("admin:payments"))
    await call.answer()


# ============================================================
#                    TO'LOVLAR STATISTIKASI
# ============================================================

@dp.callback_query_handler(text="admin:payments:stats")
@admin_required
async def show_payments_stats(call: types.CallbackQuery):
    """To'lovlar statistikasi"""

    # Umumiy
    total = user_db.execute(
        "SELECT COUNT(*), SUM(amount) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    # Bugun
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = user_db.execute(
        """SELECT COUNT(*), SUM(amount) FROM Payments 
           WHERE status = 'approved' AND DATE(approved_at) = ?""",
        parameters=(today,),
        fetchone=True
    )

    # Shu hafta
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_stats = user_db.execute(
        """SELECT COUNT(*), SUM(amount) FROM Payments 
           WHERE status = 'approved' AND DATE(approved_at) >= ?""",
        parameters=(week_ago,),
        fetchone=True
    )

    # Shu oy
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    month_stats = user_db.execute(
        """SELECT COUNT(*), SUM(amount) FROM Payments 
           WHERE status = 'approved' AND DATE(approved_at) >= ?""",
        parameters=(month_start,),
        fetchone=True
    )

    # O'rtacha chek
    avg = user_db.execute(
        "SELECT AVG(amount) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    text = f"""
📊 <b>To'lovlar statistikasi</b>

💰 <b>Umumiy:</b>
├ To'lovlar: {total[0] if total else 0}
└ Summa: {total[1]:,.0f if total and total[1] else 0} so'm

📅 <b>Bugun:</b>
├ To'lovlar: {today_stats[0] if today_stats else 0}
└ Summa: {today_stats[1]:,.0f if today_stats and today_stats[1] else 0} so'm

📆 <b>Shu hafta:</b>
├ To'lovlar: {week_stats[0] if week_stats else 0}
└ Summa: {week_stats[1]:,.0f if week_stats and week_stats[1] else 0} so'm

🗓 <b>Shu oy:</b>
├ To'lovlar: {month_stats[0] if month_stats else 0}
└ Summa: {month_stats[1]:,.0f if month_stats and month_stats[1] else 0} so'm

📈 <b>O'rtacha chek:</b> {avg[0]:,.0f if avg and avg[0] else 0} so'm
"""

    await call.message.edit_text(text, reply_markup=back_button("admin:payments"))
    await call.answer()