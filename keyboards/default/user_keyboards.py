"""
User Keyboards
==============
O'quv markaz bot - Foydalanuvchilar uchun barcha tugmalar
"""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from typing import List, Dict, Optional




def main_menu() -> ReplyKeyboardMarkup:
    """Asosiy menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📚 Mening kurslarim"),
        KeyboardButton("📖 Bepul darslar")
    )
    keyboard.add(
        KeyboardButton("💰 Kurs sotib olish"),
        KeyboardButton("📊 Natijalarim")
    )
    keyboard.add(
        KeyboardButton("ℹ️ Yordam")
    )
    return keyboard


def back_to_main() -> ReplyKeyboardMarkup:
    """Bosh menyuga qaytish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🏠 Bosh menyu"))
    return keyboard


def back_button() -> ReplyKeyboardMarkup:
    """Orqaga tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("⬅️ Orqaga"))
    keyboard.add(KeyboardButton("🏠 Bosh menyu"))
    return keyboard


def cancel_button() -> ReplyKeyboardMarkup:
    """Bekor qilish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def skip_button() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("⏩ O'tkazib yuborish"))
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def phone_request() -> ReplyKeyboardMarkup:
    """Telefon raqam so'rash"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    keyboard.add(KeyboardButton("⏩ O'tkazib yuborish"))
    return keyboard


def confirm_keyboard() -> ReplyKeyboardMarkup:
    """Tasdiqlash"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("✅ Ha"),
        KeyboardButton("❌ Yo'q")
    )
    return keyboard


# ============================================================
#                    KURSLAR
# ============================================================

def courses_list(courses: List[Dict], has_access: Dict = None) -> InlineKeyboardMarkup:
    """Kurslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if has_access is None:
        has_access = {}

    for course in courses:
        # Dostup belgisi
        if has_access.get(course['id']):
            icon = "✅"
        else:
            icon = "🔒"

        keyboard.add(
            InlineKeyboardButton(
                f"{icon} {course['name']}",
                callback_data=f"course:view:{course['id']}"
            )
        )

    return keyboard


def course_detail(course_id: int, has_access: bool = False, price: float = 0) -> InlineKeyboardMarkup:
    """Kurs tafsilotlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if has_access:
        keyboard.add(
            InlineKeyboardButton("📚 Darslarni ko'rish", callback_data=f"course:lessons:{course_id}"),
            InlineKeyboardButton("📊 Mening progressim", callback_data=f"course:progress:{course_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("📖 Bepul darslar", callback_data=f"course:free:{course_id}"),
            InlineKeyboardButton(
                f"💰 Sotib olish ({price:,.0f} so'm)",
                callback_data=f"course:buy:{course_id}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="courses:list")
    )
    return keyboard


def free_lessons_list(course_id: int, lessons: List[Dict]) -> InlineKeyboardMarkup:
    """Bepul darslar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        keyboard.add(
            InlineKeyboardButton(
                f"🆓 {lesson['order_num']}. {lesson['name']}",
                callback_data=f"lesson:view:{lesson['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("💰 To'liq kursni sotib olish", callback_data=f"course:buy:{course_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"course:view:{course_id}")
    )
    return keyboard


# ============================================================
#                    MODULLAR VA DARSLAR
# ============================================================

def modules_list(course_id: int, modules: List[Dict], progress: Dict = None) -> InlineKeyboardMarkup:
    """Modullar ro'yxati (progress bilan)"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if progress is None:
        progress = {}

    for module in modules:
        # Modul progressi
        module_progress = progress.get(module['id'], 0)
        if module_progress >= 100:
            icon = "✅"
        elif module_progress > 0:
            icon = "🔄"
        else:
            icon = "📁"

        keyboard.add(
            InlineKeyboardButton(
                f"{icon} {module['order_num']}. {module['name']}",
                callback_data=f"module:view:{module['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("📊 Umumiy progress", callback_data=f"course:progress:{course_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"course:view:{course_id}")
    )
    return keyboard


def lessons_list(module_id: int, lessons: List[Dict]) -> InlineKeyboardMarkup:
    """Darslar ro'yxati (status bilan)"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        status = lesson.get('status', 'locked')

        # Status ikonkalari
        if status == 'completed':
            icon = "✅"
        elif status == 'unlocked':
            icon = "🔓"
        else:  # locked
            icon = "🔒"

        # Qo'shimcha belgilar
        extras = ""
        if lesson.get('is_free'):
            extras += " 🆓"
        if lesson.get('has_test'):
            extras += " 📝"

        keyboard.add(
            InlineKeyboardButton(
                f"{icon} {lesson['order_num']}. {lesson['name']}{extras}",
                callback_data=f"lesson:view:{lesson['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"module:view:{module_id}")
    )
    return keyboard


def lesson_view(lesson_id: int, module_id: int, status: str = 'locked', has_test: bool = False,
                has_materials: bool = False) -> InlineKeyboardMarkup:
    """Dars ko'rish tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if status == 'locked':
        keyboard.add(
            InlineKeyboardButton("🔒 Bu dars hali ochilmagan", callback_data="lesson:locked")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("▶️ Videoni ko'rish", callback_data=f"lesson:video:{lesson_id}")
        )

        if has_materials:
            keyboard.add(
                InlineKeyboardButton("📎 Materiallar", callback_data=f"lesson:materials:{lesson_id}")
            )

        if status == 'unlocked':
            keyboard.add(
                InlineKeyboardButton("✅ Darsni tugatdim", callback_data=f"lesson:complete:{lesson_id}")
            )

        if has_test and status == 'completed':
            keyboard.add(
                InlineKeyboardButton("📝 Testni boshlash", callback_data=f"test:start:{lesson_id}")
            )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"lesson:list:{module_id}")
    )
    return keyboard


def lesson_completed(lesson_id: int, has_test: bool = False) -> InlineKeyboardMarkup:
    """Dars tugagandan keyin"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if has_test:
        keyboard.add(
            InlineKeyboardButton("📝 Testni boshlash", callback_data=f"test:start:{lesson_id}")
        )

    keyboard.add(
        InlineKeyboardButton("➡️ Keyingi dars", callback_data=f"lesson:next:{lesson_id}"),
        InlineKeyboardButton("📚 Darslar ro'yxati", callback_data=f"lesson:back:{lesson_id}")
    )
    return keyboard


# ============================================================
#                    MATERIALLAR
# ============================================================

def materials_list(lesson_id: int, materials: List[Dict]) -> InlineKeyboardMarkup:
    """Dars materiallari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

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
                callback_data=f"material:download:{material['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"lesson:view:{lesson_id}")
    )
    return keyboard


# ============================================================
#                    TESTLAR
# ============================================================

def test_start(lesson_id: int, questions_count: int, passing_score: int) -> InlineKeyboardMarkup:
    """Test boshlash"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("▶️ Boshlash", callback_data=f"test:begin:{lesson_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"lesson:view:{lesson_id}")
    )
    return keyboard


def test_question(question_id: int, question_num: int, total: int, has_c: bool = True,
                  has_d: bool = True) -> InlineKeyboardMarkup:
    """Test savoli javoblari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("🅰️ A", callback_data=f"test:answer:{question_id}:A"),
        InlineKeyboardButton("🅱️ B", callback_data=f"test:answer:{question_id}:B")
    )

    if has_c and has_d:
        keyboard.add(
            InlineKeyboardButton("🅲 C", callback_data=f"test:answer:{question_id}:C"),
            InlineKeyboardButton("🅳 D", callback_data=f"test:answer:{question_id}:D")
        )
    elif has_c:
        keyboard.add(
            InlineKeyboardButton("🅲 C", callback_data=f"test:answer:{question_id}:C")
        )

    return keyboard


def test_result(lesson_id: int, passed: bool, score: int) -> InlineKeyboardMarkup:
    """Test natijasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if not passed:
        keyboard.add(
            InlineKeyboardButton("🔄 Qayta urinish", callback_data=f"test:start:{lesson_id}")
        )

    keyboard.add(
        InlineKeyboardButton("➡️ Keyingi dars", callback_data=f"lesson:next:{lesson_id}"),
        InlineKeyboardButton("📚 Darslar ro'yxati", callback_data=f"lesson:back:{lesson_id}")
    )
    return keyboard


# ============================================================
#                    FIKR-MULOHAZA
# ============================================================

def feedback_rating() -> InlineKeyboardMarkup:
    """Fikr yulduzlari"""
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(
        InlineKeyboardButton("⭐", callback_data="feedback:rate:1"),
        InlineKeyboardButton("⭐⭐", callback_data="feedback:rate:2"),
        InlineKeyboardButton("⭐⭐⭐", callback_data="feedback:rate:3"),
        InlineKeyboardButton("⭐⭐⭐⭐", callback_data="feedback:rate:4"),
        InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="feedback:rate:5")
    )
    return keyboard


def feedback_comment(lesson_id: int, is_required: bool = False) -> InlineKeyboardMarkup:
    """Fikr izoh"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if not is_required:
        keyboard.add(
            InlineKeyboardButton("⏩ O'tkazib yuborish", callback_data=f"feedback:skip:{lesson_id}")
        )

    return keyboard


def feedback_thanks(lesson_id: int) -> InlineKeyboardMarkup:
    """Fikr uchun rahmat"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➡️ Davom etish", callback_data=f"lesson:next:{lesson_id}")
    )
    return keyboard


# ============================================================
#                    TO'LOV
# ============================================================

def payment_methods(course_id: int) -> InlineKeyboardMarkup:
    """To'lov usullari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💳 Karta orqali (Click/Payme)", callback_data=f"pay:card:{course_id}"),
        InlineKeyboardButton("💵 Naqd pul", callback_data=f"pay:cash:{course_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"course:view:{course_id}")
    )
    return keyboard


def payment_card_info(course_id: int) -> InlineKeyboardMarkup:
    """Karta to'lov ma'lumotlari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📎 Chek yuborish", callback_data=f"pay:receipt:{course_id}"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data=f"pay:methods:{course_id}")
    )
    return keyboard


def payment_confirm(course_id: int) -> InlineKeyboardMarkup:
    """To'lovni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Yuborish", callback_data=f"pay:submit:{course_id}"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data=f"pay:cancel:{course_id}")
    )
    return keyboard


def payment_pending() -> InlineKeyboardMarkup:
    """To'lov kutilmoqda"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 Status tekshirish", callback_data="pay:check"),
        InlineKeyboardButton("🏠 Bosh menyu", callback_data="main:menu")
    )
    return keyboard


def payment_success(course_id: int) -> InlineKeyboardMarkup:
    """To'lov muvaffaqiyatli"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📚 Kursni boshlash", callback_data=f"course:lessons:{course_id}"),
        InlineKeyboardButton("🏠 Bosh menyu", callback_data="main:menu")
    )
    return keyboard


# ============================================================
#                    PROGRESS VA NATIJALAR
# ============================================================

def my_results() -> InlineKeyboardMarkup:
    """Mening natijalarim menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 Umumiy progress", callback_data="results:progress"),
        InlineKeyboardButton("🏆 Mening ballarim", callback_data="results:score"),
        InlineKeyboardButton("📝 Test natijalari", callback_data="results:tests"),
        InlineKeyboardButton("📜 Sertifikatlar", callback_data="results:certs"),
        InlineKeyboardButton("🏠 Bosh menyu", callback_data="main:menu")
    )
    return keyboard


def course_progress(course_id: int, percentage: int, can_get_cert: bool = False) -> InlineKeyboardMarkup:
    """Kurs progressi"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton("📚 Davom etish", callback_data=f"course:lessons:{course_id}")
    )

    if can_get_cert:
        keyboard.add(
            InlineKeyboardButton("📜 Sertifikat olish", callback_data=f"cert:get:{course_id}")
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="results:progress")
    )
    return keyboard


def test_results_list(results: List[Dict]) -> InlineKeyboardMarkup:
    """Test natijalari ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for result in results:
        passed = "✅" if result['passed'] else "❌"
        keyboard.add(
            InlineKeyboardButton(
                f"{passed} {result['lesson_name']} - {result['score']}%",
                callback_data=f"results:test:{result['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="results")
    )
    return keyboard


# ============================================================
#                    SERTIFIKAT
# ============================================================

def certificate_view(course_id: int, has_file: bool = False) -> InlineKeyboardMarkup:
    """Sertifikat ko'rish"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if has_file:
        keyboard.add(
            InlineKeyboardButton("📥 Yuklab olish", callback_data=f"cert:download:{course_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("🔄 Yaratish", callback_data=f"cert:generate:{course_id}")
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="results:certs")
    )
    return keyboard


def certificates_list(certificates: List[Dict]) -> InlineKeyboardMarkup:
    """Sertifikatlar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    grade_icons = {
        'GOLD': '🥇',
        'SILVER': '🥈',
        'BRONZE': '🥉',
        'PARTICIPANT': '📜'
    }

    for cert in certificates:
        icon = grade_icons.get(cert.get('grade', 'PARTICIPANT'), '📜')
        keyboard.add(
            InlineKeyboardButton(
                f"{icon} {cert['course_name']} - {cert['percentage']:.0f}%",
                callback_data=f"cert:view:{cert['course_id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("⬅️ Orqaga", callback_data="results")
    )
    return keyboard


# ============================================================
#                    YORDAM
# ============================================================

def help_menu() -> InlineKeyboardMarkup:
    """Yordam menyusi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📖 Qanday ishlaydi?", callback_data="help:how"),
        InlineKeyboardButton("💰 To'lov haqida", callback_data="help:payment"),
        InlineKeyboardButton("📝 Testlar haqida", callback_data="help:tests"),
        InlineKeyboardButton("📜 Sertifikat haqida", callback_data="help:cert"),
        InlineKeyboardButton("📞 Bog'lanish", callback_data="help:contact"),
        InlineKeyboardButton("🏠 Bosh menyu", callback_data="main:menu")
    )
    return keyboard


def help_back() -> InlineKeyboardMarkup:
    """Yordam orqaga"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="help:menu"))
    return keyboard


def contact_admin() -> InlineKeyboardMarkup:
    """Admin bilan bog'lanish"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📨 Xabar yuborish", callback_data="contact:message"),
        InlineKeyboardButton("📞 Qo'ng'iroq qilish", callback_data="contact:call"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="help:menu")
    )
    return keyboard


# ============================================================
#                    YORDAMCHI FUNKSIYALAR
# ============================================================

def pagination(current_page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Pagination tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=3)

    buttons = []

    if current_page > 1:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}:page:{current_page - 1}"))

    buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="current"))

    if current_page < total_pages:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}:page:{current_page + 1}"))

    keyboard.row(*buttons)
    return keyboard


def yes_no(prefix: str, item_id: int = None) -> InlineKeyboardMarkup:
    """Ha/Yo'q tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    if item_id:
        keyboard.add(
            InlineKeyboardButton("✅ Ha", callback_data=f"{prefix}:yes:{item_id}"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"{prefix}:no:{item_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("✅ Ha", callback_data=f"{prefix}:yes"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"{prefix}:no")
        )

    return keyboard


def inline_back(callback_data: str) -> InlineKeyboardMarkup:
    """Inline orqaga tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data=callback_data))
    return keyboard


def close_button() -> InlineKeyboardMarkup:
    """Yopish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Yopish", callback_data="close"))
    return keyboard


def main_menu_inline() -> InlineKeyboardMarkup:
    """Bosh menyu (inline)"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Bosh menyu", callback_data="main:menu"))
    return keyboard