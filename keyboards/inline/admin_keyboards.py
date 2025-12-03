"""
Admin Inline Keyboards
======================
Admin uchun barcha inline tugmalar
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Optional


# ============================================================
#                    ASOSIY MENYU
# ============================================================

def admin_main_menu() -> InlineKeyboardMarkup:
    """Admin bosh menyu (inline)"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📚 Kurslar", callback_data="admin:courses"),
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin:users")
    )
    keyboard.add(
        InlineKeyboardButton("💰 To'lovlar", callback_data="admin:payments"),
        InlineKeyboardButton("📊 Hisobotlar", callback_data="admin:reports")
    )
    keyboard.add(
        InlineKeyboardButton("💬 Fikrlar", callback_data="admin:feedbacks"),
        InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin:settings")
    )

    return keyboard


# ============================================================
#                    KURSLAR
# ============================================================

def courses_menu() -> InlineKeyboardMarkup:
    """Kurslar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "➕ Yangi kurs qo'shish",
        callback_data="admin:course:add"
    ))
    keyboard.add(InlineKeyboardButton(
        "📋 Kurslar ro'yxati",
        callback_data="admin:course:list"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:main"
    ))

    return keyboard


def courses_list(courses: List[Dict]) -> InlineKeyboardMarkup:
    """Kurslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for course in courses:
        status = "✅" if course.get('is_active', True) else "❌"
        keyboard.add(InlineKeyboardButton(
            f"{status} {course['name']}",
            callback_data=f"admin:course:view:{course['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "➕ Yangi kurs",
        callback_data="admin:course:add"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:courses"
    ))

    return keyboard


def course_detail(course_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Kurs tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Modullar
    keyboard.add(InlineKeyboardButton(
        "📁 Modullar",
        callback_data=f"admin:module:list:{course_id}"
    ))

    # Tahrirlash
    keyboard.add(InlineKeyboardButton(
        "✏️ Tahrirlash",
        callback_data=f"admin:course:edit:{course_id}"
    ))

    # Statistika
    keyboard.add(InlineKeyboardButton(
        "📊 Statistika",
        callback_data=f"admin:course:stats:{course_id}"
    ))

    # Faollashtirish/Nofaollashtirish
    if is_active:
        keyboard.add(InlineKeyboardButton(
            "❌ Nofaol qilish",
            callback_data=f"admin:course:deactivate:{course_id}"
        ))
    else:
        keyboard.add(InlineKeyboardButton(
            "✅ Faollashtirish",
            callback_data=f"admin:course:activate:{course_id}"
        ))

    # O'chirish
    keyboard.add(InlineKeyboardButton(
        "🗑 O'chirish",
        callback_data=f"admin:course:delete:{course_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:course:list"
    ))

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
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:course:view:{course_id}"
    ))

    return keyboard


# ============================================================
#                    MODULLAR
# ============================================================

def modules_list(course_id: int, modules: List[Dict]) -> InlineKeyboardMarkup:
    """Modullar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for module in modules:
        status = "✅" if module.get('is_active', True) else "❌"
        keyboard.add(InlineKeyboardButton(
            f"{status} {module['name']}",
            callback_data=f"admin:module:view:{module['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "➕ Yangi modul",
        callback_data=f"admin:module:add:{course_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:course:view:{course_id}"
    ))

    return keyboard


def module_detail(module_id: int, course_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Modul tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Darslar
    keyboard.add(InlineKeyboardButton(
        "📹 Darslar",
        callback_data=f"admin:lesson:list:{module_id}"
    ))

    # Tahrirlash
    keyboard.add(InlineKeyboardButton(
        "✏️ Tahrirlash",
        callback_data=f"admin:module:edit:{module_id}"
    ))

    # Faollashtirish/Nofaollashtirish
    if is_active:
        keyboard.add(InlineKeyboardButton(
            "❌ Nofaol qilish",
            callback_data=f"admin:module:deactivate:{module_id}"
        ))
    else:
        keyboard.add(InlineKeyboardButton(
            "✅ Faollashtirish",
            callback_data=f"admin:module:activate:{module_id}"
        ))

    # O'chirish
    keyboard.add(InlineKeyboardButton(
        "🗑 O'chirish",
        callback_data=f"admin:module:delete:{module_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:module:list:{course_id}"
    ))

    return keyboard


def module_edit_menu(module_id: int) -> InlineKeyboardMarkup:
    """Modul tahrirlash menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📝 Nom", callback_data=f"admin:module:edit:name:{module_id}"),
        InlineKeyboardButton("📄 Tavsif", callback_data=f"admin:module:edit:desc:{module_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🔢 Tartib", callback_data=f"admin:module:edit:order:{module_id}")
    )
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:module:view:{module_id}"
    ))

    return keyboard


# ============================================================
#                    DARSLAR
# ============================================================

def lessons_list(module_id: int, lessons: List[Dict]) -> InlineKeyboardMarkup:
    """Darslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        # Status
        status = "✅" if lesson.get('is_active', True) else "❌"

        # Bepul
        free = "🆓" if lesson.get('is_free') else ""

        # Test
        test = "📝" if lesson.get('has_test') else ""

        keyboard.add(InlineKeyboardButton(
            f"{status} {lesson['name']} {free}{test}",
            callback_data=f"admin:lesson:view:{lesson['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "➕ Yangi dars",
        callback_data=f"admin:lesson:add:{module_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:module:view:{module_id}"
    ))

    return keyboard


def lesson_detail(lesson_id: int, module_id: int, has_test: bool, is_free: bool) -> InlineKeyboardMarkup:
    """Dars tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Video
    keyboard.add(InlineKeyboardButton(
        "🎬 Video ko'rish",
        callback_data=f"admin:lesson:video:{lesson_id}"
    ))

    # Materiallar
    keyboard.add(InlineKeyboardButton(
        "📎 Materiallar",
        callback_data=f"admin:material:list:{lesson_id}"
    ))

    # Test
    keyboard.add(InlineKeyboardButton(
        "📝 Test",
        callback_data=f"admin:test:view:{lesson_id}"
    ))

    # Tahrirlash
    keyboard.add(InlineKeyboardButton(
        "✏️ Tahrirlash",
        callback_data=f"admin:lesson:edit:{lesson_id}"
    ))

    # Bepul/Pullik
    if is_free:
        keyboard.add(InlineKeyboardButton(
            "💰 Pullik qilish",
            callback_data=f"admin:lesson:paid:{lesson_id}"
        ))
    else:
        keyboard.add(InlineKeyboardButton(
            "🆓 Bepul qilish",
            callback_data=f"admin:lesson:free:{lesson_id}"
        ))

    # O'chirish
    keyboard.add(InlineKeyboardButton(
        "🗑 O'chirish",
        callback_data=f"admin:lesson:delete:{lesson_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:lesson:list:{module_id}"
    ))

    return keyboard


def lesson_edit_menu(lesson_id: int) -> InlineKeyboardMarkup:
    """Dars tahrirlash menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📝 Nom", callback_data=f"admin:lesson:edit:name:{lesson_id}"),
        InlineKeyboardButton("📄 Tavsif", callback_data=f"admin:lesson:edit:desc:{lesson_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🎬 Video", callback_data=f"admin:lesson:edit:video:{lesson_id}"),
        InlineKeyboardButton("🔢 Tartib", callback_data=f"admin:lesson:edit:order:{lesson_id}")
    )
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:lesson:view:{lesson_id}"
    ))

    return keyboard


# ============================================================
#                    MATERIALLAR
# ============================================================

def materials_list(lesson_id: int, materials: List[Dict]) -> InlineKeyboardMarkup:
    """Materiallar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    file_icons = {
        'pdf': '📕',
        'pptx': '📊',
        'docx': '📄',
        'xlsx': '📗',
        'image': '🖼',
        'other': '📎'
    }

    for material in materials:
        icon = file_icons.get(material.get('file_type', 'other'), '📎')
        keyboard.add(InlineKeyboardButton(
            f"{icon} {material['name']}",
            callback_data=f"admin:material:view:{material['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "➕ Yangi material",
        callback_data=f"admin:material:add:{lesson_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:lesson:view:{lesson_id}"
    ))

    return keyboard


def material_detail(material_id: int, lesson_id: int) -> InlineKeyboardMarkup:
    """Material tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(InlineKeyboardButton(
        "📥 Yuklab olish",
        callback_data=f"admin:material:download:{material_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "✏️ Tahrirlash",
        callback_data=f"admin:material:edit:{material_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "🗑 O'chirish",
        callback_data=f"admin:material:delete:{material_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:material:list:{lesson_id}"
    ))

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
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:material:list:{lesson_id}"
    ))

    return keyboard


# ============================================================
#                    TEST
# ============================================================

def test_menu(lesson_id: int, has_test: bool) -> InlineKeyboardMarkup:
    """Test menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if has_test:
        keyboard.add(InlineKeyboardButton(
            "📋 Savollar",
            callback_data=f"admin:test:questions:{lesson_id}"
        ))
        keyboard.add(InlineKeyboardButton(
            "➕ Savol qo'shish",
            callback_data=f"admin:test:add_q:{lesson_id}"
        ))
        keyboard.add(InlineKeyboardButton(
            "📤 Excel yuklash",
            callback_data=f"admin:test:upload:{lesson_id}"
        ))
        keyboard.add(InlineKeyboardButton(
            "⚙️ Sozlamalar",
            callback_data=f"admin:test:settings:{lesson_id}"
        ))
        keyboard.add(InlineKeyboardButton(
            "🗑 Testni o'chirish",
            callback_data=f"admin:test:delete:{lesson_id}"
        ))
    else:
        keyboard.add(InlineKeyboardButton(
            "➕ Test yaratish",
            callback_data=f"admin:test:create:{lesson_id}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:lesson:view:{lesson_id}"
    ))

    return keyboard


def test_questions_list(lesson_id: int, questions: List[Dict]) -> InlineKeyboardMarkup:
    """Test savollari ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for i, q in enumerate(questions, 1):
        # Savolni qisqartirish
        q_text = q.get('question_text', '')[:30]
        if len(q.get('question_text', '')) > 30:
            q_text += "..."

        keyboard.add(InlineKeyboardButton(
            f"{i}. {q_text}",
            callback_data=f"admin:question:view:{q['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "➕ Savol qo'shish",
        callback_data=f"admin:test:add_q:{lesson_id}"
    ))

    if questions:
        keyboard.add(InlineKeyboardButton(
            "🗑 Barchasini o'chirish",
            callback_data=f"admin:test:clear:{lesson_id}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:test:view:{lesson_id}"
    ))

    return keyboard


def question_detail(question_id: int, lesson_id: int) -> InlineKeyboardMarkup:
    """Savol tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(InlineKeyboardButton(
        "✏️ Tahrirlash",
        callback_data=f"admin:question:edit:{question_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "🗑 O'chirish",
        callback_data=f"admin:question:delete:{question_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:test:questions:{lesson_id}"
    ))

    return keyboard


def test_settings(lesson_id: int, test_id: int) -> InlineKeyboardMarkup:
    """Test sozlamalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "📊 O'tish balini o'zgartirish",
        callback_data=f"admin:test:set:pass:{test_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⏱ Vaqt chegarasi",
        callback_data=f"admin:test:set:time:{test_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"admin:test:view:{lesson_id}"
    ))

    return keyboard


def correct_answer_select(lesson_id: int) -> InlineKeyboardMarkup:
    """To'g'ri javob tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=4)

    keyboard.add(
        InlineKeyboardButton("🅰️ A", callback_data=f"admin:answer:A:{lesson_id}"),
        InlineKeyboardButton("🅱️ B", callback_data=f"admin:answer:B:{lesson_id}"),
        InlineKeyboardButton("🅲 C", callback_data=f"admin:answer:C:{lesson_id}"),
        InlineKeyboardButton("🅳 D", callback_data=f"admin:answer:D:{lesson_id}")
    )

    return keyboard


# ============================================================
#                    FOYDALANUVCHILAR
# ============================================================

def users_menu() -> InlineKeyboardMarkup:
    """Foydalanuvchilar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📋 Barcha", callback_data="admin:users:all"),
        InlineKeyboardButton("🔍 Qidirish", callback_data="admin:users:search")
    )
    keyboard.add(
        InlineKeyboardButton("💰 Pullik", callback_data="admin:users:paid"),
        InlineKeyboardButton("🏆 Top", callback_data="admin:users:top")
    )
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:main"
    ))

    return keyboard


# ============================================================
#                    TO'LOVLAR
# ============================================================

def payments_menu() -> InlineKeyboardMarkup:
    """To'lovlar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("⏳ Kutilayotgan", callback_data="admin:payments:pending"),
        InlineKeyboardButton("✅ Tasdiqlangan", callback_data="admin:payments:approved")
    )
    keyboard.add(
        InlineKeyboardButton("❌ Rad etilgan", callback_data="admin:payments:rejected"),
        InlineKeyboardButton("📊 Statistika", callback_data="admin:payments:stats")
    )
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:main"
    ))

    return keyboard


# ============================================================
#                    HISOBOTLAR
# ============================================================

def reports_menu() -> InlineKeyboardMarkup:
    """Hisobotlar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📊 Umumiy", callback_data="admin:report:general"),
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin:report:users")
    )
    keyboard.add(
        InlineKeyboardButton("💰 Moliyaviy", callback_data="admin:report:finance"),
        InlineKeyboardButton("📚 Kurslar", callback_data="admin:report:courses")
    )
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:main"
    ))

    return keyboard


# ============================================================
#                    FIKRLAR
# ============================================================

def feedbacks_menu() -> InlineKeyboardMarkup:
    """Fikrlar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📋 So'nggi", callback_data="admin:feedbacks:recent"),
        InlineKeyboardButton("⭐️ Yulduz bo'yicha", callback_data="admin:feedbacks:rating")
    )
    keyboard.add(
        InlineKeyboardButton("📊 Statistika", callback_data="admin:feedbacks:stats")
    )
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:main"
    ))

    return keyboard


# ============================================================
#                    SOZLAMALAR
# ============================================================

def settings_menu() -> InlineKeyboardMarkup:
    """Sozlamalar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "💬 Fikr sozlamalari",
        callback_data="admin:settings:feedback"
    ))
    keyboard.add(InlineKeyboardButton(
        "📝 Test sozlamalari",
        callback_data="admin:settings:test"
    ))
    keyboard.add(InlineKeyboardButton(
        "🎓 Sertifikat sozlamalari",
        callback_data="admin:settings:cert"
    ))
    keyboard.add(InlineKeyboardButton(
        "👨‍💼 Adminlar",
        callback_data="admin:settings:admins"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:main"
    ))

    return keyboard


# ============================================================
#                    BROADCAST
# ============================================================

def broadcast_menu() -> InlineKeyboardMarkup:
    """Ommaviy xabar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📢 Barchaga", callback_data="admin:broadcast:all"),
        InlineKeyboardButton("💰 Pullik", callback_data="admin:broadcast:paid")
    )
    keyboard.add(
        InlineKeyboardButton("🆓 Bepul", callback_data="admin:broadcast:free"),
        InlineKeyboardButton("📚 Kurs bo'yicha", callback_data="admin:broadcast:course")
    )
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="admin:main"
    ))

    return keyboard


# ============================================================
#                    YORDAMCHI TUGMALAR
# ============================================================

def confirm_action(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Amalni tasdiqlash"""
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