import asyncio
import logging
from aiogram import executor
from environs import Env

# Environment variables
env = Env()
env.read_env()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import bot va dispatcher
from loader import dp, bot, user_db

# Handlerlarni import qilish
import handlers


def run_migrations():
    """
    Database migratsiyalarni ishga tushirish
    Yangi ustunlar qo'shish (agar mavjud bo'lmasa)
    """
    logger.info("🔄 Database migratsiyalar tekshirilmoqda...")

    migrations = [
        # Kelajakda yangi ustunlar qo'shish uchun
        # {
        #     'name': 'new_column',
        #     'table': 'Users',
        #     'sql': 'ALTER TABLE Users ADD COLUMN new_column TEXT'
        # },
    ]

    for migration in migrations:
        try:
            # Ustun mavjudligini tekshirish
            check_sql = f"PRAGMA table_info({migration['table']})"
            columns = user_db.execute(check_sql, fetchall=True)
            column_names = [col[1] for col in columns]

            if migration['name'] not in column_names:
                # Ustun yo'q - qo'shish
                user_db.execute(migration['sql'], commit=True)
                logger.info(f"✅ Migration qo'shildi: {migration['name']}")
            else:
                logger.info(f"ℹ️ Migration mavjud: {migration['name']}")

        except Exception as e:
            logger.error(f"❌ Migration xato ({migration['name']}): {e}")


def create_all_tables():
    """Barcha database jadvallarini yaratish"""
    logger.info("📦 Database jadvallari yaratilmoqda...")

    try:
        # 1. Foydalanuvchilar
        user_db.create_table_users()
        logger.info("  ✅ Users jadvali")

        # 2. Adminlar
        user_db.create_table_admins()
        logger.info("  ✅ Admins jadvali")

        # 3. Kurslar
        user_db.create_table_courses()
        logger.info("  ✅ Courses jadvali")

        # 4. Modullar
        user_db.create_table_modules()
        logger.info("  ✅ Modules jadvali")

        # 5. Darslar
        user_db.create_table_lessons()
        logger.info("  ✅ Lessons jadvali")

        # 6. Dars materiallari
        user_db.create_table_lesson_materials()
        logger.info("  ✅ LessonMaterials jadvali")

        # 7. Testlar
        user_db.create_table_tests()
        logger.info("  ✅ Tests jadvali")

        # 8. Test savollari
        user_db.create_table_questions()
        logger.info("  ✅ Questions jadvali")

        # 9. Foydalanuvchi progressi
        user_db.create_table_user_progress()
        logger.info("  ✅ UserProgress jadvali")

        # 10. Test natijalari
        user_db.create_table_test_results()
        logger.info("  ✅ TestResults jadvali")

        # 11. Fikr-mulohazalar
        user_db.create_table_feedbacks()
        logger.info("  ✅ Feedbacks jadvali")

        # 12. To'lovlar
        user_db.create_table_payments()
        logger.info("  ✅ Payments jadvali")

        # 13. Qo'lda dostup
        user_db.create_table_manual_access()
        logger.info("  ✅ ManualAccess jadvali")

        # 14. Sertifikatlar
        user_db.create_table_certificates()
        logger.info("  ✅ Certificates jadvali")

        # 15. Sozlamalar
        user_db.create_table_settings()
        logger.info("  ✅ Settings jadvali")

        logger.info("📦 Barcha jadvallar tayyor! (15 ta)")
        return True

    except Exception as e:
        logger.error(f"❌ Jadval yaratishda xato: {e}")
        return False


async def on_startup(dispatcher):
    """Bot ishga tushganda"""
    logger.info("=" * 50)
    logger.info("🚀 O'QUV MARKAZ BOT ISHGA TUSHMOQDA...")
    logger.info("=" * 50)

    # Database jadvallarini yaratish
    create_all_tables()

    # Migratsiyalarni ishga tushirish
    try:
        run_migrations()
        logger.info("✅ Database migratsiyalar tayyor")
    except Exception as e:
        logger.error(f"❌ Migration xato: {e}")

    # Bot ma'lumotlarini olish
    try:
        bot_info = await bot.get_me()
        logger.info(f"🤖 Bot: @{bot_info.username}")
    except Exception as e:
        logger.error(f"❌ Bot info xato: {e}")

    # Statistika
    try:
        users_count = user_db.count_users()
        logger.info(f"👥 Jami foydalanuvchilar: {users_count}")
    except:
        pass

    logger.info("=" * 50)
    logger.info("✅ BOT TAYYOR!")
    logger.info("=" * 50)


async def on_shutdown(dispatcher):
    """Bot to'xtaganda"""
    logger.info("=" * 50)
    logger.info("⏹ BOT TO'XTATILMOQDA...")
    logger.info("=" * 50)

    # Connectionlarni yopish
    await dp.storage.close()
    await dp.storage.wait_closed()

    logger.info("=" * 50)
    logger.info("✅ BOT TO'XTATILDI")
    logger.info("=" * 50)


if __name__ == '__main__':
    # Bot'ni ishga tushirish
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )