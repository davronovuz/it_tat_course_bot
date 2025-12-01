"""
Admin Panel Keyboards
=====================
O'quv markaz bot - Admin panel uchun barcha tugmalar
"""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from typing import List, Dict, Optional


# ============================================================
#                    REPLY KEYBOARDS (Asosiy menyu)
# ============================================================

def admin_main_menu() -> ReplyKeyboardMarkup:
    """Admin asosiy menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📚 Kurslar"),
        KeyboardButton("👥 Foydalanuvchilar")
    )
    keyboard.add(
        KeyboardButton("💰 To'lovlar"),
        KeyboardButton("📊 Hisobotlar")
    )
    keyboard.add(
        KeyboardButton("💬 Fikrlar"),
        KeyboardButton("⚙️ Sozlamalar")
    )
    keyboard.add(KeyboardButton("🏠 Bosh menyu"))
    return keyboard


def admin_back_button() -> ReplyKeyboardMarkup:
    """Orqaga tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("⬅️ Orqaga"))
    keyboard.add(KeyboardButton("🏠 Bosh menyu"))
    return keyboard


def admin_cancel_button() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def admin_skip_button() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("⏩ O'tkazib yuborish"))
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def admin_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Tasdiqlash klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("✅ Ha"),
        KeyboardButton("❌ Yo'q")
    )
    return keyboard


# ============================================================
#                    KURS BOSHQARUVI
# ============================================================

def courses_menu() -> InlineKeyboardMarkup:
    """Kurslar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ Yangi kurs", callback_data="admin:course:add"),
        InlineKeyboardButton("📋 Kurslar ro'yxati", callback_data="admin:course:list"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:main")
    )
    return keyboard


def courses_list(courses: List[Dict]) -> InlineKeyboardMarkup:
    """Kurslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for course in courses:
        status = "✅" if course.get('is_active', True) else "❌"
        keyboard.add(
            InlineKeyboardButton(
                f"{status} {course['name']}",
                callback_data=f"admin:course:view:{course['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("➕ Yangi kurs", callback_data="admin:course:add"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:courses")
    )
    return keyboard


def course_detail(course_id: int, is_active: bool = True) -> InlineKeyboardMarkup:
    """Kurs tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📁 Modullar", callback_data=f"admin:module:list:{course_id}"),
        InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"admin:course:edit:{course_id}")
    )
    keyboard.add(
        InlineKeyboardButton("💰 Narx", callback_data=f"admin:course:price:{course_id}"),
        InlineKeyboardButton("📊 Statistika", callback_data=f"admin:course:stats:{course_id}")
    )

    if is_active:
        keyboard.add(
            InlineKeyboardButton("🚫 O'chirish", callback_data=f"admin:course:deactivate:{course_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("✅ Faollashtirish", callback_data=f"admin:course:activate:{course_id}")
        )

    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin:course:delete:{course_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:course:list")
    )
    return keyboard


def course_edit_menu(course_id: int) -> InlineKeyboardMarkup:
    """Kurs tahrirlash menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Nom", callback_data=f"admin:course:edit:name:{course_id}"),
        InlineKeyboardButton("📄 Tavsif", callback_data=f"admin:course:edit:desc:{course_id}")
    )
    keyboard.add(
        InlineKeyboardButton("💰 Narx", callback_data=f"admin:course:edit:price:{course_id}"),
        InlineKeyboardButton("🔢 Tartib", callback_data=f"admin:course:edit:order:{course_id}")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:course:view:{course_id}")
    )
    return keyboard


# ============================================================
#                    MODUL BOSHQARUVI
# ============================================================

def modules_list(course_id: int, modules: List[Dict]) -> InlineKeyboardMarkup:
    """Modullar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for module in modules:
        status = "✅" if module.get('is_active', True) else "❌"
        keyboard.add(
            InlineKeyboardButton(
                f"{status} {module['order_num']}. {module['name']}",
                callback_data=f"admin:module:view:{module['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("➕ Yangi modul", callback_data=f"admin:module:add:{course_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:course:view:{course_id}")
    )
    return keyboard


def module_detail(module_id: int, course_id: int, is_active: bool = True) -> InlineKeyboardMarkup:
    """Modul tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📹 Darslar", callback_data=f"admin:lesson:list:{module_id}"),
        InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"admin:module:edit:{module_id}")
    )

    if is_active:
        keyboard.add(
            InlineKeyboardButton("🚫 O'chirish", callback_data=f"admin:module:deactivate:{module_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("✅ Faollashtirish", callback_data=f"admin:module:activate:{module_id}")
        )

    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin:module:delete:{module_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:module:list:{course_id}")
    )
    return keyboard


def module_edit_menu(module_id: int) -> InlineKeyboardMarkup:
    """Modul tahrirlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Nom", callback_data=f"admin:module:edit:name:{module_id}"),
        InlineKeyboardButton("📄 Tavsif", callback_data=f"admin:module:edit:desc:{module_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🔢 Tartib", callback_data=f"admin:module:edit:order:{module_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:module:view:{module_id}")
    )
    return keyboard


# ============================================================
#                    DARS BOSHQARUVI
# ============================================================

def lessons_list(module_id: int, lessons: List[Dict]) -> InlineKeyboardMarkup:
    """Darslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        # Status ikonkalari
        free = "🆓" if lesson.get('is_free') else ""
        test = "📝" if lesson.get('has_test') else ""
        status = "✅" if lesson.get('is_active', True) else "❌"

        keyboard.add(
            InlineKeyboardButton(
                f"{status} {lesson['order_num']}. {lesson['name']} {free}{test}",
                callback_data=f"admin:lesson:view:{lesson['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("➕ Yangi dars", callback_data=f"admin:lesson:add:{module_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:module:view:{module_id}")
    )
    return keyboard


def lesson_detail(lesson_id: int, module_id: int, has_test: bool = False,
                  is_free: bool = False) -> InlineKeyboardMarkup:
    """Dars tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"admin:lesson:edit:{lesson_id}"),
        InlineKeyboardButton("📹 Video", callback_data=f"admin:lesson:video:{lesson_id}")
    )

    keyboard.add(
        InlineKeyboardButton("📎 Materiallar", callback_data=f"admin:material:list:{lesson_id}"),
        InlineKeyboardButton("📝 Test", callback_data=f"admin:test:view:{lesson_id}")
    )

    # Bepul/Pullik toggle
    if is_free:
        keyboard.add(
            InlineKeyboardButton("💰 Pullik qilish", callback_data=f"admin:lesson:paid:{lesson_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("🆓 Bepul qilish", callback_data=f"admin:lesson:free:{lesson_id}")
        )

    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin:lesson:delete:{lesson_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:lesson:list:{module_id}")
    )
    return keyboard


def lesson_edit_menu(lesson_id: int) -> InlineKeyboardMarkup:
    """Dars tahrirlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Nom", callback_data=f"admin:lesson:edit:name:{lesson_id}"),
        InlineKeyboardButton("📄 Tavsif", callback_data=f"admin:lesson:edit:desc:{lesson_id}")
    )
    keyboard.add(
        InlineKeyboardButton("📹 Video", callback_data=f"admin:lesson:edit:video:{lesson_id}"),
        InlineKeyboardButton("🔢 Tartib", callback_data=f"admin:lesson:edit:order:{lesson_id}")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:lesson:view:{lesson_id}")
    )
    return keyboard


# ============================================================
#                    MATERIAL BOSHQARUVI
# ============================================================

def materials_list(lesson_id: int, materials: List[Dict]) -> InlineKeyboardMarkup:
    """Materiallar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Fayl turi ikonkalari
    type_icons = {
        'pdf': '📕',
        'pptx': '📊',
        'docx': '📄',
        'xlsx': '📗',
        'image': '🖼',
        'other': '📎'
    }

    for material in materials:
        icon = type_icons.get(material.get('file_type', 'other'), '📎')
        keyboard.add(
            InlineKeyboardButton(
                f"{icon} {material['name']}",
                callback_data=f"admin:material:view:{material['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("➕ Material qo'shish", callback_data=f"admin:material:add:{lesson_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:lesson:view:{lesson_id}")
    )
    return keyboard


def material_detail(material_id: int, lesson_id: int) -> InlineKeyboardMarkup:
    """Material tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📥 Yuklab olish", callback_data=f"admin:material:download:{material_id}"),
        InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"admin:material:edit:{material_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin:material:delete:{material_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:material:list:{lesson_id}")
    )
    return keyboard


def material_type_select(lesson_id: int) -> InlineKeyboardMarkup:
    """Material turini tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📕 PDF", callback_data=f"admin:material:type:pdf:{lesson_id}"),
        InlineKeyboardButton("📊 PPTX", callback_data=f"admin:material:type:pptx:{lesson_id}")
    )
    keyboard.add(
        InlineKeyboardButton("📄 DOCX", callback_data=f"admin:material:type:docx:{lesson_id}"),
        InlineKeyboardButton("📗 XLSX", callback_data=f"admin:material:type:xlsx:{lesson_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🖼 Rasm", callback_data=f"admin:material:type:image:{lesson_id}"),
        InlineKeyboardButton("📎 Boshqa", callback_data=f"admin:material:type:other:{lesson_id}")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:material:list:{lesson_id}")
    )
    return keyboard


# ============================================================
#                    TEST BOSHQARUVI
# ============================================================

def test_menu(lesson_id: int, has_test: bool = False) -> InlineKeyboardMarkup:
    """Test menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if has_test:
        keyboard.add(
            InlineKeyboardButton("📋 Savollar", callback_data=f"admin:test:questions:{lesson_id}"),
            InlineKeyboardButton("➕ Savol qo'shish", callback_data=f"admin:test:add_q:{lesson_id}"),
            InlineKeyboardButton("📤 Excel yuklash", callback_data=f"admin:test:upload:{lesson_id}"),
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data=f"admin:test:settings:{lesson_id}"),
            InlineKeyboardButton("🗑 Testni o'chirish", callback_data=f"admin:test:delete:{lesson_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("➕ Test yaratish", callback_data=f"admin:test:create:{lesson_id}")
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:lesson:view:{lesson_id}")
    )
    return keyboard


def test_questions_list(lesson_id: int, questions: List[Dict]) -> InlineKeyboardMarkup:
    """Test savollari ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for i, q in enumerate(questions, 1):
        # Savolni qisqartirish
        text = q['question'][:30] + "..." if len(q['question']) > 30 else q['question']
        keyboard.add(
            InlineKeyboardButton(
                f"{i}. {text}",
                callback_data=f"admin:question:view:{q['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("➕ Savol qo'shish", callback_data=f"admin:test:add_q:{lesson_id}"),
        InlineKeyboardButton("🗑 Barchasini o'chirish", callback_data=f"admin:test:clear:{lesson_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:test:view:{lesson_id}")
    )
    return keyboard


def question_detail(question_id: int, lesson_id: int) -> InlineKeyboardMarkup:
    """Savol tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"admin:question:edit:{question_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin:question:delete:{question_id}")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:test:questions:{lesson_id}")
    )
    return keyboard


def test_settings(lesson_id: int, test_id: int) -> InlineKeyboardMarkup:
    """Test sozlamalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 O'tish bali (%)", callback_data=f"admin:test:set:pass:{test_id}"),
        InlineKeyboardButton("⏱ Vaqt chegarasi", callback_data=f"admin:test:set:time:{test_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:test:view:{lesson_id}")
    )
    return keyboard


def correct_answer_select(lesson_id: int) -> InlineKeyboardMarkup:
    """To'g'ri javobni tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=4)
    keyboard.add(
        InlineKeyboardButton("🅰️ A", callback_data=f"admin:answer:A:{lesson_id}"),
        InlineKeyboardButton("🅱️ B", callback_data=f"admin:answer:B:{lesson_id}"),
        InlineKeyboardButton("🅲 C", callback_data=f"admin:answer:C:{lesson_id}"),
        InlineKeyboardButton("🅳 D", callback_data=f"admin:answer:D:{lesson_id}")
    )
    keyboard.add(
        InlineKeyboardButton("❌ Bekor qilish", callback_data=f"admin:test:add_q:{lesson_id}")
    )
    return keyboard


# ============================================================
#                    FOYDALANUVCHILAR BOSHQARUVI
# ============================================================

def users_menu() -> InlineKeyboardMarkup:
    """Foydalanuvchilar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📋 Barcha foydalanuvchilar", callback_data="admin:users:list"),
        InlineKeyboardButton("🔍 Qidirish", callback_data="admin:users:search"),
        InlineKeyboardButton("💰 Pullik obunalar", callback_data="admin:users:paid"),
        InlineKeyboardButton("🏆 Top o'quvchilar", callback_data="admin:users:top"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:main")
    )
    return keyboard


def users_list(users: List[Dict], page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Foydalanuvchilar ro'yxati (pagination bilan)"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for user in users:
        name = user.get('full_name') or user.get('username') or f"ID: {user['telegram_id']}"
        score = user.get('total_score', 0)
        keyboard.add(
            InlineKeyboardButton(
                f"👤 {name} | 🏆 {score}",
                callback_data=f"admin:user:view:{user['telegram_id']}"
            )
        )

    # Pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️", callback_data=f"admin:users:page:{page - 1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(f"{page}/{total_pages}", callback_data="admin:users:current")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton("➡️", callback_data=f"admin:users:page:{page + 1}")
        )

    if nav_buttons:
        keyboard.row(*nav_buttons)

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:users")
    )
    return keyboard


def user_detail(telegram_id: int, is_blocked: bool = False) -> InlineKeyboardMarkup:
    """Foydalanuvchi tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("🎁 Dostup berish", callback_data=f"admin:user:access:{telegram_id}"),
        InlineKeyboardButton("📊 Progress", callback_data=f"admin:user:progress:{telegram_id}")
    )
    keyboard.add(
        InlineKeyboardButton("📨 Xabar yuborish", callback_data=f"admin:user:message:{telegram_id}"),
        InlineKeyboardButton("🏆 Ball qo'shish", callback_data=f"admin:user:score:{telegram_id}")
    )

    if is_blocked:
        keyboard.add(
            InlineKeyboardButton("✅ Blokdan chiqarish", callback_data=f"admin:user:unblock:{telegram_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("🚫 Bloklash", callback_data=f"admin:user:block:{telegram_id}")
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:users:list")
    )
    return keyboard


def grant_access_courses(telegram_id: int, courses: List[Dict]) -> InlineKeyboardMarkup:
    """Dostup berish - kurs tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for course in courses:
        keyboard.add(
            InlineKeyboardButton(
                f"📚 {course['name']}",
                callback_data=f"admin:access:course:{telegram_id}:{course['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🎨 Barcha kurslar", callback_data=f"admin:access:all:{telegram_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:user:view:{telegram_id}")
    )
    return keyboard


def grant_access_duration(telegram_id: int, course_id: int) -> InlineKeyboardMarkup:
    """Dostup berish - muddat tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("1 oy", callback_data=f"admin:access:dur:{telegram_id}:{course_id}:30"),
        InlineKeyboardButton("3 oy", callback_data=f"admin:access:dur:{telegram_id}:{course_id}:90"),
        InlineKeyboardButton("6 oy", callback_data=f"admin:access:dur:{telegram_id}:{course_id}:180")
    )
    keyboard.add(
        InlineKeyboardButton("1 yil", callback_data=f"admin:access:dur:{telegram_id}:{course_id}:365"),
        InlineKeyboardButton("♾ Cheksiz", callback_data=f"admin:access:dur:{telegram_id}:{course_id}:0")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:user:access:{telegram_id}")
    )
    return keyboard


# ============================================================
#                    TO'LOVLAR BOSHQARUVI
# ============================================================

def payments_menu() -> InlineKeyboardMarkup:
    """To'lovlar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📥 Kutilayotgan", callback_data="admin:payments:pending"),
        InlineKeyboardButton("✅ Tasdiqlangan", callback_data="admin:payments:approved"),
        InlineKeyboardButton("❌ Rad etilgan", callback_data="admin:payments:rejected"),
        InlineKeyboardButton("📊 Statistika", callback_data="admin:payments:stats"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:main")
    )
    return keyboard


def pending_payments_list(payments: List[Dict]) -> InlineKeyboardMarkup:
    """Kutilayotgan to'lovlar"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for payment in payments:
        name = payment.get('full_name') or payment.get('username') or 'Noma\'lum'
        keyboard.add(
            InlineKeyboardButton(
                f"💰 {name} - {payment['amount']:,.0f} so'm",
                callback_data=f"admin:payment:view:{payment['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:payments")
    )
    return keyboard


def payment_detail(payment_id: int, has_receipt: bool = False) -> InlineKeyboardMarkup:
    """To'lov tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    if has_receipt:
        keyboard.add(
            InlineKeyboardButton("🧾 Chekni ko'rish", callback_data=f"admin:payment:receipt:{payment_id}")
        )

    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin:payment:approve:{payment_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"admin:payment:reject:{payment_id}")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:payments:pending")
    )
    return keyboard


def payment_confirm(payment_id: int, action: str) -> InlineKeyboardMarkup:
    """To'lovni tasdiqlash/rad etish"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"admin:payment:{action}:confirm:{payment_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"admin:payment:view:{payment_id}")
    )
    return keyboard


# ============================================================
#                    HISOBOTLAR
# ============================================================

def reports_menu() -> InlineKeyboardMarkup:
    """Hisobotlar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 Umumiy statistika", callback_data="admin:report:general"),
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin:report:users"),
        InlineKeyboardButton("💰 Moliyaviy", callback_data="admin:report:finance"),
        InlineKeyboardButton("📚 Kurslar bo'yicha", callback_data="admin:report:courses"),
        InlineKeyboardButton("📥 Excel yuklab olish", callback_data="admin:report:export"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:main")
    )
    return keyboard


def report_period_select(report_type: str) -> InlineKeyboardMarkup:
    """Hisobot davri tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📅 Bugun", callback_data=f"admin:report:{report_type}:today"),
        InlineKeyboardButton("📅 Bu hafta", callback_data=f"admin:report:{report_type}:week")
    )
    keyboard.add(
        InlineKeyboardButton("📅 Bu oy", callback_data=f"admin:report:{report_type}:month"),
        InlineKeyboardButton("📅 Barchasi", callback_data=f"admin:report:{report_type}:all")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:reports")
    )
    return keyboard


# ============================================================
#                    FIKRLAR
# ============================================================

def feedbacks_menu() -> InlineKeyboardMarkup:
    """Fikrlar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📋 So'nggi fikrlar", callback_data="admin:feedback:list"),
        InlineKeyboardButton("⭐ Yulduz bo'yicha", callback_data="admin:feedback:by_rating"),
        InlineKeyboardButton("📚 Dars bo'yicha", callback_data="admin:feedback:by_lesson"),
        InlineKeyboardButton("📊 Statistika", callback_data="admin:feedback:stats"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:main")
    )
    return keyboard


def feedbacks_list(feedbacks: List[Dict], page: int = 1) -> InlineKeyboardMarkup:
    """Fikrlar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for feedback in feedbacks:
        stars = "⭐" * feedback['rating']
        name = feedback.get('username') or 'Anonim'
        keyboard.add(
            InlineKeyboardButton(
                f"{stars} {name}",
                callback_data=f"admin:feedback:view:{feedback['id']}"
            )
        )

    # Pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"admin:feedback:page:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}", callback_data="current"))
    nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"admin:feedback:page:{page + 1}"))
    keyboard.row(*nav_buttons)

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:feedbacks")
    )
    return keyboard


def feedback_rating_filter() -> InlineKeyboardMarkup:
    """Yulduz bo'yicha filter"""
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(
        InlineKeyboardButton("⭐", callback_data="admin:feedback:rating:1"),
        InlineKeyboardButton("⭐⭐", callback_data="admin:feedback:rating:2"),
        InlineKeyboardButton("⭐⭐⭐", callback_data="admin:feedback:rating:3"),
        InlineKeyboardButton("⭐⭐⭐⭐", callback_data="admin:feedback:rating:4"),
        InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="admin:feedback:rating:5")
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:feedbacks")
    )
    return keyboard


# ============================================================
#                    SOZLAMALAR
# ============================================================

def settings_menu() -> InlineKeyboardMarkup:
    """Sozlamalar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📝 Fikr sozlamalari", callback_data="admin:settings:feedback"),
        InlineKeyboardButton("📊 Test sozlamalari", callback_data="admin:settings:test"),
        InlineKeyboardButton("🏆 Sertifikat sozlamalari", callback_data="admin:settings:cert"),
        InlineKeyboardButton("🔔 Bildirishnomalar", callback_data="admin:settings:notifications"),
        InlineKeyboardButton("👨‍💼 Adminlar", callback_data="admin:settings:admin"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:main")
    )
    return keyboard


def feedback_settings(current: Dict) -> InlineKeyboardMarkup:
    """Fikr sozlamalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    required = "✅" if current.get('feedback_required') == 'true' else "❌"
    keyboard.add(
        InlineKeyboardButton(f"Majburiy: {required}", callback_data="admin:settings:feedback:required"),
        InlineKeyboardButton(f"Ball: {current.get('feedback_score', 2)}",
                             callback_data="admin:settings:feedback:score"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:settings")
    )
    return keyboard


def test_settings_menu(current: Dict) -> InlineKeyboardMarkup:
    """Test sozlamalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(
            f"O'tish bali: {current.get('test_passing_score', 60)}%",
            callback_data="admin:settings:test:pass"
        ),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:settings")
    )
    return keyboard


def cert_settings(current: Dict) -> InlineKeyboardMarkup:
    """Sertifikat sozlamalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(
            f"🥉 Bronza: {current.get('bronze_threshold', 60)}%",
            callback_data="admin:settings:cert:bronze"
        ),
        InlineKeyboardButton(
            f"🥈 Kumush: {current.get('silver_threshold', 75)}%",
            callback_data="admin:settings:cert:silver"
        ),
        InlineKeyboardButton(
            f"🥇 Oltin: {current.get('gold_threshold', 90)}%",
            callback_data="admin:settings:cert:gold"
        ),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:settings")
    )
    return keyboard


def admins_list(admins: List[Dict]) -> InlineKeyboardMarkup:
    """Adminlar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for admin in admins:
        role = "👑" if admin.get('is_super_admin') else "👨‍💼"
        keyboard.add(
            InlineKeyboardButton(
                f"{role} {admin['name']}",
                callback_data=f"admin:admin:view:{admin['telegram_id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("➕ Admin qo'shish", callback_data="admin:admin:add"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:settings")
    )
    return keyboard


def admin_detail(admin_telegram_id: int, is_super: bool = False) -> InlineKeyboardMarkup:
    """Admin tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if is_super:
        keyboard.add(
            InlineKeyboardButton("👨‍💼 Oddiy admin qilish", callback_data=f"admin:admin:demote:{admin_telegram_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("👑 Super admin qilish", callback_data=f"admin:admin:promote:{admin_telegram_id}")
        )

    keyboard.add(
        InlineKeyboardButton("🗑 Olib tashlash", callback_data=f"admin:admin:remove:{admin_telegram_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:settings:admin")
    )
    return keyboard


# ============================================================
#                    OMMAVIY XABAR
# ============================================================

def broadcast_menu() -> InlineKeyboardMarkup:
    """Ommaviy xabar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("👥 Barcha foydalanuvchilarga", callback_data="admin:broadcast:all"),
        InlineKeyboardButton("💰 Pullik obunachilar", callback_data="admin:broadcast:paid"),
        InlineKeyboardButton("🆓 Bepul foydalanuvchilar", callback_data="admin:broadcast:free"),
        InlineKeyboardButton("📚 Kurs bo'yicha", callback_data="admin:broadcast:course"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:main")
    )
    return keyboard


def broadcast_confirm(target: str) -> InlineKeyboardMarkup:
    """Xabar yuborishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Yuborish", callback_data=f"admin:broadcast:send:{target}"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="admin:broadcast")
    )
    return keyboard


# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def confirm_action(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Umumiy tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"admin:confirm:{action}:{item_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"admin:cancel:{action}:{item_id}")
    )
    return keyboard


def back_button(callback_data: str) -> InlineKeyboardMarkup:
    """Orqaga tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data=callback_data))
    return keyboard


def close_button() -> InlineKeyboardMarkup:
    """Yopish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Yopish", callback_data="admin:close"))
    return keyboard