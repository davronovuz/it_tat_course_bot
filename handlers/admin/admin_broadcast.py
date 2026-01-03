"""
Admin Broadcast Handler (Ultimate Version)
==========================================
Birlashtirilgan: Tezkor, Rejalashtiriladigan va Boshqariladigan tizim.
"""

import asyncio
from datetime import datetime, timedelta
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import exceptions

from loader import dp, bot, user_db
from keyboards.inline.admin_keyboards import broadcast_menu, back_button
from keyboards.default.admin_keyboards import admin_cancel_button, admin_confirm_keyboard, admin_skip_button, \
    remove_keyboard
from states.admin_states import BroadcastStates
from handlers.admin.admin_start import admin_required

# ============================================================
#                BROADCAST MANAGER (MOTOR)
# ============================================================
# Bu klass xabar tarqatish jarayonini to'liq boshqaradi

active_broadcasts = {}  # Aktiv reklamalarni saqlash uchun


class BroadcastCampaign:
    def __init__(self, campaign_id, users, message_data, creator_id, schedule_time=None):
        self.id = campaign_id
        self.users = users  # Userlar ro'yxati (ID lar)
        self.data = message_data  # Xabar matni, media, tugmalar
        self.creator_id = creator_id
        self.schedule_time = schedule_time

        # Statuslar
        self.running = True
        self.paused = False
        self.stopped = False

        # Statistika
        self.sent = 0
        self.failed = 0
        self.blocked = 0
        self.total = len(users)
        self.status_msg = None

    async def start(self):
        """Reklamani ishga tushirish"""

        # 1. Agar vaqt belgilangan bo'lsa, kutamiz
        if self.schedule_time:
            now = datetime.now()
            delay = (self.schedule_time - now).total_seconds()
            if delay > 0:
                await bot.send_message(
                    self.creator_id,
                    f"⏳ <b>Reklama rejalashtirildi!</b>\n\n"
                    f"⏰ Yuborish vaqti: {self.schedule_time.strftime('%H:%M')}\n"
                    f"🆔 ID: #{self.id}"
                )
                await asyncio.sleep(delay)

        # 2. Jarayon boshlanishi haqida xabar
        self.status_msg = await bot.send_message(
            self.creator_id,
            self._get_report_text("🚀 Boshlanmoqda..."),
            reply_markup=self._get_control_keyboard()
        )

        # 3. Asosiy sikl
        for i, user_id in enumerate(self.users, 1):
            # Agar to'xtatilgan bo'lsa
            if self.stopped:
                break

            # Agar pauza bo'lsa, kutib turamiz
            while self.paused:
                await asyncio.sleep(1)
                if self.stopped: break

            # Xabar yuborish
            if isinstance(user_id, (tuple, list)):
                user_id = user_id[0]  # Bazadan tuple qaytishi mumkin

            success, error = await self._send_safe(user_id)

            if success:
                self.sent += 1
            else:
                if error == "blocked":
                    self.blocked += 1
                else:
                    self.failed += 1

            # Har 20 ta xabarda statistika yangilash
            if i % 20 == 0:
                try:
                    await self.status_msg.edit_text(
                        self._get_report_text("📤 Yuborilmoqda..."),
                        reply_markup=self._get_control_keyboard()
                    )
                except:
                    pass

            # Telegram limitlari uchun kichik pauza
            await asyncio.sleep(0.05)

        # 4. Yakunlash
        final_status = "⛔️ To'xtatildi" if self.stopped else "✅ Yakunlandi"
        try:
            await self.status_msg.edit_text(
                self._get_report_text(final_status),
                reply_markup=None  # Tugmalarni olib tashlaymiz
            )
        except:
            pass

        # Ro'yxatdan o'chirish
        if self.id in active_broadcasts:
            del active_broadcasts[self.id]

    async def _send_safe(self, user_id):
        """Xavfsiz xabar yuborish funksiyasi"""
        try:
            text = self.data.get('text')
            media_type = self.data.get('media_type')
            media_id = self.data.get('media_id')
            keyboard = self.data.get('keyboard')

            if media_type == 'photo':
                await bot.send_photo(user_id, media_id, caption=text, reply_markup=keyboard)
            elif media_type == 'video':
                await bot.send_video(user_id, media_id, caption=text, reply_markup=keyboard)
            else:
                await bot.send_message(user_id, text, reply_markup=keyboard, disable_web_page_preview=True)
            return True, None

        except exceptions.BotBlocked:
            return False, "blocked"
        except exceptions.UserDeactivated:
            return False, "blocked"
        except exceptions.RetryAfter as e:
            await asyncio.sleep(e.timeout)
            return await self._send_safe(user_id)
        except Exception as e:
            return False, str(e)

    def _get_report_text(self, status):
        progress = self.sent + self.failed + self.blocked
        percent = (progress / self.total * 100) if self.total > 0 else 0

        return (
            f"📢 <b>Reklama #{self.id}</b>\n\n"
            f"📊 Holat: <b>{status}</b>\n"
            f"📈 Progress: {progress}/{self.total} ({percent:.1f}%)\n\n"
            f"✅ Yetib bordi: {self.sent}\n"
            f"🚫 Bloklagan: {self.blocked}\n"
            f"❌ Xatolik: {self.failed}"
        )

    def _get_control_keyboard(self):
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        if self.paused:
            keyboard.insert(
                types.InlineKeyboardButton("▶️ Davom ettirish", callback_data=f"broadcast:resume:{self.id}"))
        else:
            keyboard.insert(types.InlineKeyboardButton("⏸ Pauza", callback_data=f"broadcast:pause:{self.id}"))

        keyboard.insert(types.InlineKeyboardButton("⛔️ To'xtatish", callback_data=f"broadcast:stop:{self.id}"))
        return keyboard

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.stopped = True
        self.paused = False  # Loopdan chiqish uchun


# ============================================================
#                    MENYULAR & TAYYORGARLIK
# ============================================================

@dp.message_handler(Text(equals="📢 Reklama"))
@admin_required
async def broadcast_menu_message(message: types.Message):
    await show_broadcast_main_menu(message)


@dp.callback_query_handler(text="admin:broadcast")
@admin_required
async def show_broadcast_menu_query(call: types.CallbackQuery):
    await show_broadcast_main_menu(call.message, edit=True)


async def show_broadcast_main_menu(message: types.Message, edit=False):
    total = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)[0]
    paid = user_db.execute("SELECT COUNT(DISTINCT user_id) FROM Payments WHERE status = 'approved'", fetchone=True)[0]

    text = f"""
📢 <b>Ommaviy xabar yuborish (Mukammal Tizim)</b>

👥 Jami userlar: <b>{total}</b>
💰 Pullik obunachilar: <b>{paid}</b>
🆓 Bepul userlar: <b>{total - paid}</b>

⬇️ <b>Kimga yubormoqchisiz?</b>
"""
    if edit:
        await message.edit_text(text, reply_markup=broadcast_menu())
    else:
        await message.answer(text, reply_markup=broadcast_menu())


# --- Target Selection ---

@dp.callback_query_handler(text_startswith="admin:broadcast:")
@admin_required
async def start_broadcast_wizard(call: types.CallbackQuery, state: FSMContext):
    target_type = call.data.split(":")[-1]

    if target_type == "course":
        # Kurs tanlash logikasi
        courses = user_db.get_all_courses(active_only=True)
        kb = types.InlineKeyboardMarkup(row_width=1)
        for c in courses:
            count = \
            user_db.execute("SELECT COUNT(DISTINCT user_id) FROM Payments WHERE course_id=? AND status='approved'",
                            (c['id'],), fetchone=True)[0]
            kb.add(types.InlineKeyboardButton(f"{c['name']} ({count})", callback_data=f"admin:bc_course:{c['id']}"))
        kb.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:broadcast"))
        await call.message.edit_text("📚 Kursni tanlang:", reply_markup=kb)
        return

    # Userlarni hisoblash
    count = 0
    target_name = ""

    if target_type == "all":
        count = user_db.execute("SELECT COUNT(*) FROM Users", fetchone=True)[0]
        target_name = "Barchaga"
    elif target_type == "paid":
        count = user_db.execute("SELECT COUNT(DISTINCT user_id) FROM Payments WHERE status='approved'", fetchone=True)[
            0]
        target_name = "Pullik obunachilarga"
    elif target_type == "free":
        count = user_db.execute(
            "SELECT COUNT(*) FROM Users u WHERE NOT EXISTS (SELECT 1 FROM Payments p WHERE p.user_id=u.id AND p.status='approved')",
            fetchone=True)[0]
        target_name = "Bepul foydalanuvchilarga"

    if count == 0:
        await call.answer("📭 Foydalanuvchilar yo'q!", show_alert=True)
        return

    await state.update_data(target=target_type, count=count, target_name=target_name)

    await call.message.edit_text(
        f"📢 <b>{target_name}</b>\n"
        f"👥 Qabul qiluvchilar: {count} ta\n\n"
        f"📝 <b>Xabar matnini yuboring:</b>"
    )
    await BroadcastStates.message_text.set()


@dp.callback_query_handler(text_startswith="admin:bc_course:")
@admin_required
async def course_broadcast_selected(call: types.CallbackQuery, state: FSMContext):
    course_id = int(call.data.split(":")[-1])
    course = user_db.get_course(course_id)
    count = user_db.execute("SELECT COUNT(DISTINCT user_id) FROM Payments WHERE course_id=? AND status='approved'",
                            (course_id,), fetchone=True)[0]

    if count == 0:
        await call.answer("📭 Bu kursda o'quvchi yo'q", show_alert=True)
        return

    await state.update_data(target="course", target_id=course_id, count=count,
                            target_name=f"{course['name']} o'quvchilari")
    await call.message.edit_text(
        f"📢 <b>{course['name']} kursi</b>\n"
        f"👥 O'quvchilar: {count} ta\n\n"
        f"📝 <b>Xabar matnini yuboring:</b>"
    )
    await BroadcastStates.message_text.set()


# ============================================================
#                    CONTENT INPUT
# ============================================================

@dp.message_handler(state=BroadcastStates.message_text, content_types=types.ContentType.ANY)
async def receive_text_or_media(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    # Matn va Media aniqlash
    text = message.caption or message.text or ""
    media_type = None
    media_id = None

    if message.photo:
        media_type = 'photo'
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = 'video'
        media_id = message.video.file_id

    await state.update_data(text=text, media_type=media_type, media_id=media_id)

    await message.answer(
        "🔘 <b>Tugma qo'shasizmi?</b>\n\n"
        "Format: <code>Tugma nomi - https://manzil.uz</code>\n"
        "Masalan: <code>Kanalga o'tish - https://t.me/kanal</code>\n\n"
        "Agar kerak bo'lmasa, <b>⏩ O'tkazib yuborish</b> ni bosing.",
        reply_markup=admin_skip_button()
    )
    await BroadcastStates.buttons.set()


@dp.message_handler(state=BroadcastStates.buttons)
async def receive_buttons(message: types.Message, state: FSMContext):
    keyboard = None

    if message.text != "⏩ O'tkazib yuborish" and message.text != "❌ Bekor qilish":
        try:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            # Bir nechta tugma bo'lishi mumkin (vergul bilan)
            raw_buttons = message.text.split(',')
            for raw in raw_buttons:
                parts = raw.split('-')
                if len(parts) != 2: raise ValueError
                name = parts[0].strip()
                url = parts[1].strip()
                if not url.startswith('http'): url = f"https://{url}"
                keyboard.add(types.InlineKeyboardButton(name, url=url))
        except:
            await message.reply("❌ Xato format! Qaytadan yozing yoki o'tkazib yuboring.")
            return

    await state.update_data(keyboard=keyboard)

    # Vaqtni so'rash
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚀 Hozir yuborish", callback_data="time:now"))
    kb.add(types.InlineKeyboardButton("⏰ Keyinroq (Vaqt belgilash)", callback_data="time:later"))

    await message.answer("⏳ <b>Qachon yuborilsin?</b>", reply_markup=kb)
    await BroadcastStates.time.set()




# ============================================================
#                    VAQT VA TASDIQLASH
# ============================================================

@dp.callback_query_handler(state=BroadcastStates.time)
async def choose_time(call: types.CallbackQuery, state: FSMContext):
    if call.data == "time:now":
        await confirm_broadcast(call, state)
    else:
        await call.message.edit_text("⏰ Vaqtni <b>HH:MM</b> formatda yozing (Masalan: 14:30):")
        await BroadcastStates.custom_time.set()


@dp.message_handler(state=BroadcastStates.custom_time)
async def receive_custom_time(message: types.Message, state: FSMContext):
    try:
        # Vaqtni pars qilish
        time_str = message.text.strip()
        now = datetime.now()
        target_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)

        # Agar vaqt o'tib ketgan bo'lsa, ertangi kunga o'tkazamiz
        if target_time < now:
            target_time += timedelta(days=1)

        await state.update_data(schedule_time=target_time)
        await confirm_broadcast(message, state, manual_msg=True)

    except ValueError:
        await message.reply("❌ Noto'g'ri format! HH:MM shaklida yozing (Masalan: 20:00)")


async def confirm_broadcast(obj, state: FSMContext, manual_msg=False):
    data = await state.get_data()
    schedule_time = data.get('schedule_time')

    time_text = schedule_time.strftime("%d-%m %H:%M") if schedule_time else "Hozir"

    text = f"""
📢 <b>Tasdiqlash</b>

🎯 <b>Kimga:</b> {data['target_name']}
📊 <b>Soni:</b> {data['count']} ta
⏳ <b>Vaqt:</b> {time_text}

📝 <b>Matn:</b> {data['text'][:100]}...
"""
    # Preview
    msg = obj if manual_msg else obj.message

    if data.get('media_type') == 'photo':
        await bot.send_photo(msg.chat.id, data['media_id'], caption=text, reply_markup=admin_confirm_keyboard())
    elif data.get('media_type') == 'video':
        await bot.send_video(msg.chat.id, data['media_id'], caption=text, reply_markup=admin_confirm_keyboard())
    else:
        await bot.send_message(msg.chat.id, text, reply_markup=admin_confirm_keyboard())

    await BroadcastStates.confirm.set()


@dp.message_handler(state=BroadcastStates.confirm)
async def execute_broadcast(message: types.Message, state: FSMContext):
    if message.text != "✅ Ha":
        await state.finish()
        await message.answer("❌ Bekor qilindi", reply_markup=remove_keyboard())
        return

    data = await state.get_data()
    await state.finish()

    # 1. Userlarni bazadan olish
    users = []
    if data['target'] == "all":
        users = user_db.execute("SELECT telegram_id FROM Users", fetchall=True)
    elif data['target'] == "paid":
        users = user_db.execute(
            "SELECT DISTINCT u.telegram_id FROM Users u JOIN Payments p ON u.id=p.user_id WHERE p.status='approved'",
            fetchall=True)
    elif data['target'] == "free":
        users = user_db.execute(
            "SELECT telegram_id FROM Users u WHERE NOT EXISTS (SELECT 1 FROM Payments p WHERE p.user_id=u.id AND p.status='approved')",
            fetchall=True)
    elif data['target'] == "course":
        users = user_db.execute(
            "SELECT DISTINCT u.telegram_id FROM Users u JOIN Payments p ON u.id=p.user_id WHERE p.course_id=? AND p.status='approved'",
            (data['target_id'],), fetchall=True)

    if not users:
        await message.answer("❌ Xatolik: Userlar topilmadi.")
        return

    # Listga o'tkazish
    user_ids = [u[0] for u in users]

    # 2. Campaign yaratish
    campaign_id = len(active_broadcasts) + 1
    campaign = BroadcastCampaign(
        campaign_id=campaign_id,
        users=user_ids,
        message_data=data,
        creator_id=message.chat.id,
        schedule_time=data.get('schedule_time')
    )

    # 3. Global ro'yxatga qo'shish va ishga tushirish
    active_broadcasts[campaign_id] = campaign

    await message.answer("✅ Qabul qilindi!", reply_markup=remove_keyboard())

    # Orqa fonda ishga tushirish
    asyncio.create_task(campaign.start())


# ============================================================
#                    CONTROL HANDLERS (CALLBACKS)
# ============================================================

@dp.callback_query_handler(text_startswith="broadcast:")
async def control_broadcast(call: types.CallbackQuery):
    action, campaign_id = call.data.split(":")[1:]
    campaign_id = int(campaign_id)

    campaign = active_broadcasts.get(campaign_id)

    if not campaign:
        await call.answer("⚠️ Bu reklama allaqachon tugagan yoki topilmadi.", show_alert=True)
        return

    if action == "pause":
        campaign.pause()
        await call.answer("⏸ Pauza qilindi")
    elif action == "resume":
        campaign.resume()
        await call.answer("▶️ Davom ettirilmoqda")
    elif action == "stop":
        campaign.stop()
        await call.answer("⛔️ To'xtatildi")

    # Klaviaturani yangilash (Xabar o'zi loop ichida yangilanadi, lekin biz darhol reaksiya beramiz)
    try:
        await campaign.status_msg.edit_reply_markup(reply_markup=campaign._get_control_keyboard())
    except:
        pass