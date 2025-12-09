"""
User Inline Keyboards
=====================
Foydalanuvchi uchun barcha inline tugmalar
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Optional


# ============================================================
#                    ASOSIY MENYU
# ============================================================

def main_menu_inline() -> InlineKeyboardMarkup:
    """Bosh menyu (inline)"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📚 Mening kurslarim", callback_data="user:my_courses"),
        InlineKeyboardButton("🆓 Bepul darslar", callback_data="user:free_lessons")
    )
    keyboard.add(
        InlineKeyboardButton("🛒 Kurs sotib olish", callback_data="user:courses"),
        InlineKeyboardButton("📊 Natijalarim", callback_data="user:results")
    )
    keyboard.add(
        InlineKeyboardButton("❓ Yordam", callback_data="user:help")
    )

    return keyboard


# ============================================================
#                    KURSLAR
# ============================================================

def courses_list(courses: List[Dict], user_id: int = None) -> InlineKeyboardMarkup:
    """Kurslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for course in courses:
        # Status belgisi
        if course.get('has_access'):
            icon = "✅"
        else:
            icon = "🔒"

        # Narx
        price = course.get('price', 0)
        price_text = f" - {price:,.0f} so'm" if price > 0 and not course.get('has_access') else ""

        keyboard.add(InlineKeyboardButton(
            f"{icon} {course['name']}{price_text}",
            callback_data=f"user:course:view:{course['id']}"
        ))

    keyboard.add(InlineKeyboardButton("🏠 Bosh menyu", callback_data="user:main"))

    return keyboard


def course_detail(course_id: int, has_access: bool, has_free_lessons: bool = False) -> InlineKeyboardMarkup:
    """Kurs tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if has_access:
        # Dostup bor
        keyboard.add(InlineKeyboardButton(
            "📁 Modullar",
            callback_data=f"user:modules:{course_id}"
        ))
        keyboard.add(InlineKeyboardButton(
            "📊 Mening progressim",
            callback_data=f"user:progress:{course_id}"
        ))
    else:
        # Dostup yo'q
        keyboard.add(InlineKeyboardButton(
            "🛒 Sotib olish",
            callback_data=f"user:buy:{course_id}"
        ))

        if has_free_lessons:
            keyboard.add(InlineKeyboardButton(
                "🆓 Bepul darslar",
                callback_data=f"user:free_lessons:{course_id}"
            ))

    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="user:courses"))

    return keyboard


# ============================================================
#                    MODULLAR
# ============================================================

def modules_list(course_id: int, modules: List[Dict]) -> InlineKeyboardMarkup:
    """Modullar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for module in modules:
        # Progress belgisi
        completed = module.get('completed', 0)
        total = module.get('total', 0)

        if total > 0:
            if completed == total:
                icon = "✅"  # Tugagan
            elif completed > 0:
                icon = "🔄"  # Jarayonda
            else:
                icon = "📁"  # Boshlanmagan
        else:
            icon = "📁"

        progress_text = f" ({completed}/{total})" if total > 0 else ""

        keyboard.add(InlineKeyboardButton(
            f"{icon} {module['name']}{progress_text}",
            callback_data=f"user:lessons:{module['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:course:view:{course_id}"
    ))

    return keyboard


# ============================================================
#                    DARSLAR
# ============================================================

def lessons_list(module_id: int, lessons: List[Dict], has_access: bool) -> InlineKeyboardMarkup:
    """Darslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        status = lesson.get('status', 'locked')

        # Status belgisi
        if status == 'completed':
            icon = "✅"
        elif status == 'unlocked' or status == 'free':
            icon = "🔓"
        elif lesson.get('is_free'):
            icon = "🆓"
        else:
            icon = "🔒"

        # Test belgisi
        test_mark = " 📝" if lesson.get('has_test') else ""

        # Tugma
        if status == 'locked' and not lesson.get('is_free'):
            # Yopiq dars - bosilmaydi
            keyboard.add(InlineKeyboardButton(
                f"{icon} {lesson['name']}{test_mark}",
                callback_data=f"user:locked:{lesson['id']}"
            ))
        else:
            keyboard.add(InlineKeyboardButton(
                f"{icon} {lesson['name']}{test_mark}",
                callback_data=f"user:lesson:view:{lesson['id']}"
            ))

    # Orqaga tugmasi - modulning kursiga
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:module:back:{module_id}"
    ))

    return keyboard


def lesson_view(
        lesson_id: int,
        module_id: int,
        has_video: bool = False,
        has_materials: bool = False,
        has_test: bool = False,
        is_completed: bool = False,
        has_access: bool = True,
        next_lesson_id: int = None
) -> InlineKeyboardMarkup:
    """Darsni ko'rish"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Video
    if has_video:
        keyboard.add(InlineKeyboardButton(
            "▶️ Video ko'rish",
            callback_data=f"user:video:{lesson_id}"
        ))

    # Materiallar
    if has_materials:
        keyboard.add(InlineKeyboardButton(
            "📎 Materiallar",
            callback_data=f"user:materials:{lesson_id}"
        ))

    # Test
    if has_test:
        keyboard.add(InlineKeyboardButton(
            "📝 Test yechish",
            callback_data=f"user:test:start:{lesson_id}"
        ))

    # Fikr qoldirish
    if has_access:
        keyboard.add(InlineKeyboardButton(
            "💬 Fikr qoldirish",
            callback_data=f"user:feedback:{lesson_id}"
        ))

    # Keyingi dars (faqat tugallangan bo'lsa)
    if is_completed and next_lesson_id:
        keyboard.add(InlineKeyboardButton(
            "⏭ Keyingi dars",
            callback_data=f"user:next_lesson:{next_lesson_id}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:lessons:{module_id}"
    ))

    return keyboard


def lesson_completed_menu(
        lesson_id: int,
        module_id: int,
        next_lesson_id: int = None,
        has_test: bool = False
) -> InlineKeyboardMarkup:
    """Dars tugagandan keyin menyu"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Test
    if has_test:
        keyboard.add(InlineKeyboardButton(
            "📝 Test yechish",
            callback_data=f"user:test:start:{lesson_id}"
        ))

    # Keyingi dars
    if next_lesson_id:
        keyboard.add(InlineKeyboardButton(
            "⏭ Keyingi dars",
            callback_data=f"user:next_lesson:{next_lesson_id}"
        ))

    keyboard.add(InlineKeyboardButton(
        "📁 Barcha darslar",
        callback_data=f"user:lessons:{module_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "🏠 Bosh menyu",
        callback_data="user:main"
    ))

    return keyboard


# ============================================================
#                    BEPUL DARSLAR
# ============================================================

def free_lessons_list(lessons: List[Dict]) -> InlineKeyboardMarkup:
    """Bepul darslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        keyboard.add(InlineKeyboardButton(
            f"🆓 {lesson['name']}",
            callback_data=f"user:lesson:view:{lesson['id']}"
        ))

    keyboard.add(InlineKeyboardButton("🏠 Bosh menyu", callback_data="user:main"))

    return keyboard


def free_lessons_in_course(course_id: int, lessons: List[Dict]) -> InlineKeyboardMarkup:
    """Kurs ichidagi bepul darslar"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        keyboard.add(InlineKeyboardButton(
            f"🆓 {lesson['name']}",
            callback_data=f"user:lesson:view:{lesson['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:course:view:{course_id}"
    ))

    return keyboard


# ============================================================
#                    MATERIALLAR
# ============================================================

def materials_list(lesson_id: int, materials: List[Dict]) -> InlineKeyboardMarkup:
    """Materiallar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Fayl ikonkalari
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
            callback_data=f"user:material:download:{material['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:lesson:view:{lesson_id}"
    ))

    return keyboard


# ============================================================
#                    TO'LOV
# ============================================================

def payment_methods(course_id: int) -> InlineKeyboardMarkup:
    """To'lov usullari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "💳 Karta orqali to'lash",
        callback_data=f"user:pay:card:{course_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:course:view:{course_id}"
    ))

    return keyboard


def payment_pending(course_id: int) -> InlineKeyboardMarkup:
    """To'lov kutilmoqda"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "🔄 Statusni tekshirish",
        callback_data=f"user:payment_status:{course_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "🏠 Bosh menyu",
        callback_data="user:main"
    ))

    return keyboard


# ============================================================
#                    TEST
# ============================================================

def test_start(lesson_id: int) -> InlineKeyboardMarkup:
    """Test boshlash"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "▶️ Testni boshlash",
        callback_data=f"user:test:begin:{lesson_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:lesson:view:{lesson_id}"
    ))

    return keyboard


def test_question(test_id: int, question_index: int, options: List[str]) -> InlineKeyboardMarkup:
    """Test savoli javoblari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Javob variantlari
    option_icons = {'A': '🅰️', 'B': '🅱️', 'C': '🅲', 'D': '🅳'}

    buttons = []
    for option in options:
        icon = option_icons.get(option, option)
        buttons.append(InlineKeyboardButton(
            f"{icon} {option}",
            callback_data=f"user:test:answer:{question_index}:{option}"
        ))

    # 2 tadan qo'yish
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.row(buttons[i], buttons[i + 1])
        else:
            keyboard.row(buttons[i])

    # Bekor qilish
    keyboard.add(InlineKeyboardButton(
        "❌ Bekor qilish",
        callback_data="user:test:cancel"
    ))

    return keyboard


def test_result(lesson_id: int, passed: bool, can_retry: bool = True, next_lesson_id: int = None) -> InlineKeyboardMarkup:
    """Test natijasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if passed:
        # O'tdi - keyingi darsga o'tish
        if next_lesson_id:
            keyboard.add(InlineKeyboardButton(
                "⏭ Keyingi dars",
                callback_data=f"user:next_lesson:{next_lesson_id}"
            ))
    else:
        # O'tmadi - qayta topshirish
        if can_retry:
            keyboard.add(InlineKeyboardButton(
                "🔄 Qayta topshirish",
                callback_data=f"user:test:retry:{lesson_id}"
            ))

    keyboard.add(InlineKeyboardButton(
        "📊 Test tarixi",
        callback_data=f"user:test:history:{lesson_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Darsga qaytish",
        callback_data=f"user:lesson:view:{lesson_id}"
    ))

    return keyboard
# ============================================================
#                    FIKR
# ============================================================

def feedback_rating(lesson_id: int) -> InlineKeyboardMarkup:
    """Baho berish tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=5)

    # 1-5 yulduz
    buttons = []
    for i in range(1, 6):
        stars = "⭐️" * i
        buttons.append(InlineKeyboardButton(
            str(i),
            callback_data=f"user:rate:{i}"
        ))

    keyboard.row(*buttons)

    keyboard.add(InlineKeyboardButton(
        "❌ Bekor qilish",
        callback_data=f"user:lesson:view:{lesson_id}"
    ))

    return keyboard


def feedback_skip_comment(lesson_id: int) -> InlineKeyboardMarkup:
    """Izohni o'tkazib yuborish"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "⏩ O'tkazib yuborish",
        callback_data=f"user:feedback:skip:{lesson_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "❌ Bekor qilish",
        callback_data=f"user:lesson:view:{lesson_id}"
    ))

    return keyboard


def feedback_thanks(lesson_id: int) -> InlineKeyboardMarkup:
    """Fikr uchun rahmat"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "⬅️ Darsga qaytish",
        callback_data=f"user:lesson:view:{lesson_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "🏠 Bosh menyu",
        callback_data="user:main"
    ))

    return keyboard


def feedback_prompt(lesson_id: int) -> InlineKeyboardMarkup:
    """Fikr qoldirish so'rovi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "💬 Fikr qoldirish",
        callback_data=f"user:feedback:{lesson_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:lesson:view:{lesson_id}"
    ))

    return keyboard


# ============================================================
#                    NATIJALAR
# ============================================================

def my_results_menu() -> InlineKeyboardMarkup:
    """Natijalar menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "📊 Kurs progressi",
        callback_data="user:my_progress"
    ))

    keyboard.add(InlineKeyboardButton(
        "📝 Test natijalari",
        callback_data="user:test_results"
    ))

    keyboard.add(InlineKeyboardButton(
        "🎓 Sertifikatlar",
        callback_data="user:certificates"
    ))

    keyboard.add(InlineKeyboardButton(
        "🏠 Bosh menyu",
        callback_data="user:main"
    ))

    return keyboard


def course_progress_detail(courses: List[Dict]) -> InlineKeyboardMarkup:
    """Kurs progressi ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for course in courses:
        percentage = course.get('percentage', 0)

        # Progress belgisi
        if percentage >= 100:
            icon = "✅"
        elif percentage > 0:
            icon = "🔄"
        else:
            icon = "📚"

        keyboard.add(InlineKeyboardButton(
            f"{icon} {course['name']} ({percentage:.0f}%)",
            callback_data=f"user:progress:{course['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:results"
    ))

    return keyboard


def test_results_list(results: List[Dict]) -> InlineKeyboardMarkup:
    """Test natijalari ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Faqat orqaga tugmasi
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:results"
    ))

    return keyboard


def certificates_list(certificates: List[Dict]) -> InlineKeyboardMarkup:
    """Sertifikatlar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    grade_icons = {'GOLD': '🥇', 'SILVER': '🥈', 'BRONZE': '🥉', 'PARTICIPANT': '📜'}

    for cert in certificates:
        icon = grade_icons.get(cert.get('grade', 'PARTICIPANT'), '📜')

        keyboard.add(InlineKeyboardButton(
            f"{icon} {cert['course_name']}",
            callback_data=f"user:certificate:view:{cert['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:results"
    ))

    return keyboard


# ============================================================
#                    YORDAM
# ============================================================

def help_menu() -> InlineKeyboardMarkup:
    """Yordam menyusi (bosh sahifada)"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📚 Kurslar", callback_data="user:help:courses"),
        InlineKeyboardButton("💰 To'lov", callback_data="user:help:payment")
    )
    keyboard.add(
        InlineKeyboardButton("📝 Testlar", callback_data="user:help:tests"),
        InlineKeyboardButton("🎓 Sertifikat", callback_data="user:help:certificate")
    )
    keyboard.add(
        InlineKeyboardButton("📞 Bog'lanish", callback_data="user:help:contact")
    )
    keyboard.add(
        InlineKeyboardButton("🏠 Bosh menyu", callback_data="user:main")
    )

    return keyboard


def help_topics() -> InlineKeyboardMarkup:
    """Yordam mavzulari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("📚 Kurslar", callback_data="user:help:courses"),
        InlineKeyboardButton("💰 To'lov", callback_data="user:help:payment")
    )
    keyboard.add(
        InlineKeyboardButton("📝 Testlar", callback_data="user:help:tests"),
        InlineKeyboardButton("🎓 Sertifikat", callback_data="user:help:certificate")
    )
    keyboard.add(
        InlineKeyboardButton("❓ FAQ", callback_data="user:faq")
    )
    keyboard.add(
        InlineKeyboardButton("📞 Bog'lanish", callback_data="user:help:contact")
    )
    keyboard.add(
        InlineKeyboardButton("🏠 Bosh menyu", callback_data="user:main")
    )

    return keyboard


def contact_options() -> InlineKeyboardMarkup:
    """Bog'lanish variantlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "💬 Xabar yuborish",
        callback_data="user:contact:message"
    ))

    keyboard.add(InlineKeyboardButton(
        "📞 Telefon raqam",
        callback_data="user:contact:phone"
    ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:help"
    ))

    return keyboard


# ============================================================
#                    YORDAMCHI TUGMALAR
# ============================================================

def back_button(callback_data: str) -> InlineKeyboardMarkup:
    """Orqaga tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data=callback_data))
    return keyboard


def close_button() -> InlineKeyboardMarkup:
    """Yopish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Yopish", callback_data="user:close"))
    return keyboard


def confirm_inline(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """Tasdiqlash tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=yes_callback),
        InlineKeyboardButton("❌ Yo'q", callback_data=no_callback)
    )
    return keyboard


def pagination(
        current_page: int,
        total_pages: int,
        callback_prefix: str
) -> InlineKeyboardMarkup:
    """Sahifalash tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=3)

    buttons = []

    # Oldingi
    if current_page > 1:
        buttons.append(InlineKeyboardButton(
            "◀️",
            callback_data=f"{callback_prefix}:{current_page - 1}"
        ))
    else:
        buttons.append(InlineKeyboardButton(" ", callback_data="user:noop"))

    # Joriy
    buttons.append(InlineKeyboardButton(
        f"{current_page}/{total_pages}",
        callback_data="user:noop"
    ))

    # Keyingi
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(
            "▶️",
            callback_data=f"{callback_prefix}:{current_page + 1}"
        ))
    else:
        buttons.append(InlineKeyboardButton(" ", callback_data="user:noop"))

    keyboard.row(*buttons)

    return keyboard


def cancel_button(callback_data: str = "user:cancel") -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=callback_data))
    return keyboard


def payment_cancel_button(course_id: int = None) -> InlineKeyboardMarkup:
    """To'lovni bekor qilish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    if course_id:
        keyboard.add(InlineKeyboardButton(
            "❌ Bekor qilish",
            callback_data=f"user:payment:cancel:{course_id}"
        ))
    else:
        keyboard.add(InlineKeyboardButton(
            "❌ Bekor qilish",
            callback_data="user:cancel"
        ))
    return keyboard