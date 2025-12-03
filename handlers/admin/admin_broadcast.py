"""
Admin Broadcast Handler
=======================
Ommaviy xabar yuborish handlerlari
"""

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
import asyncio

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import broadcast_menu, back_button
from keyboards.default.admin_keyboards import admin_cancel_button, admin_confirm_keyboard, admin_skip_button, \
    remove_keyboard
from states.admin_states import BroadcastStates
from handlers.admin.admin_start import admin_required


# ============================================================
#                    BROADCAST MENYUSI
# ============================================================

@dp.callback_query_handler(text="admin:broadcast")
@admin_required
async def show_broadcast_menu(call: types.CallbackQuery):
    """Broadcast menyusi"""

    # Statistika
    total_users = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)
    paid_users = user_db.execute(
        "SELECT COUNT(DISTINCT user_id) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    total = total_users[0] if total_users else 0
    paid = paid_users[0] if paid_users else 0
    free = total - paid

    text = f"""
📢 <b>Ommaviy xabar yuborish</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: <b>{total}</b>
├ Pullik: <b>{paid}</b>
└ Bepul: <b>{free}</b>

⬇️ Kimga yubormoqchisiz?
"""

    await call.message.edit_text(text, reply_markup=broadcast_menu())
    await call.answer()


# ============================================================
#                    BARCHAGA YUBORISH
# ============================================================

@dp.callback_query_handler(text="admin:broadcast:all")
@admin_required
async def broadcast_all_start(call: types.CallbackQuery, state: FSMContext):
    """Barchaga xabar - boshlash"""

    total = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)

    await state.update_data(
        target='all',
        target_name='Barcha foydalanuvchilar',
        target_count=total[0] if total else 0
    )

    await call.message.edit_text(
        f"📢 <b>Barchaga xabar yuborish</b>\n\n"
        f"👥 Qabul qiluvchilar: <b>{total[0] if total else 0}</b> ta\n\n"
        f"📝 Xabar matnini kiriting:"
    )

    await call.message.answer(
        "✍️ Xabar yozing:",
        reply_markup=admin_cancel_button()
    )

    await BroadcastStates.message_text.set()
    await call.answer()


# ============================================================
#                    PULLIK FOYDALANUVCHILARGA
# ============================================================

@dp.callback_query_handler(text="admin:broadcast:paid")
@admin_required
async def broadcast_paid_start(call: types.CallbackQuery, state: FSMContext):
    """Pullik foydalanuvchilarga xabar"""

    count = user_db.execute(
        "SELECT COUNT(DISTINCT user_id) FROM Payments WHERE status = 'approved'",
        fetchone=True
    )

    if not count or count[0] == 0:
        await call.answer("📭 Pullik foydalanuvchilar yo'q", show_alert=True)
        return

    await state.update_data(
        target='paid',
        target_name='Pullik foydalanuvchilar',
        target_count=count[0]
    )

    await call.message.edit_text(
        f"📢 <b>Pullik foydalanuvchilarga xabar</b>\n\n"
        f"👥 Qabul qiluvchilar: <b>{count[0]}</b> ta\n\n"
        f"📝 Xabar matnini kiriting:"
    )

    await call.message.answer(
        "✍️ Xabar yozing:",
        reply_markup=admin_cancel_button()
    )

    await BroadcastStates.message_text.set()
    await call.answer()


# ============================================================
#                    BEPUL FOYDALANUVCHILARGA
# ============================================================

@dp.callback_query_handler(text="admin:broadcast:free")
@admin_required
async def broadcast_free_start(call: types.CallbackQuery, state: FSMContext):
    """Bepul foydalanuvchilarga xabar"""

    count = user_db.execute(
        """SELECT COUNT(*) FROM Users u
           WHERE NOT EXISTS (
               SELECT 1 FROM Payments p 
               WHERE p.user_id = u.id AND p.status = 'approved'
           )""",
        fetchone=True
    )

    if not count or count[0] == 0:
        await call.answer("📭 Bepul foydalanuvchilar yo'q", show_alert=True)
        return

    await state.update_data(
        target='free',
        target_name='Bepul foydalanuvchilar',
        target_count=count[0]
    )

    await call.message.edit_text(
        f"📢 <b>Bepul foydalanuvchilarga xabar</b>\n\n"
        f"👥 Qabul qiluvchilar: <b>{count[0]}</b> ta\n\n"
        f"📝 Xabar matnini kiriting:"
    )

    await call.message.answer(
        "✍️ Xabar yozing:",
        reply_markup=admin_cancel_button()
    )

    await BroadcastStates.message_text.set()
    await call.answer()


# ============================================================
#                    KURS BO'YICHA
# ============================================================

@dp.callback_query_handler(text="admin:broadcast:course")
@admin_required
async def broadcast_course_select(call: types.CallbackQuery, state: FSMContext):
    """Kurs tanlash"""

    courses = user_db.get_all_courses(active_only=True)

    if not courses:
        await call.answer("📭 Kurslar yo'q", show_alert=True)
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    for course in courses:
        # O'quvchilar soni
        count = user_db.execute(
            """SELECT COUNT(DISTINCT user_id) FROM Payments 
               WHERE course_id = ? AND status = 'approved'""",
            parameters=(course['id'],),
            fetchone=True
        )

        keyboard.add(types.InlineKeyboardButton(
            f"📚 {course['name']} ({count[0] if count else 0} ta)",
            callback_data=f"admin:broadcast:course:{course['id']}"
        ))

    keyboard.add(types.InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:broadcast"
    ))

    await call.message.edit_text(
        "📚 <b>Kurs tanlang</b>\n\n"
        "Qaysi kurs o'quvchilariga xabar yubormoqchisiz?",
        reply_markup=keyboard
    )
    await call.answer()


@dp.callback_query_handler(text_startswith="admin:broadcast:course:")
@admin_required
async def broadcast_course_start(call: types.CallbackQuery, state: FSMContext):
    """Kurs o'quvchilariga xabar"""
    course_id = int(call.data.split(":")[-1])

    course = user_db.get_course(course_id)

    if not course:
        await call.answer("❌ Kurs topilmadi!", show_alert=True)
        return

    count = user_db.execute(
        """SELECT COUNT(DISTINCT user_id) FROM Payments 
           WHERE course_id = ? AND status = 'approved'""",
        parameters=(course_id,),
        fetchone=True
    )

    if not count or count[0] == 0:
        await call.answer("📭 Bu kursda o'quvchilar yo'q", show_alert=True)
        return

    await state.update_data(
        target='course',
        target_id=course_id,
        target_name=f"'{course['name']}' kursi o'quvchilari",
        target_count=count[0]
    )

    await call.message.edit_text(
        f"📢 <b>Kurs o'quvchilariga xabar</b>\n\n"
        f"📚 Kurs: {course['name']}\n"
        f"👥 Qabul qiluvchilar: <b>{count[0]}</b> ta\n\n"
        f"📝 Xabar matnini kiriting:"
    )

    await call.message.answer(
        "✍️ Xabar yozing:",
        reply_markup=admin_cancel_button()
    )

    await BroadcastStates.message_text.set()
    await call.answer()


# ============================================================
#                    XABAR MATNI
# ============================================================

@dp.message_handler(state=BroadcastStates.message_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    """Xabar matnini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    text = message.text.strip()

    if len(text) < 5:
        await message.answer("❌ Xabar juda qisqa!")
        return

    if len(text) > 4000:
        await message.answer("❌ Xabar juda uzun! 4000 belgidan kam bo'lsin.")
        return

    await state.update_data(message_text=text)

    await message.answer(
        "📸 Rasm yoki video qo'shmoqchimisiz?\n\n"
        "Media yuboring yoki o'tkazib yuboring:",
        reply_markup=admin_skip_button()
    )

    await BroadcastStates.message_media.set()


# ============================================================
#                    MEDIA
# ============================================================

@dp.message_handler(state=BroadcastStates.message_media, content_types=['photo', 'video'])
async def broadcast_media(message: types.Message, state: FSMContext):
    """Media qabul qilish"""

    if message.photo:
        media_type = 'photo'
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = 'video'
        media_id = message.video.file_id
    else:
        await message.answer("❌ Faqat rasm yoki video yuboring!")
        return

    await state.update_data(
        media_type=media_type,
        media_id=media_id
    )

    # Tasdiqlash
    await show_broadcast_confirm(message, state)


@dp.message_handler(state=BroadcastStates.message_media)
async def broadcast_skip_media(message: types.Message, state: FSMContext):
    """Media o'tkazib yuborish"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    if message.text == "⏩ O'tkazib yuborish":
        await state.update_data(media_type=None, media_id=None)
        await show_broadcast_confirm(message, state)
    else:
        await message.answer("⏩ O'tkazib yuborish yoki media yuboring")


# ============================================================
#                    TASDIQLASH
# ============================================================

async def show_broadcast_confirm(message: types.Message, state: FSMContext):
    """Tasdiqlash ko'rsatish"""
    data = await state.get_data()

    text = f"""
📢 <b>Xabar yuborishni tasdiqlang</b>

👥 <b>Kimga:</b> {data['target_name']}
📊 <b>Soni:</b> {data['target_count']} ta
📎 <b>Media:</b> {'Bor' if data.get('media_type') else 'Yoq'}

📝 <b>Xabar:</b>
{data['message_text'][:500]}{'...' if len(data['message_text']) > 500 else ''}

✅ Yuborishni tasdiqlaysizmi?
"""

    await message.answer(text, reply_markup=admin_confirm_keyboard())
    await BroadcastStates.confirm.set()


@dp.message_handler(state=BroadcastStates.confirm)
async def broadcast_confirm(message: types.Message, state: FSMContext):
    """Yuborishni tasdiqlash"""
    if message.text == "❌ Yo'q" or message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    if message.text != "✅ Ha":
        await message.answer("✅ Ha yoki ❌ Yo'q tugmasini bosing")
        return

    data = await state.get_data()

    await state.finish()

    # Foydalanuvchilarni olish
    if data['target'] == 'all':
        users = user_db.execute(
            "SELECT telegram_id FROM Users",
            fetchall=True
        )
    elif data['target'] == 'paid':
        users = user_db.execute(
            """SELECT DISTINCT u.telegram_id FROM Users u
               JOIN Payments p ON u.id = p.user_id
               WHERE p.status = 'approved'""",
            fetchall=True
        )
    elif data['target'] == 'free':
        users = user_db.execute(
            """SELECT telegram_id FROM Users u
               WHERE NOT EXISTS (
                   SELECT 1 FROM Payments p 
                   WHERE p.user_id = u.id AND p.status = 'approved'
               )""",
            fetchall=True
        )
    elif data['target'] == 'course':
        users = user_db.execute(
            """SELECT DISTINCT u.telegram_id FROM Users u
               JOIN Payments p ON u.id = p.user_id
               WHERE p.course_id = ? AND p.status = 'approved'""",
            parameters=(data['target_id'],),
            fetchall=True
        )
    else:
        users = []

    if not users:
        await message.answer("📭 Foydalanuvchilar topilmadi!", reply_markup=remove_keyboard())
        return

    # Yuborish
    progress_msg = await message.answer(
        f"📤 Yuborilmoqda...\n"
        f"0/{len(users)}",
        reply_markup=remove_keyboard()
    )

    success = 0
    failed = 0

    for i, user in enumerate(users, 1):
        try:
            if data.get('media_type') == 'photo':
                await bot.send_photo(
                    user[0],
                    data['media_id'],
                    caption=data['message_text']
                )
            elif data.get('media_type') == 'video':
                await bot.send_video(
                    user[0],
                    data['media_id'],
                    caption=data['message_text']
                )
            else:
                await bot.send_message(user[0], data['message_text'])

            success += 1
        except Exception as e:
            failed += 1

        # Har 10 ta xabarda progress yangilash
        if i % 10 == 0 or i == len(users):
            try:
                await progress_msg.edit_text(
                    f"📤 Yuborilmoqda...\n"
                    f"{i}/{len(users)}\n\n"
                    f"✅ Muvaffaqiyatli: {success}\n"
                    f"❌ Xato: {failed}"
                )
            except:
                pass

        # Telegram limitlarini hurmat qilish
        await asyncio.sleep(0.05)  # 20 ta/sekund

    # Yakuniy natija
    await progress_msg.edit_text(
        f"📢 <b>Xabar yuborildi!</b>\n\n"
        f"👥 Jami: {len(users)}\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xato: {failed}"
    )