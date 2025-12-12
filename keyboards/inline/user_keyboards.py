"""
User Inline Keyboards (MAKSIMAL SODDA)
======================================
Modul yo'q, menyu yo'q, yordam yo'q
Faqat: Demo → Ro'yxat → To'lov → Darslar (ketma-ket) → Sertifikat
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


# ============================================================
#                    DEMO DARS
# ============================================================

def demo_lesson_button() -> InlineKeyboardMarkup:
    """
    /start dan keyin - demo darsni ko'rish
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "📘 Bepul demo darsni ko'rish",
        callback_data="user:demo"
    ))
    return keyboard


def after_demo_not_registered() -> InlineKeyboardMarkup:
    """
    Demo ko'rgandan keyin - ro'yxatdan o'tmagan user
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "📝 Ro'yxatdan o'tish",
        callback_data="user:register"
    ))
    return keyboard


def after_demo_registered() -> InlineKeyboardMarkup:
    """
    Demo ko'rgandan keyin - ro'yxatdan o'tgan, to'lamagan
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "💰 Kursni sotib olish",
        callback_data="user:buy"
    ))
    return keyboard


# ============================================================
#                    TO'LOV
# ============================================================

def payment_info() -> InlineKeyboardMarkup:
    """
    To'lov ma'lumotlari ko'rsatilgandan keyin - chek yuborish
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "✅ To'ladim (chek yuborish)",
        callback_data="user:send_receipt"
    ))
    keyboard.add(InlineKeyboardButton(
        "❌ Bekor qilish",
        callback_data="user:cancel"
    ))
    return keyboard


def payment_pending() -> InlineKeyboardMarkup:
    """
    To'lov tekshirilmoqda
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "🔄 Statusni tekshirish",
        callback_data="user:check_payment"
    ))
    return keyboard


def payment_approved() -> InlineKeyboardMarkup:
    """
    To'lov tasdiqlandi - kursni boshlash
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "▶️ Kursni boshlash",
        callback_data="user:lessons"
    ))
    return keyboard


# ============================================================
#                    DARSLAR RO'YXATI
# ============================================================

def simple_lessons_list(lessons: List[Dict]) -> InlineKeyboardMarkup:
    """
    Sodda darslar ro'yxati - MODUL KO'RINMAYDI

    lessons = [
        {
            'id': 1,
            'order_num': 1,  # Global tartib (1, 2, 3...)
            'name': 'Kompyuter bilan tanishish',
            'status': 'completed' | 'unlocked' | 'locked'
        },
        ...
    ]

    Ko'rinishi:
    ✅ 1. Kompyuter bilan tanishish
    ✅ 2. Monitor va klaviatura
    🔓 3. Windows asoslari         ← hozirgi ochiq
    🔒 4. Fayl va papkalar
    🔒 5. Word dasturi
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

    for lesson in lessons:
        status = lesson.get('status', 'locked')
        order = lesson.get('order_num', 0)
        name = lesson.get('name', '')

        # Status belgisi
        if status == 'completed':
            icon = "✅"
        elif status == 'unlocked':
            icon = "🔓"
        else:
            icon = "🔒"

        # Tugma matni: ✅ 1. Kompyuter bilan tanishish
        button_text = f"{icon} {order}. {name}"

        # Callback
        if status == 'locked':
            callback = f"user:locked:{lesson['id']}"
        else:
            callback = f"user:lesson:{lesson['id']}"

        keyboard.add(InlineKeyboardButton(button_text, callback_data=callback))

    return keyboard


# ============================================================
#                    DARS KO'RISH
# ============================================================

def lesson_view(
        lesson_id: int,
        has_video: bool = True,
        has_materials: bool = False,
        has_test: bool = False,
        is_completed: bool = False,
        next_lesson_id: int = None
) -> InlineKeyboardMarkup:
    """
    Darsni ko'rish tugmalari
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

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
            callback_data=f"user:test:{lesson_id}"
        ))

    # Keyingi dars (faqat completed bo'lsa)
    if is_completed and next_lesson_id:
        keyboard.add(InlineKeyboardButton(
            "⏭ Keyingi dars",
            callback_data=f"user:lesson:{next_lesson_id}"
        ))

    # Orqaga
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:lessons"
    ))

    return keyboard


def after_video_with_test(lesson_id: int) -> InlineKeyboardMarkup:
    """
    Video ko'rgandan keyin - test bor
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "📝 Test yechish",
        callback_data=f"user:test:{lesson_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:lessons"
    ))
    return keyboard


def after_video_no_test(next_lesson_id: int = None) -> InlineKeyboardMarkup:
    """
    Video ko'rgandan keyin - test yo'q (dars avtomatik tugaydi)
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

    if next_lesson_id:
        keyboard.add(InlineKeyboardButton(
            "⏭ Keyingi dars",
            callback_data=f"user:lesson:{next_lesson_id}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:lessons"
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
        callback_data=f"user:lesson:{lesson_id}"
    ))
    return keyboard


def test_question(question_index: int, options: List[str]) -> InlineKeyboardMarkup:
    """
    Test savoli javoblari
    options = ['A', 'B', 'C', 'D']
    """
    keyboard = InlineKeyboardMarkup(row_width=2)

    buttons = []
    for option in options:
        buttons.append(InlineKeyboardButton(
            option,
            callback_data=f"user:answer:{question_index}:{option}"
        ))

    # 2 tadan qo'yish
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.row(buttons[i], buttons[i + 1])
        else:
            keyboard.row(buttons[i])

    return keyboard


def test_result(lesson_id: int, passed: bool, next_lesson_id: int = None,
                is_last_lesson: bool = False) -> InlineKeyboardMarkup:
    """
    Test natijasi
    passed=True: 60%+ to'pladi
    passed=False: 60% dan kam
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

    if passed:
        if is_last_lesson:
            # Oxirgi dars - sertifikat
            keyboard.add(InlineKeyboardButton(
                "🎓 Sertifikatni olish",
                callback_data="user:certificate"
            ))
        elif next_lesson_id:
            # Keyingi darsga
            keyboard.add(InlineKeyboardButton(
                "⏭ Keyingi dars",
                callback_data=f"user:lesson:{next_lesson_id}"
            ))
    else:
        # O'tmadi - qayta topshirish
        keyboard.add(InlineKeyboardButton(
            "🔄 Qayta topshirish",
            callback_data=f"user:test:{lesson_id}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:lessons"
    ))

    return keyboard


# ============================================================
#                    MATERIALLAR
# ============================================================

def materials_list(lesson_id: int, materials: List[Dict]) -> InlineKeyboardMarkup:
    """Materiallar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for material in materials:
        name = material.get('name', 'Material')
        keyboard.add(InlineKeyboardButton(
            f"📎 {name}",
            callback_data=f"user:material:{material['id']}"
        ))

    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data=f"user:lesson:{lesson_id}"
    ))

    return keyboard


# ============================================================
#                    SERTIFIKAT
# ============================================================

def certificate_ready() -> InlineKeyboardMarkup:
    """Sertifikat tayyor"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "📥 Sertifikatni yuklab olish",
        callback_data="user:certificate:download"
    ))
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:lessons"
    ))
    return keyboard


# ============================================================
#                    YORDAMCHI
# ============================================================

def back_to_lessons() -> InlineKeyboardMarkup:
    """Darslar ro'yxatiga qaytish"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="user:lessons"
    ))
    return keyboard


def cancel_button() -> InlineKeyboardMarkup:
    """Bekor qilish"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "❌ Bekor qilish",
        callback_data="user:cancel"
    ))
    return keyboard


# ============================================================
#                    REFERAL
# ============================================================

def referral_menu(ref_link: str, stats: dict) -> InlineKeyboardMarkup:
    """
    Referal sahifasi - sodda
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(
        "📤 Do'stlarga yuborish",
        url=f"https://t.me/share/url?url={ref_link}&text=Ajoyib kurslarni ko'ring! 🎓"
    ))

    if stats.get('total_referrals', 0) > 0:
        keyboard.add(InlineKeyboardButton(
            f"👥 Taklif qilganlarim ({stats['total_referrals']})",
            callback_data="referral:list"
        ))

    return keyboard


def referral_back() -> InlineKeyboardMarkup:
    """Orqaga"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(
        "⬅️ Orqaga",
        callback_data="referral:menu"
    ))
    return keyboard