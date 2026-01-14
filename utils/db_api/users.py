"""
O'quv Markaz Bot - Ma'lumotlar Bazasi
=====================================
Kurslar, modullar, darslar, testlar, progress va sertifikatlar uchun
to'liq database logikasi.

Muallif: Davronov G'olibjon
Sana: 2025
"""
from data.config import ADMINS
from .database import Database
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import pytz

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


class UserDatabase(Database):
    """O'quv markaz bot uchun asosiy database class"""

    # ============================================================
    #                    JADVALLARNI YARATISH
    # ============================================================

    def create_tables(self):
        """Barcha jadvallarni yaratish"""
        self.create_table_users()
        self.create_table_admins()
        self.create_table_courses()
        self.create_table_modules()
        self.create_table_lessons()
        self.create_table_tests()
        self.create_table_questions()
        self.create_table_user_progress()
        self.create_table_test_results()
        self.create_table_feedbacks()
        self.create_table_payments()
        self.create_table_manual_access()
        self.create_table_certificates()
        self.create_table_settings()
        self.create_table_lesson_materials()
        self.create_table_referrals()
        print("✅ Barcha jadvallar yaratildi")

    def create_table_users(self):
        """Foydalanuvchilar jadvali (YANGILANGAN)"""
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT NOT NULL UNIQUE,
            username VARCHAR(255) NULL,
            full_name VARCHAR(255) NULL,
            phone VARCHAR(20) NULL,
            total_score INTEGER DEFAULT 0,

            -- YANGI QO'SHILGAN USTUNLAR:
            balance DECIMAL(10, 2) DEFAULT 0.00,
            referral_code VARCHAR(20) UNIQUE NULL,
            referred_by INTEGER NULL,
            referral_count INTEGER DEFAULT 0,

            is_active BOOLEAN DEFAULT TRUE,
            is_blocked BOOLEAN DEFAULT FALSE,
            last_active DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram ON Users(telegram_id);", commit=True)


    def create_table_admins(self):
        """Adminlar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            is_super_admin BOOLEAN DEFAULT FALSE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)




    def create_table_courses(self):
        """Kurslar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            description TEXT NULL,
            price DECIMAL(10, 2) DEFAULT 0.00,
            order_num INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NULL
        );
        """
        self.execute(sql, commit=True)

    def create_table_referrals(self):
        """Referallar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL UNIQUE,
            status VARCHAR(20) DEFAULT 'registered',
            bonus_given INTEGER DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            converted_at DATETIME NULL,
            FOREIGN KEY (referrer_id) REFERENCES Users(id) ON DELETE CASCADE,
            FOREIGN KEY (referred_id) REFERENCES Users(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON Referrals(referrer_id);", commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred ON Referrals(referred_id);", commit=True)

    def create_table_modules(self):
        """Modullar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT NULL,
            order_num INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_modules_course ON Modules(course_id);", commit=True)

    def create_table_lessons(self):
        """Darslar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT NULL,
            video_file_id TEXT NULL,
            video_duration INTEGER NULL,
            order_num INTEGER DEFAULT 0,
            has_test BOOLEAN DEFAULT FALSE,
            is_free BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (module_id) REFERENCES Modules(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_lessons_module ON Lessons(module_id);", commit=True)

    def create_table_tests(self):
        """Testlar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL UNIQUE,
            name VARCHAR(255) NULL,
            passing_score INTEGER DEFAULT 60,
            time_limit INTEGER NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lesson_id) REFERENCES Lessons(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)

    def create_table_questions(self):
        """Test savollari jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            option_a VARCHAR(500) NOT NULL,
            option_b VARCHAR(500) NOT NULL,
            option_c VARCHAR(500) NULL,
            option_d VARCHAR(500) NULL,
            correct_answer CHAR(1) NOT NULL,
            order_num INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES Tests(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_questions_test ON Questions(test_id);", commit=True)

    def create_table_user_progress(self):
        """Foydalanuvchi progressi jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS UserProgress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'locked',
            started_at DATETIME NULL,
            completed_at DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id),
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
            FOREIGN KEY (lesson_id) REFERENCES Lessons(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_progress_user ON UserProgress(user_id);", commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_progress_lesson ON UserProgress(lesson_id);", commit=True)

    def create_table_test_results(self):
        """Test natijalari jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS TestResults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL,
            passed BOOLEAN DEFAULT FALSE,
            answers_json TEXT NULL,
            completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
            FOREIGN KEY (test_id) REFERENCES Tests(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_test_results_user ON TestResults(user_id);", commit=True)

    def create_table_feedbacks(self):
        """Fikr-mulohazalar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT NULL,
            score_given INTEGER DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id),
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
            FOREIGN KEY (lesson_id) REFERENCES Lessons(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_feedbacks_lesson ON Feedbacks(lesson_id);", commit=True)

    def create_table_payments(self):
        """To'lovlar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            receipt_file_id TEXT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            admin_id INTEGER NULL,
            admin_note TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NULL,
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE,
            FOREIGN KEY (admin_id) REFERENCES Users(id) ON DELETE SET NULL
        );
        """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_payments_user ON Payments(user_id);", commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON Payments(status);", commit=True)

    def create_table_manual_access(self):
        """Qo'lda berilgan dostuplar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS ManualAccess (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            granted_by INTEGER NOT NULL,
            reason TEXT NULL,
            expires_at DATETIME NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE,
            FOREIGN KEY (granted_by) REFERENCES Users(id) ON DELETE SET NULL
        );
        """
        self.execute(sql, commit=True)

    def create_table_certificates(self):
        """Sertifikatlar jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            certificate_code VARCHAR(50) NOT NULL UNIQUE,
            total_score INTEGER NOT NULL,
            percentage DECIMAL(5, 2) NOT NULL,
            grade VARCHAR(20) NOT NULL,
            file_id TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)

    def create_table_settings(self):
        """Tizim sozlamalari jadvali"""
        sql = """
        CREATE TABLE IF NOT EXISTS Settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) NOT NULL UNIQUE,
            value TEXT NOT NULL,
            description TEXT NULL,
            updated_at DATETIME NULL
        );
        """
        self.execute(sql, commit=True)

        # Default sozlamalar
        default_settings = [
            ('feedback_required', 'false', 'Fikr yozish majburiymi'),
            ('feedback_score', '2', 'Fikr uchun beriladigan ball'),
            ('test_passing_score', '60', 'Testdan otish minimal bali (%)'),
            ('bronze_threshold', '60', 'Bronza sertifikat chegarasi (%)'),
            ('silver_threshold', '75', 'Kumush sertifikat chegarasi (%)'),
            ('gold_threshold', '90', 'Oltin sertifikat chegarasi (%)'),
            ('reminder_days', '3', 'Necha kundan keyin eslatma yuborish'),
            ('referral_cashback', '10', 'Referal cashback foizi (%)'),
        ]

        for key, value, desc in default_settings:
            self.execute(
                "INSERT OR IGNORE INTO Settings (key, value, description) VALUES (?, ?, ?)",
                parameters=(key, value, desc),
                commit=True
            )

    def create_table_lesson_materials(self):
        sql = """
            CREATE TABLE IF NOT EXISTS LessonMaterials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                file_type VARCHAR(20) NOT NULL,
                file_id TEXT NOT NULL,
                file_size INTEGER NULL,
                description TEXT NULL,
                order_num INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lesson_id) REFERENCES Lessons(id) ON DELETE CASCADE
            );
            """
        self.execute(sql, commit=True)
        self.execute("CREATE INDEX IF NOT EXISTS idx_materials_lesson ON LessonMaterials(lesson_id);", commit=True)

        # Default sozlamalar
        default_settings = [
            ('feedback_required', 'false', 'Fikr yozish majburiymi'),
            ('feedback_score', '2', 'Fikr uchun beriladigan ball'),
            ('test_passing_score', '60', 'Testdan o\'tish minimal bali (%)'),
            ('bronze_threshold', '60', 'Bronza sertifikat chegarasi (%)'),
            ('silver_threshold', '75', 'Kumush sertifikat chegarasi (%)'),
            ('gold_threshold', '90', 'Oltin sertifikat chegarasi (%)'),
            ('reminder_days', '3', 'Necha kundan keyin eslatma yuborish'),
        ]

        for key, value, desc in default_settings:
            self.execute(
                "INSERT OR IGNORE INTO Settings (key, value, description) VALUES (?, ?, ?)",
                parameters=(key, value, desc),
                commit=True
            )

    # ============================================================
    #                    USER METODLARI
    # ============================================================

    def user_exists(self, telegram_id: int) -> bool:
        """Foydalanuvchi mavjudligini tekshirish"""
        result = self.execute(
            "SELECT 1 FROM Users WHERE telegram_id = ?",
            parameters=(telegram_id,),
            fetchone=True
        )
        return result is not None

    def add_user(self, telegram_id: int, username: str = None, full_name: str = None,referral_code: str = None) -> bool:
        """Yangi foydalanuvchi qo'shish"""
        if self.user_exists(telegram_id):
            return False

        self.execute(
            """INSERT INTO Users (telegram_id, username, full_name, created_at) 
               VALUES (?, ?, ?, ?)""",
            parameters=(telegram_id, username, full_name, datetime.now(TASHKENT_TZ).isoformat()),
            commit=True
        )

        # Agar referal kod bilan kelgan bo'lsa
        if referral_code:
            referrer = self.get_user_by_referral_code(referral_code)
            if referrer:
                self.register_referral(referrer['telegram_id'], telegram_id)
        return True

    def get_user_id(self, telegram_id: int) -> Optional[int]:
        """Telegram ID bo'yicha ichki ID olish"""
        result = self.execute(
            "SELECT id FROM Users WHERE telegram_id = ?",
            parameters=(telegram_id,),
            fetchone=True
        )
        return result[0] if result else None

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Foydalanuvchi ma'lumotlarini olish (BALANS BILAN)"""
        result = self.execute(
            """SELECT id, telegram_id, username, full_name, phone, total_score, 
                      balance, referral_code, is_active, created_at 
               FROM Users WHERE telegram_id = ?""",
            parameters=(telegram_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'telegram_id': result[1],
                'username': result[2],
                'full_name': result[3],
                'phone': result[4],
                'total_score': result[5],
                'balance': result[6] or 0.0,  # <-- Balans
                'referral_code': result[7],  # <-- Referal kod
                'is_active': bool(result[8]),
                'created_at': result[9]
            }
        return None

    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Foydalanuvchi ma'lumotlarini yangilash"""
        if not kwargs:
            return False

        # 'balance' ni ruxsat etilganlar ro'yxatiga qo'shdik
        allowed_fields = ['username', 'full_name', 'phone', 'is_active', 'is_blocked', 'balance']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(telegram_id)
        sql = f"UPDATE Users SET {', '.join(updates)} WHERE telegram_id = ?"
        self.execute(sql, parameters=tuple(params), commit=True)
        return True

        # YANGI METOD
    def add_balance(self, telegram_id: int, amount: float) -> bool:
            """Foydalanuvchi balansiga pul qo'shish"""
            try:
                self.execute(
                    "UPDATE Users SET balance = COALESCE(balance, 0) + ? WHERE telegram_id = ?",
                    parameters=(amount, telegram_id),
                    commit=True
                )
                return True
            except Exception as e:
                print(f"❌ Balans to'ldirishda xato: {e}")
                return False



    def update_last_active(self, telegram_id: int):
        """Oxirgi faollik vaqtini yangilash"""
        self.execute(
            "UPDATE Users SET last_active = ? WHERE telegram_id = ?",
            parameters=(datetime.now(TASHKENT_TZ).isoformat(), telegram_id),
            commit=True
        )

    def add_score(self, telegram_id: int, score: int) -> bool:
        """Foydalanuvchiga ball qo'shish"""
        try:
            self.execute(
                "UPDATE Users SET total_score = total_score + ? WHERE telegram_id = ?",
                parameters=(score, telegram_id),
                commit=True
            )
            return True
        except Exception as e:
            print(f"❌ Ball qo'shishda xato: {e}")
            return False

    def get_user_score(self, telegram_id: int) -> int:
        """Foydalanuvchi umumiy balini olish"""
        result = self.execute(
            "SELECT total_score FROM Users WHERE telegram_id = ?",
            parameters=(telegram_id,),
            fetchone=True
        )
        return result[0] if result else 0

    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Barcha foydalanuvchilar ro'yxati"""
        results = self.execute(
            """SELECT id, telegram_id, username, full_name, total_score, is_active, created_at
               FROM Users ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            parameters=(limit, offset),
            fetchall=True
        )
        users = []
        for row in results:
            users.append({
                'id': row[0],
                'telegram_id': row[1],
                'username': row[2],
                'full_name': row[3],
                'total_score': row[4],
                'is_active': bool(row[5]),
                'created_at': row[6]
            })
        return users

    def count_users(self) -> int:
        """Jami foydalanuvchilar soni"""
        result = self.execute("SELECT COUNT(*) FROM Users", fetchone=True)
        return result[0] if result else 0

    def search_users(self, query: str) -> List[Dict]:
        """Foydalanuvchi qidirish"""
        search = f"%{query}%"
        results = self.execute(
            """SELECT id, telegram_id, username, full_name, total_score
               FROM Users 
               WHERE username LIKE ? OR full_name LIKE ? OR CAST(telegram_id AS TEXT) LIKE ?
               LIMIT 20""",
            parameters=(search, search, search),
            fetchall=True
        )
        users = []
        for row in results:
            users.append({
                'id': row[0],
                'telegram_id': row[1],
                'username': row[2],
                'full_name': row[3],
                'total_score': row[4]
            })
        return users

    # ============================================================
    #                    ADMIN METODLARI
    # ============================================================

    def is_admin(self, telegram_id: int) -> bool:
        """
        Foydalanuvchi adminmi tekshirish.
        1) Avvalo config.ADMINS (super-adminlar) ichida telegram_id bormi tekshiradi.
        2) Keyin users jadvalidan user_id olib, Admins jadvalidan tekshiradi.
        """
        # 1) super-adminlarni tekshirish (env orqali)
        try:
            # config.ADMINS ni list[int] yoki set[int] deb kutamiz
            if telegram_id in ADMINS:
                return True
        except Exception:
            # agar config.ADMINS noto'g'ri formatda bo'lsa, xatolikni yutib davom etish
            pass

        # 2) odatiy DB-adminni tekshirish
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        result = self.execute(
            "SELECT 1 FROM Admins WHERE user_id = ?",
            parameters=(user_id,),
            fetchone=True
        )
        return result is not None

        # database/db.py ichiga qo'shing

    def get_notification_admins(self):
            """Xabar yuborish uchun barcha adminlar (Config + DB)"""
            # 1. Bazadagi adminlar
            db_admins = self.execute(
                "SELECT u.telegram_id FROM Admins a JOIN Users u ON a.user_id = u.id",
                fetchall=True
            )
            admin_ids = [row[0] for row in db_admins] if db_admins else []

            # 2. Config dagi adminlar (import qilingan bo'lishi kerak)
            from data.config import ADMINS
            for admin in ADMINS:
                if admin not in admin_ids:
                    admin_ids.append(admin)

            return admin_ids

    def is_super_admin(self, telegram_id: int) -> bool:
        """Foydalanuvchi super adminmi tekshirish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False
        result = self.execute(
            "SELECT is_super_admin FROM Admins WHERE user_id = ?",
            parameters=(user_id,),
            fetchone=True
        )
        return bool(result[0]) if result else False

    def add_admin(self, telegram_id: int, name: str, is_super: bool = False) -> bool:
        """Admin qo'shish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        try:
            self.execute(
                "INSERT OR REPLACE INTO Admins (user_id, name, is_super_admin) VALUES (?, ?, ?)",
                parameters=(user_id, name, is_super),
                commit=True
            )
            return True
        except Exception as e:
            print(f"❌ Admin qo'shishda xato: {e}")
            return False

    def remove_admin(self, telegram_id: int) -> bool:
        """Adminni olib tashlash"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        self.execute(
            "DELETE FROM Admins WHERE user_id = ?",
            parameters=(user_id,),
            commit=True
        )
        return True

    def get_all_admins(self) -> List[Dict]:
        """Barcha adminlar ro'yxati"""
        results = self.execute(
            """SELECT a.id, u.telegram_id, u.username, a.name, a.is_super_admin, a.created_at
               FROM Admins a
               JOIN Users u ON a.user_id = u.id""",
            fetchall=True
        )
        admins = []
        for row in results:
            admins.append({
                'id': row[0],
                'telegram_id': row[1],
                'username': row[2],
                'name': row[3],
                'is_super_admin': bool(row[4]),
                'created_at': row[5]
            })
        return admins

    # ============================================================
    #                    KURS METODLARI
    # ============================================================

    def add_course(self, name: str, description: str = None, price: float = 0) -> Optional[int]:
        """Yangi kurs qo'shish"""
        try:
            # Tartib raqamini olish
            result = self.execute(
                "SELECT COALESCE(MAX(order_num), 0) + 1 FROM Courses",
                fetchone=True
            )
            order_num = result[0] if result else 1

            self.execute(
                """INSERT INTO Courses (name, description, price, order_num) 
                   VALUES (?, ?, ?, ?)""",
                parameters=(name, description, price, order_num),
                commit=True
            )

            result = self.execute(
                "SELECT id FROM Courses WHERE name = ? ORDER BY id DESC LIMIT 1",
                parameters=(name,),
                fetchone=True
            )
            return result[0] if result else None

        except Exception as e:
            print(f"❌ Kurs qo'shishda xato: {e}")
            return None

    def get_course(self, course_id: int) -> Optional[Dict]:
        """Kurs ma'lumotlarini olish"""
        result = self.execute(
            """SELECT id, name, description, price, order_num, is_active, created_at
               FROM Courses WHERE id = ?""",
            parameters=(course_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'description': result[2],
                'price': float(result[3]),
                'order_num': result[4],
                'is_active': bool(result[5]),
                'created_at': result[6]
            }
        return None

    def get_all_courses(self, active_only: bool = True) -> List[Dict]:
        """Barcha kurslar ro'yxati"""
        if active_only:
            sql = "SELECT id, name, description, price, order_num FROM Courses WHERE is_active = TRUE ORDER BY order_num"
        else:
            sql = "SELECT id, name, description, price, order_num, is_active FROM Courses ORDER BY order_num"

        results = self.execute(sql, fetchall=True)
        courses = []
        for row in results:
            course = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'price': float(row[3]),
                'order_num': row[4]
            }
            if not active_only:
                course['is_active'] = bool(row[5])
            courses.append(course)
        return courses

    def update_course(self, course_id: int, **kwargs) -> bool:
        """Kurs ma'lumotlarini yangilash"""
        allowed_fields = ['name', 'description', 'price', 'order_num', 'is_active']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now(TASHKENT_TZ).isoformat())
        params.append(course_id)

        sql = f"UPDATE Courses SET {', '.join(updates)} WHERE id = ?"
        self.execute(sql, parameters=tuple(params), commit=True)
        return True

    def delete_course(self, course_id: int) -> bool:
        """Kursni o'chirish (soft delete)"""
        return self.update_course(course_id, is_active=False)

    # ============================================================
    #                    MODUL METODLARI
    # ============================================================

    def add_module(self, course_id: int, name: str, description: str = None) -> Optional[int]:
        """Yangi modul qo'shish"""
        try:
            result = self.execute(
                "SELECT COALESCE(MAX(order_num), 0) + 1 FROM Modules WHERE course_id = ?",
                parameters=(course_id,),
                fetchone=True
            )
            order_num = result[0] if result else 1

            self.execute(
                "INSERT INTO Modules (course_id, name, description, order_num) VALUES (?, ?, ?, ?)",
                parameters=(course_id, name, description, order_num),
                commit=True
            )

            result = self.execute(
                "SELECT id FROM Modules WHERE course_id = ? AND name = ? ORDER BY id DESC LIMIT 1",
                parameters=(course_id, name),
                fetchone=True
            )
            return result[0] if result else None

        except Exception as e:
            print(f"❌ Modul qo'shishda xato: {e}")
            return None

    def get_module(self, module_id: int) -> Optional[Dict]:
        """Modul ma'lumotlarini olish"""
        result = self.execute(
            """SELECT m.id, m.course_id, m.name, m.description, m.order_num, m.is_active, c.name
               FROM Modules m
               JOIN Courses c ON m.course_id = c.id
               WHERE m.id = ?""",
            parameters=(module_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'course_id': result[1],
                'name': result[2],
                'description': result[3],
                'order_num': result[4],
                'is_active': bool(result[5]),
                'course_name': result[6]
            }
        return None

    def get_course_modules(self, course_id: int, active_only: bool = True) -> List[Dict]:
        """Kurs modullari ro'yxati"""
        if active_only:
            sql = """SELECT id, name, description, order_num 
                     FROM Modules WHERE course_id = ? AND is_active = TRUE ORDER BY order_num"""
        else:
            sql = """SELECT id, name, description, order_num, is_active 
                     FROM Modules WHERE course_id = ? ORDER BY order_num"""

        results = self.execute(sql, parameters=(course_id,), fetchall=True)
        modules = []
        for row in results:
            module = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'order_num': row[3]
            }
            if not active_only:
                module['is_active'] = bool(row[4])
            modules.append(module)
        return modules

    def update_module(self, module_id: int, **kwargs) -> bool:
        """Modul yangilash"""
        allowed_fields = ['name', 'description', 'order_num', 'is_active']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(module_id)
        sql = f"UPDATE Modules SET {', '.join(updates)} WHERE id = ?"
        self.execute(sql, parameters=tuple(params), commit=True)
        return True

    def delete_module(self, module_id: int) -> bool:
        """Modulni o'chirish"""
        return self.update_module(module_id, is_active=False)

    # ============================================================
    #                    DARS METODLARI
    # ============================================================

    def add_lesson(
            self,
            module_id: int,
            name: str,
            description: str = None,
            video_file_id: str = None,
            video_duration: int = None,
            is_free: bool = False
    ) -> Optional[int]:
        """Yangi dars qo'shish"""
        try:
            result = self.execute(
                "SELECT COALESCE(MAX(order_num), 0) + 1 FROM Lessons WHERE module_id = ?",
                parameters=(module_id,),
                fetchone=True
            )
            order_num = result[0] if result else 1

            self.execute(
                """INSERT INTO Lessons (module_id, name, description, video_file_id, 
                   video_duration, order_num, is_free) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                parameters=(module_id, name, description, video_file_id, video_duration, order_num, is_free),
                commit=True
            )

            result = self.execute(
                "SELECT id FROM Lessons WHERE module_id = ? ORDER BY id DESC LIMIT 1",
                parameters=(module_id,),
                fetchone=True
            )
            return result[0] if result else None

        except Exception as e:
            print(f"❌ Dars qo'shishda xato: {e}")
            return None

    def get_lesson(self, lesson_id: int) -> Optional[Dict]:
        """Dars ma'lumotlarini olish"""
        result = self.execute(
            """SELECT l.id, l.module_id, l.name, l.description, l.video_file_id, 
                      l.video_duration, l.order_num, l.has_test, l.is_free, l.is_active,
                      m.name, m.course_id
               FROM Lessons l
               JOIN Modules m ON l.module_id = m.id
               WHERE l.id = ?""",
            parameters=(lesson_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'module_id': result[1],
                'name': result[2],
                'description': result[3],
                'video_file_id': result[4],
                'video_duration': result[5],
                'order_num': result[6],
                'has_test': bool(result[7]),
                'is_free': bool(result[8]),
                'is_active': bool(result[9]),
                'module_name': result[10],
                'course_id': result[11]
            }
        return None

    def get_module_lessons(self, module_id: int, active_only: bool = True) -> List[Dict]:
        """Modul darslari ro'yxati"""
        if active_only:
            sql = """SELECT id, name, description, video_file_id, has_test, is_free, order_num
                     FROM Lessons WHERE module_id = ? AND is_active = TRUE ORDER BY order_num"""
        else:
            sql = """SELECT id, name, description, video_file_id, has_test, is_free, order_num, is_active
                     FROM Lessons WHERE module_id = ? ORDER BY order_num"""

        results = self.execute(sql, parameters=(module_id,), fetchall=True)
        lessons = []
        for row in results:
            lesson = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'video_file_id': row[3],
                'has_test': bool(row[4]),
                'is_free': bool(row[5]),
                'order_num': row[6]
            }
            if not active_only:
                lesson['is_active'] = bool(row[7])
            lessons.append(lesson)
        return lessons

    def get_course_lessons(self, course_id: int) -> List[Dict]:
        """Kursdagi barcha darslar"""
        results = self.execute(
            """SELECT l.id, l.name, l.order_num, l.has_test, l.is_free, m.id, m.name, m.order_num
               FROM Lessons l
               JOIN Modules m ON l.module_id = m.id
               WHERE m.course_id = ? AND l.is_active = TRUE AND m.is_active = TRUE
               ORDER BY m.order_num, l.order_num""",
            parameters=(course_id,),
            fetchall=True
        )
        lessons = []
        for row in results:
            lessons.append({
                'id': row[0],
                'name': row[1],
                'order_num': row[2],
                'has_test': bool(row[3]),
                'is_free': bool(row[4]),
                'module_id': row[5],
                'module_name': row[6],
                'module_order': row[7]
            })
        return lessons

    def update_lesson(self, lesson_id: int, **kwargs) -> bool:
        """Dars yangilash"""
        allowed_fields = ['name', 'description', 'video_file_id', 'video_duration',
                          'order_num', 'has_test', 'is_free', 'is_active']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(lesson_id)
        sql = f"UPDATE Lessons SET {', '.join(updates)} WHERE id = ?"
        self.execute(sql, parameters=tuple(params), commit=True)
        return True

    def delete_lesson(self, lesson_id: int) -> bool:
        """Darsni o'chirish"""
        return self.update_lesson(lesson_id, is_active=False)

    def count_course_lessons(self, course_id: int) -> int:
        """Kursdagi darslar soni"""
        result = self.execute(
            """SELECT COUNT(*) FROM Lessons l
               JOIN Modules m ON l.module_id = m.id
               WHERE m.course_id = ? AND l.is_active = TRUE AND m.is_active = TRUE""",
            parameters=(course_id,),
            fetchone=True
        )
        return result[0] if result else 0

    def add_test(self, lesson_id: int, name: str = None, passing_score: int = 60) -> Optional[int]:
        """Darsga test qo'shish (yoki mavjudini qayta faollashtirish)"""
        try:
            # Avval o'chirilgan test bormi tekshirish
            existing = self.execute(
                "SELECT id FROM Tests WHERE lesson_id = ?",
                parameters=(lesson_id,),
                fetchone=True
            )

            if existing:
                # Mavjud testni qayta faollashtirish
                self.execute(
                    "UPDATE Tests SET is_active = TRUE, passing_score = ? WHERE lesson_id = ?",
                    parameters=(passing_score, lesson_id),
                    commit=True
                )
                test_id = existing[0]

                # ESKI SAVOLLARNI O'CHIRISH
                self.execute(
                    "DELETE FROM Questions WHERE test_id = ?",
                    parameters=(test_id,),
                    commit=True
                )
            else:
                # Yangi test yaratish
                self.execute(
                    "INSERT INTO Tests (lesson_id, name, passing_score) VALUES (?, ?, ?)",
                    parameters=(lesson_id, name, passing_score),
                    commit=True
                )

                result = self.execute(
                    "SELECT id FROM Tests WHERE lesson_id = ?",
                    parameters=(lesson_id,),
                    fetchone=True
                )
                test_id = result[0] if result else None

            # Darsda test borligini belgilash
            self.execute(
                "UPDATE Lessons SET has_test = TRUE WHERE id = ?",
                parameters=(lesson_id,),
                commit=True
            )

            return test_id

        except Exception as e:
            print(f"❌ Test qo'shishda xato: {e}")
            return None

    def get_test(self, test_id: int) -> Optional[Dict]:
        """Test ma'lumotlarini olish"""
        result = self.execute(
            """SELECT t.id, t.lesson_id, t.name, t.passing_score, t.time_limit, t.is_active, l.name
               FROM Tests t
               JOIN Lessons l ON t.lesson_id = l.id
               WHERE t.id = ?""",
            parameters=(test_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'lesson_id': result[1],
                'name': result[2],
                'passing_score': result[3],
                'time_limit': result[4],
                'is_active': bool(result[5]),
                'lesson_name': result[6]
            }
        return None

    def get_test_by_lesson(self, lesson_id: int) -> Optional[Dict]:
        """Dars bo'yicha testni olish"""
        result = self.execute(
            "SELECT id, name, passing_score, time_limit FROM Tests WHERE lesson_id = ? AND is_active = TRUE",
            parameters=(lesson_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'passing_score': result[2],
                'time_limit': result[3]
            }
        return None

    def delete_test(self, test_id: int) -> bool:
        """Testni o'chirish"""
        test = self.get_test(test_id)
        if not test:
            return False

        self.execute(
            "UPDATE Tests SET is_active = FALSE WHERE id = ?",
            parameters=(test_id,),
            commit=True
        )
        self.execute(
            "UPDATE Lessons SET has_test = FALSE WHERE id = ?",
            parameters=(test['lesson_id'],),
            commit=True
        )
        return True

    # ============================================================
    #                    SAVOL METODLARI
    # ============================================================

    def add_question(
            self,
            test_id: int,
            question_text: str,
            option_a: str,
            option_b: str,
            correct_answer: str,
            option_c: str = None,
            option_d: str = None
    ) -> Optional[int]:
        """Testga savol qo'shish"""
        try:
            result = self.execute(
                "SELECT COALESCE(MAX(order_num), 0) + 1 FROM Questions WHERE test_id = ?",
                parameters=(test_id,),
                fetchone=True
            )
            order_num = result[0] if result else 1

            self.execute(
                """INSERT INTO Questions (test_id, question_text, option_a, option_b, 
                   option_c, option_d, correct_answer, order_num)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                parameters=(test_id, question_text, option_a, option_b,
                            option_c, option_d, correct_answer.upper(), order_num),
                commit=True
            )

            result = self.execute(
                "SELECT id FROM Questions WHERE test_id = ? ORDER BY id DESC LIMIT 1",
                parameters=(test_id,),
                fetchone=True
            )
            return result[0] if result else None

        except Exception as e:
            print(f"❌ Savol qo'shishda xato: {e}")
            return None

    def add_questions_bulk(self, test_id: int, questions: List[Dict]) -> int:
        """Bir nechta savol qo'shish (Excel dan)"""
        count = 0
        for q in questions:
            result = self.add_question(
                test_id=test_id,
                question_text=q.get('question'),
                option_a=q.get('a'),
                option_b=q.get('b'),
                option_c=q.get('c'),
                option_d=q.get('d'),
                correct_answer=q.get('correct', 'A')
            )
            if result:
                count += 1
        return count

    def get_test_questions(self, test_id: int) -> List[Dict]:
        """Test savollari ro'yxati"""
        results = self.execute(
            """SELECT id, question_text, option_a, option_b, option_c, option_d, 
                      correct_answer, order_num
               FROM Questions WHERE test_id = ? AND is_active = TRUE ORDER BY order_num""",
            parameters=(test_id,),
            fetchall=True
        )
        questions = []
        for row in results:
            questions.append({
                'id': row[0],
                'question': row[1],
                'a': row[2],
                'b': row[3],
                'c': row[4],
                'd': row[5],
                'correct': row[6],
                'order_num': row[7]
            })
        return questions

    def count_test_questions(self, test_id: int) -> int:
        """Test savollari soni"""
        result = self.execute(
            "SELECT COUNT(*) FROM Questions WHERE test_id = ? AND is_active = TRUE",
            parameters=(test_id,),
            fetchone=True
        )
        return result[0] if result else 0

    def delete_question(self, question_id: int) -> bool:
        """Savolni o'chirish"""
        self.execute(
            "UPDATE Questions SET is_active = FALSE WHERE id = ?",
            parameters=(question_id,),
            commit=True
        )
        return True

    def delete_all_test_questions(self, test_id: int) -> bool:
        """Test barcha savollarini o'chirish"""
        self.execute(
            "UPDATE Questions SET is_active = FALSE WHERE test_id = ?",
            parameters=(test_id,),
            commit=True
        )
        return True

    # ============================================================
    #                    PROGRESS METODLARI
    # ============================================================

    def init_user_progress(self, telegram_id: int, course_id: int) -> bool:
        """Foydalanuvchi progressini boshlash (kurs sotib olganda)"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        lessons = self.get_course_lessons(course_id)
        if not lessons:
            return False

        # Birinchi darsni ochiq qilish
        first_lesson = lessons[0] if lessons else None

        for i, lesson in enumerate(lessons):
            status = 'unlocked' if i == 0 else 'locked'
            self.execute(
                """INSERT OR IGNORE INTO UserProgress (user_id, lesson_id, status) 
                   VALUES (?, ?, ?)""",
                parameters=(user_id, lesson['id'], status),
                commit=True
            )

        return True

    def get_lesson_status(self, telegram_id: int, lesson_id: int) -> str:
        """Dars statusini olish: locked, unlocked, completed"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return 'locked'

        result = self.execute(
            "SELECT status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
            parameters=(user_id, lesson_id),
            fetchone=True
        )
        return result[0] if result else 'locked'

    def unlock_lesson(self, telegram_id: int, lesson_id: int) -> bool:
        """Darsni ochish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        self.execute(
            """INSERT OR REPLACE INTO UserProgress (user_id, lesson_id, status, started_at)
               VALUES (?, ?, 'unlocked', ?)""",
            parameters=(user_id, lesson_id, datetime.now(TASHKENT_TZ).isoformat()),
            commit=True
        )
        return True

    def complete_lesson(self, telegram_id: int, lesson_id: int) -> bool:
        """Darsni tugatish va keyingisini ochish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        # Hozirgi darsni completed qilish
        self.execute(
            """UPDATE UserProgress SET status = 'completed', completed_at = ?
               WHERE user_id = ? AND lesson_id = ?""",
            parameters=(datetime.now(TASHKENT_TZ).isoformat(), user_id, lesson_id),
            commit=True
        )

        # Keyingi darsni ochish
        lesson = self.get_lesson(lesson_id)
        if lesson:
            next_lesson = self.execute(
                """SELECT l.id FROM Lessons l
                   JOIN Modules m ON l.module_id = m.id
                   WHERE m.course_id = ? AND l.is_active = TRUE AND m.is_active = TRUE
                   AND (m.order_num > (SELECT order_num FROM Modules WHERE id = ?)
                        OR (m.order_num = (SELECT order_num FROM Modules WHERE id = ?) 
                            AND l.order_num > ?))
                   ORDER BY m.order_num, l.order_num LIMIT 1""",
                parameters=(lesson['course_id'], lesson['module_id'],
                            lesson['module_id'], lesson['order_num']),
                fetchone=True
            )

            if next_lesson:
                self.unlock_lesson(telegram_id, next_lesson[0])

        return True

    def get_user_course_progress(self, telegram_id: int, course_id: int) -> Dict:
        """Foydalanuvchining kurs progressi"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return {'completed': 0, 'total': 0, 'percentage': 0}

        total = self.count_course_lessons(course_id)

        result = self.execute(
            """SELECT COUNT(*) FROM UserProgress up
               JOIN Lessons l ON up.lesson_id = l.id
               JOIN Modules m ON l.module_id = m.id
               WHERE up.user_id = ? AND m.course_id = ? AND up.status = 'completed'""",
            parameters=(user_id, course_id),
            fetchone=True
        )
        completed = result[0] if result else 0

        percentage = round((completed / total * 100), 1) if total > 0 else 0

        return {
            'completed': completed,
            'total': total,
            'percentage': percentage
        }

    def get_user_lessons_with_status(self, telegram_id: int, course_id: int) -> List[Dict]:
        """Foydalanuvchi uchun darslar statuslari bilan"""
        user_id = self.get_user_id(telegram_id)

        lessons = self.get_course_lessons(course_id)

        for lesson in lessons:
            if user_id:
                result = self.execute(
                    "SELECT status FROM UserProgress WHERE user_id = ? AND lesson_id = ?",
                    parameters=(user_id, lesson['id']),
                    fetchone=True
                )
                lesson['status'] = result[0] if result else 'locked'
            else:
                lesson['status'] = 'locked'

            # Bepul darslar har doim ochiq
            if lesson['is_free']:
                lesson['status'] = 'unlocked' if lesson['status'] == 'locked' else lesson['status']

        return lessons

    # ============================================================
    #                    TEST NATIJASI METODLARI
    # ============================================================

    def save_test_result(
            self,
            telegram_id: int,
            test_id: int,
            score: int,
            total_questions: int,
            correct_answers: int,
            answers: Dict = None
    ) -> Optional[int]:
        """Test natijasini saqlash"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None

        test = self.get_test(test_id)
        if not test:
            return None

        passed = score >= test['passing_score']

        try:
            self.execute(
                """INSERT INTO TestResults (user_id, test_id, score, total_questions, 
                   correct_answers, passed, answers_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                parameters=(user_id, test_id, score, total_questions, correct_answers,
                            passed, json.dumps(answers) if answers else None),
                commit=True
            )

            # Ball qo'shish
            if passed:
                self.add_score(telegram_id, 10)  # Test uchun 10 ball
                if score == 100:
                    self.add_score(telegram_id, 5)  # Bonus 100% uchun

            result = self.execute(
                "SELECT id FROM TestResults WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                parameters=(user_id,),
                fetchone=True
            )
            return result[0] if result else None

        except Exception as e:
            print(f"❌ Test natijasini saqlashda xato: {e}")
            return None

    def get_user_test_results(self, telegram_id: int, course_id: int = None) -> List[Dict]:
        """Foydalanuvchi test natijalari"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return []

        if course_id:
            sql = """SELECT tr.id, tr.test_id, tr.score, tr.correct_answers, tr.total_questions,
                            tr.passed, tr.completed_at, t.name, l.name
                     FROM TestResults tr
                     JOIN Tests t ON tr.test_id = t.id
                     JOIN Lessons l ON t.lesson_id = l.id
                     JOIN Modules m ON l.module_id = m.id
                     WHERE tr.user_id = ? AND m.course_id = ?
                     ORDER BY tr.completed_at DESC"""
            results = self.execute(sql, parameters=(user_id, course_id), fetchall=True)
        else:
            sql = """SELECT tr.id, tr.test_id, tr.score, tr.correct_answers, tr.total_questions,
                            tr.passed, tr.completed_at, t.name, l.name
                     FROM TestResults tr
                     JOIN Tests t ON tr.test_id = t.id
                     JOIN Lessons l ON t.lesson_id = l.id
                     WHERE tr.user_id = ?
                     ORDER BY tr.completed_at DESC LIMIT 20"""
            results = self.execute(sql, parameters=(user_id,), fetchall=True)

        test_results = []
        for row in results:
            test_results.append({
                'id': row[0],
                'test_id': row[1],
                'score': row[2],
                'correct': row[3],
                'total': row[4],
                'passed': bool(row[5]),
                'completed_at': row[6],
                'test_name': row[7],
                'lesson_name': row[8]
            })
        return test_results

    def has_passed_test(self, telegram_id: int, test_id: int) -> bool:
        """Foydalanuvchi testdan o'tganmi"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        result = self.execute(
            "SELECT 1 FROM TestResults WHERE user_id = ? AND test_id = ? AND passed = TRUE",
            parameters=(user_id, test_id),
            fetchone=True
        )
        return result is not None

    # ============================================================
    #                    FIKR-MULOHAZA METODLARI
    # ============================================================

    def add_feedback(
            self,
            telegram_id: int,
            lesson_id: int,
            rating: int,
            comment: str = None
    ) -> bool:
        """Fikr qo'shish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        # Ball berish (sozlamalardan)
        feedback_score = int(self.get_setting('feedback_score', '2'))

        try:
            self.execute(
                """INSERT OR REPLACE INTO Feedbacks (user_id, lesson_id, rating, comment, score_given)
                   VALUES (?, ?, ?, ?, ?)""",
                parameters=(user_id, lesson_id, rating, comment, feedback_score),
                commit=True
            )

            # Ball qo'shish
            self.add_score(telegram_id, feedback_score)

            return True
        except Exception as e:
            print(f"❌ Fikr qo'shishda xato: {e}")
            return False

    def has_feedback(self, telegram_id: int, lesson_id: int) -> bool:
        """Foydalanuvchi fikr qoldirganmi"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        result = self.execute(
            "SELECT 1 FROM Feedbacks WHERE user_id = ? AND lesson_id = ?",
            parameters=(user_id, lesson_id),
            fetchone=True
        )
        return result is not None

    def get_lesson_feedbacks(self, lesson_id: int) -> List[Dict]:
        """Dars fikrlari"""
        results = self.execute(
            """SELECT f.id, f.rating, f.comment, f.created_at, u.username, u.full_name
               FROM Feedbacks f
               JOIN Users u ON f.user_id = u.id
               WHERE f.lesson_id = ?
               ORDER BY f.created_at DESC""",
            parameters=(lesson_id,),
            fetchall=True
        )
        feedbacks = []
        for row in results:
            feedbacks.append({
                'id': row[0],
                'rating': row[1],
                'comment': row[2],
                'created_at': row[3],
                'username': row[4],
                'full_name': row[5]
            })
        return feedbacks

    def get_lesson_average_rating(self, lesson_id: int) -> float:
        """Dars o'rtacha bahosi"""
        result = self.execute(
            "SELECT AVG(rating) FROM Feedbacks WHERE lesson_id = ?",
            parameters=(lesson_id,),
            fetchone=True
        )
        return round(result[0], 1) if result and result[0] else 0.0

    def get_all_feedbacks(self, limit: int = 50) -> List[Dict]:
        """Barcha fikrlar (admin uchun)"""
        results = self.execute(
            """SELECT f.id, f.rating, f.comment, f.created_at, 
                      u.username, u.full_name, l.name as lesson_name
               FROM Feedbacks f
               JOIN Users u ON f.user_id = u.id
               JOIN Lessons l ON f.lesson_id = l.id
               ORDER BY f.created_at DESC LIMIT ?""",
            parameters=(limit,),
            fetchall=True
        )
        feedbacks = []
        for row in results:
            feedbacks.append({
                'id': row[0],
                'rating': row[1],
                'comment': row[2],
                'created_at': row[3],
                'username': row[4],
                'full_name': row[5],
                'lesson_name': row[6]
            })
        return feedbacks

    # ============================================================
    #                    TO'LOV METODLARI
    # ============================================================

    def create_payment(
            self,
            telegram_id: int,
            course_id: int,
            amount: float,
            receipt_file_id: str = None
    ) -> Optional[int]:
        """To'lov so'rovi yaratish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None

        try:
            self.execute(
                """INSERT INTO Payments (user_id, course_id, amount, receipt_file_id)
                   VALUES (?, ?, ?, ?)""",
                parameters=(user_id, course_id, amount, receipt_file_id),
                commit=True
            )

            result = self.execute(
                "SELECT id FROM Payments WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                parameters=(user_id,),
                fetchone=True
            )
            return result[0] if result else None

        except Exception as e:
            print(f"❌ To'lov yaratishda xato: {e}")
            return None

    def get_payment(self, payment_id: int) -> Optional[Dict]:
        """To'lov ma'lumotlari"""
        result = self.execute(
            """SELECT p.id, p.user_id, p.course_id, p.amount, p.receipt_file_id,
                      p.status, p.admin_note, p.created_at, p.updated_at,
                      u.telegram_id, u.username, c.name
               FROM Payments p
               JOIN Users u ON p.user_id = u.id
               JOIN Courses c ON p.course_id = c.id
               WHERE p.id = ?""",
            parameters=(payment_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'user_id': result[1],
                'course_id': result[2],
                'amount': float(result[3]),
                'receipt_file_id': result[4],
                'status': result[5],
                'admin_note': result[6],
                'created_at': result[7],
                'updated_at': result[8],
                'telegram_id': result[9],
                'username': result[10],
                'course_name': result[11]
            }
        return None

    def get_pending_payments(self) -> List[Dict]:
        """Kutilayotgan to'lovlar"""
        results = self.execute(
            """SELECT p.id, p.amount, p.receipt_file_id, p.created_at,
                      u.telegram_id, u.username, u.full_name, c.name
               FROM Payments p
               JOIN Users u ON p.user_id = u.id
               JOIN Courses c ON p.course_id = c.id
               WHERE p.status = 'pending'
               ORDER BY p.created_at ASC""",
            fetchall=True
        )
        payments = []
        for row in results:
            payments.append({
                'id': row[0],
                'amount': float(row[1]),
                'receipt_file_id': row[2],
                'created_at': row[3],
                'telegram_id': row[4],
                'username': row[5],
                'full_name': row[6],
                'course_name': row[7]
            })
        return payments

        # database/user_db.py ichiga joylang:

    def approve_payment(self, payment_id: int, admin_telegram_id: int) -> bool:
            """
            To'lovni tasdiqlash (TUZATILGAN)
            Faqat statusni o'zgartiradi va darsni ochadi.
            Referalga TEGMAYDI (buni admin_payments.py qiladi).
            """
            payment = self.get_payment(payment_id)
            if not payment or payment['status'] != 'pending':
                return False

            admin_id = self.get_user_id(admin_telegram_id)

            # 1. To'lovni tasdiqlash
            self.execute(
                """UPDATE Payments SET status = 'approved', admin_id = ?, updated_at = ?
                   WHERE id = ?""",
                parameters=(admin_id, datetime.now(TASHKENT_TZ).isoformat(), payment_id),
                commit=True
            )

            # 2. Kursga dostup berish
            self.init_user_progress(payment['telegram_id'], payment['course_id'])

            return True

    def reject_payment(self, payment_id: int, admin_telegram_id: int, note: str = None) -> bool:
        """To'lovni rad etish"""
        admin_id = self.get_user_id(admin_telegram_id)

        self.execute(
            """UPDATE Payments SET status = 'rejected', admin_id = ?, admin_note = ?, updated_at = ?
               WHERE id = ? AND status = 'pending'""",
            parameters=(admin_id, note, datetime.now(TASHKENT_TZ).isoformat(), payment_id),
            commit=True
        )
        return True

    def count_pending_payments(self) -> int:
        """Kutilayotgan to'lovlar soni"""
        result = self.execute(
            "SELECT COUNT(*) FROM Payments WHERE status = 'pending'",
            fetchone=True
        )
        return result[0] if result else 0

    # ============================================================
    #                    QO'LDA DOSTUP METODLARI
    # ============================================================

    def grant_manual_access(
            self,
            telegram_id: int,
            course_id: int,
            admin_telegram_id: int,
            reason: str = None,
            expires_days: int = None
    ) -> bool:
        """Qo'lda dostup berish"""
        user_id = self.get_user_id(telegram_id)
        admin_id = self.get_user_id(admin_telegram_id)

        if not user_id or not admin_id:
            return False

        expires_at = None
        if expires_days:
            expires_at = (datetime.now(TASHKENT_TZ) + timedelta(days=expires_days)).isoformat()

        try:
            self.execute(
                """INSERT OR REPLACE INTO ManualAccess 
                   (user_id, course_id, granted_by, reason, expires_at, is_active)
                   VALUES (?, ?, ?, ?, ?, TRUE)""",
                parameters=(user_id, course_id, admin_id, reason, expires_at),
                commit=True
            )

            # Progress boshlash
            self.init_user_progress(telegram_id, course_id)

            return True
        except Exception as e:
            print(f"❌ Manual access xato: {e}")
            return False

    def revoke_access(self, telegram_id: int, course_id: int) -> bool:
        """Dostupni olish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        self.execute(
            "UPDATE ManualAccess SET is_active = FALSE WHERE user_id = ? AND course_id = ?",
            parameters=(user_id, course_id),
            commit=True
        )
        return True

    def has_course_access(self, telegram_id: int, course_id: int) -> bool:
        """Foydalanuvchida kursga dostup bormi"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        # To'lov orqali
        result = self.execute(
            """SELECT 1 FROM Payments 
               WHERE user_id = ? AND course_id = ? AND status = 'approved'""",
            parameters=(user_id, course_id),
            fetchone=True
        )
        if result:
            return True

        # Manual access orqali
        result = self.execute(
            """SELECT 1 FROM ManualAccess 
               WHERE user_id = ? AND course_id = ? AND is_active = TRUE
               AND (expires_at IS NULL OR expires_at > ?)""",
            parameters=(user_id, course_id, datetime.now(TASHKENT_TZ).isoformat()),
            fetchone=True
        )
        return result is not None

    # ============================================================
    #                    SERTIFIKAT METODLARI
    # ============================================================

    def generate_certificate(self, telegram_id: int, course_id: int) -> Optional[Dict]:
        """Sertifikat yaratish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None

        # Progress tekshirish
        progress = self.get_user_course_progress(telegram_id, course_id)
        if progress['percentage'] < 100:
            return None

        # Test natijalarini hisoblash
        test_results = self.get_user_test_results(telegram_id, course_id)
        total_score = sum(r['score'] for r in test_results)
        avg_score = total_score / len(test_results) if test_results else 0

        # Daraja aniqlash
        gold = int(self.get_setting('gold_threshold', '90'))
        silver = int(self.get_setting('silver_threshold', '75'))
        bronze = int(self.get_setting('bronze_threshold', '60'))

        if avg_score >= gold:
            grade = 'GOLD'
        elif avg_score >= silver:
            grade = 'SILVER'
        elif avg_score >= bronze:
            grade = 'BRONZE'
        else:
            grade = 'PARTICIPANT'

        # Unikal kod
        import uuid
        cert_code = f"CERT-{uuid.uuid4().hex[:8].upper()}"

        try:
            self.execute(
                """INSERT OR REPLACE INTO Certificates 
                   (user_id, course_id, certificate_code, total_score, percentage, grade)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                parameters=(user_id, course_id, cert_code, total_score, avg_score, grade),
                commit=True
            )

            return {
                'code': cert_code,
                'total_score': total_score,
                'percentage': avg_score,
                'grade': grade
            }
        except Exception as e:
            print(f"❌ Sertifikat yaratishda xato: {e}")
            return None

    def get_certificate(self, telegram_id: int, course_id: int) -> Optional[Dict]:
        """Sertifikat olish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None

        result = self.execute(
            """SELECT c.certificate_code, c.total_score, c.percentage, c.grade, 
                      c.file_id, c.created_at, co.name, u.full_name
               FROM Certificates c
               JOIN Courses co ON c.course_id = co.id
               JOIN Users u ON c.user_id = u.id
               WHERE c.user_id = ? AND c.course_id = ?""",
            parameters=(user_id, course_id),
            fetchone=True
        )
        if result:
            return {
                'code': result[0],
                'total_score': result[1],
                'percentage': float(result[2]),
                'grade': result[3],
                'file_id': result[4],
                'created_at': result[5],
                'course_name': result[6],
                'user_name': result[7]
            }
        return None

    def update_certificate_file(self, telegram_id: int, course_id: int, file_id: str) -> bool:
        """Sertifikat faylini yangilash"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        self.execute(
            "UPDATE Certificates SET file_id = ? WHERE user_id = ? AND course_id = ?",
            parameters=(file_id, user_id, course_id),
            commit=True
        )
        return True

    # ============================================================
    #                    SOZLAMALAR METODLARI
    # ============================================================

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Sozlama qiymatini olish"""
        result = self.execute(
            "SELECT value FROM Settings WHERE key = ?",
            parameters=(key,),
            fetchone=True
        )
        return result[0] if result else default

    def set_setting(self, key: str, value: str) -> bool:
        """Sozlamani o'zgartirish"""
        try:
            self.execute(
                """INSERT OR REPLACE INTO Settings (key, value, updated_at)
                   VALUES (?, ?, ?)""",
                parameters=(key, value, datetime.now(TASHKENT_TZ).isoformat()),
                commit=True
            )
            return True
        except Exception as e:
            print(f"❌ Sozlama o'zgartirishda xato: {e}")
            return False

    def get_all_settings(self) -> Dict:
        """Barcha sozlamalar"""
        results = self.execute(
            "SELECT key, value, description FROM Settings",
            fetchall=True
        )
        settings = {}
        for row in results:
            settings[row[0]] = {
                'value': row[1],
                'description': row[2]
            }
        return settings

    # ============================================================
    #                    STATISTIKA METODLARI
    # ============================================================

    def get_dashboard_stats(self) -> Dict:
        """Admin dashboard statistikasi"""
        now = datetime.now(TASHKENT_TZ)
        today_start = now.replace(hour=0, minute=0, second=0).isoformat()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0).isoformat()
        month_start = now.replace(day=1, hour=0, minute=0, second=0).isoformat()

        stats = {}

        # Foydalanuvchilar
        stats['total_users'] = self.execute(
            "SELECT COUNT(*) FROM Users", fetchone=True
        )[0]

        stats['new_users_today'] = self.execute(
            "SELECT COUNT(*) FROM Users WHERE created_at >= ?",
            parameters=(today_start,), fetchone=True
        )[0]

        stats['new_users_week'] = self.execute(
            "SELECT COUNT(*) FROM Users WHERE created_at >= ?",
            parameters=(week_start,), fetchone=True
        )[0]

        stats['new_users_month'] = self.execute(
            "SELECT COUNT(*) FROM Users WHERE created_at >= ?",
            parameters=(month_start,), fetchone=True
        )[0]

        # To'lovlar
        stats['pending_payments'] = self.count_pending_payments()

        stats['approved_payments_month'] = self.execute(
            """SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM Payments 
               WHERE status = 'approved' AND updated_at >= ?""",
            parameters=(month_start,), fetchone=True
        )

        # Kurslar
        stats['total_courses'] = self.execute(
            "SELECT COUNT(*) FROM Courses WHERE is_active = TRUE", fetchone=True
        )[0]

        stats['total_lessons'] = self.execute(
            """SELECT COUNT(*) FROM Lessons l
               JOIN Modules m ON l.module_id = m.id
               WHERE l.is_active = TRUE AND m.is_active = TRUE""",
            fetchone=True
        )[0]

        # Fikrlar
        result = self.execute(
            "SELECT AVG(rating) FROM Feedbacks", fetchone=True
        )
        stats['avg_rating'] = round(result[0], 1) if result and result[0] else 0

        # Sertifikatlar
        stats['certificates_issued'] = self.execute(
            "SELECT COUNT(*) FROM Certificates", fetchone=True
        )[0]

        return stats

    def get_course_stats(self, course_id: int) -> Dict:
        """Kurs statistikasi"""
        stats = {}

        # Modullar va darslar soni
        stats['modules'] = self.execute(
            "SELECT COUNT(*) FROM Modules WHERE course_id = ? AND is_active = TRUE",
            parameters=(course_id,), fetchone=True
        )[0]

        stats['lessons'] = self.count_course_lessons(course_id)

        # O'quvchilar soni
        stats['students'] = self.execute(
            """SELECT COUNT(DISTINCT user_id) FROM UserProgress up
               JOIN Lessons l ON up.lesson_id = l.id
               JOIN Modules m ON l.module_id = m.id
               WHERE m.course_id = ?""",
            parameters=(course_id,), fetchone=True
        )[0]

        # Tugatganlar
        stats['completed'] = self.execute(
            "SELECT COUNT(*) FROM Certificates WHERE course_id = ?",
            parameters=(course_id,), fetchone=True
        )[0]

        # O'rtacha progress
        result = self.execute(
            """SELECT AVG(progress) FROM (
                   SELECT (COUNT(CASE WHEN up.status = 'completed' THEN 1 END) * 100.0 / 
                           COUNT(*)) as progress
                   FROM UserProgress up
                   JOIN Lessons l ON up.lesson_id = l.id
                   JOIN Modules m ON l.module_id = m.id
                   WHERE m.course_id = ?
                   GROUP BY up.user_id
               )""",
            parameters=(course_id,), fetchone=True
        )
        stats['avg_progress'] = round(result[0], 1) if result and result[0] else 0

        return stats

    def get_inactive_users(self, days: int = 3) -> List[Dict]:
        """Faol bo'lmagan foydalanuvchilar (eslatma uchun)"""
        threshold = (datetime.now(TASHKENT_TZ) - timedelta(days=days)).isoformat()

        results = self.execute(
            """SELECT u.telegram_id, u.username, u.full_name, u.last_active
               FROM Users u
               WHERE u.last_active < ? AND u.is_active = TRUE
               AND EXISTS (
                   SELECT 1 FROM UserProgress up WHERE up.user_id = u.id
               )""",
            parameters=(threshold,),
            fetchall=True
        )

        users = []
        for row in results:
            users.append({
                'telegram_id': row[0],
                'username': row[1],
                'full_name': row[2],
                'last_active': row[3]
            })
        return users

    def get_top_students(self, limit: int = 10) -> List[Dict]:
        """Eng yaxshi o'quvchilar"""
        results = self.execute(
            """SELECT telegram_id, username, full_name, total_score
               FROM Users
               WHERE total_score > 0
               ORDER BY total_score DESC LIMIT ?""",
            parameters=(limit,),
            fetchall=True
        )

        students = []
        for i, row in enumerate(results, 1):
            students.append({
                'rank': i,
                'telegram_id': row[0],
                'username': row[1],
                'full_name': row[2],
                'score': row[3]
            })
        return students

    def delete_user(self, telegram_id: int) -> bool:
        """Foydalanuvchini butunlay o'chirish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        self.execute(
            "DELETE FROM Users WHERE id = ?",
            parameters=(user_id,),
            commit=True
        )
        return True

    def get_admin(self, telegram_id: int) -> Optional[Dict]:
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None

        result = self.execute(
            """SELECT a.id, u.telegram_id, a.name, a.is_super_admin, a.created_at
               FROM Admins a
               JOIN Users u ON a.user_id = u.id
               WHERE a.user_id = ?""",
            parameters=(user_id,),
            fetchone=True
        )

        if result:
            return {
                'id': result[0],
                'telegram_id': result[1],
                'name': result[2],
                'is_super': bool(result[3]),
                'created_at': result[4]
            }
        return None

    def delete_all_users(self) -> int:
        """Barcha foydalanuvchilarni o'chirish (adminlardan tashqari)"""
        # Avval sonini olish
        result = self.execute(
            "SELECT COUNT(*) FROM Users WHERE id NOT IN (SELECT user_id FROM Admins)",
            fetchone=True
        )
        count = result[0] if result else 0

        # O'chirish
        self.execute(
            "DELETE FROM Users WHERE id NOT IN (SELECT user_id FROM Admins)",
            commit=True
        )
        return count


    def add_material(
            self,
            lesson_id: int,
            name: str,
            file_type: str,
            file_id: str,
            file_size: int = None,
            description: str = None
    ) -> Optional[int]:
        """
        Darsga material qo'shish

        Args:
            lesson_id: Dars ID
            name: Fayl nomi (masalan: "1-dars slides.pptx")
            file_type: Fayl turi (pdf, pptx, docx, xlsx, image, other)
            file_id: Telegram file_id
            file_size: Fayl hajmi (baytda)
            description: Tavsif (ixtiyoriy)

        Returns:
            Material ID yoki None
        """
        try:
            # Tartib raqamini olish
            result = self.execute(
                "SELECT COALESCE(MAX(order_num), 0) + 1 FROM LessonMaterials WHERE lesson_id = ?",
                parameters=(lesson_id,),
                fetchone=True
            )
            order_num = result[0] if result else 1

            self.execute(
                """INSERT INTO LessonMaterials 
                   (lesson_id, name, file_type, file_id, file_size, description, order_num)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                parameters=(lesson_id, name, file_type.lower(), file_id, file_size, description, order_num),
                commit=True
            )

            result = self.execute(
                "SELECT id FROM LessonMaterials WHERE lesson_id = ? ORDER BY id DESC LIMIT 1",
                parameters=(lesson_id,),
                fetchone=True
            )
            return result[0] if result else None

        except Exception as e:
            print(f"❌ Material qo'shishda xato: {e}")
            return None

    def get_material(self, material_id: int) -> Optional[Dict]:
        """Material ma'lumotlarini olish"""
        result = self.execute(
            """SELECT m.id, m.lesson_id, m.name, m.file_type, m.file_id, 
                      m.file_size, m.description, m.order_num, m.created_at, l.name
               FROM LessonMaterials m
               JOIN Lessons l ON m.lesson_id = l.id
               WHERE m.id = ? AND m.is_active = TRUE""",
            parameters=(material_id,),
            fetchone=True
        )
        if result:
            return {
                'id': result[0],
                'lesson_id': result[1],
                'name': result[2],
                'file_type': result[3],
                'file_id': result[4],
                'file_size': result[5],
                'description': result[6],
                'order_num': result[7],
                'created_at': result[8],
                'lesson_name': result[9]
            }
        return None

    def get_lesson_materials(self, lesson_id: int) -> List[Dict]:
        """Dars materiallari ro'yxati"""
        results = self.execute(
            """SELECT id, name, file_type, file_id, file_size, description, order_num
               FROM LessonMaterials 
               WHERE lesson_id = ? AND is_active = TRUE 
               ORDER BY order_num""",
            parameters=(lesson_id,),
            fetchall=True
        )
        materials = []
        for row in results:
            materials.append({
                'id': row[0],
                'name': row[1],
                'file_type': row[2],
                'file_id': row[3],
                'file_size': row[4],
                'description': row[5],
                'order_num': row[6]
            })
        return materials

    def update_material(self, material_id: int, **kwargs) -> bool:
        """Material yangilash"""
        allowed_fields = ['name', 'file_type', 'file_id', 'file_size', 'description', 'order_num']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(material_id)
        sql = f"UPDATE LessonMaterials SET {', '.join(updates)} WHERE id = ?"
        self.execute(sql, parameters=tuple(params), commit=True)
        return True

    def delete_material(self, material_id: int) -> bool:
        """Materialni o'chirish (soft delete)"""
        self.execute(
            "UPDATE LessonMaterials SET is_active = FALSE WHERE id = ?",
            parameters=(material_id,),
            commit=True
        )
        return True

    def delete_lesson_materials(self, lesson_id: int) -> bool:
        """Darsning barcha materiallarini o'chirish"""
        self.execute(
            "UPDATE LessonMaterials SET is_active = FALSE WHERE lesson_id = ?",
            parameters=(lesson_id,),
            commit=True
        )
        return True

    def count_lesson_materials(self, lesson_id: int) -> int:
        """Dars materiallari soni"""
        result = self.execute(
            "SELECT COUNT(*) FROM LessonMaterials WHERE lesson_id = ? AND is_active = TRUE",
            parameters=(lesson_id,),
            fetchone=True
        )
        return result[0] if result else 0

    def get_materials_by_type(self, lesson_id: int, file_type: str) -> List[Dict]:
        """Turi bo'yicha materiallar (masalan: faqat PDF lar)"""
        results = self.execute(
            """SELECT id, name, file_id, file_size, description
               FROM LessonMaterials 
               WHERE lesson_id = ? AND file_type = ? AND is_active = TRUE 
               ORDER BY order_num""",
            parameters=(lesson_id, file_type.lower()),
            fetchall=True
        )
        materials = []
        for row in results:
            materials.append({
                'id': row[0],
                'name': row[1],
                'file_id': row[2],
                'file_size': row[3],
                'description': row[4]
            })
        return materials

    def reorder_materials(self, lesson_id: int, material_ids: List[int]) -> bool:
        """Materiallar tartibini o'zgartirish"""
        try:
            for order, material_id in enumerate(material_ids, 1):
                self.execute(
                    "UPDATE LessonMaterials SET order_num = ? WHERE id = ? AND lesson_id = ?",
                    parameters=(order, material_id, lesson_id),
                    commit=True
                )
            return True
        except Exception as e:
            print(f"❌ Tartib o'zgartirishda xato: {e}")
            return False

    # ============================================================
    #                    REFERAL METODLARI
    # ============================================================

    def generate_referral_code(self, telegram_id: int) -> Optional[str]:
        """Foydalanuvchi uchun unikal referal kod yaratish"""
        user = self.get_user(telegram_id)
        if not user:
            return None

        # Agar allaqachon bor bo'lsa, qaytarish
        if user.get('referral_code'):
            return user['referral_code']

        # Yangi kod yaratish
        import random
        import string

        while True:
            code = 'REF_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

            # Unikal ekanini tekshirish
            existing = self.execute(
                "SELECT 1 FROM Users WHERE referral_code = ?",
                parameters=(code,),
                fetchone=True
            )
            if not existing:
                break

        # Saqlash
        self.execute(
            "UPDATE Users SET referral_code = ? WHERE telegram_id = ?",
            parameters=(code, telegram_id),
            commit=True
        )

        return code

    def get_referral_code(self, telegram_id: int) -> Optional[str]:
        """Foydalanuvchi referal kodini olish (yo'q bo'lsa yaratish)"""
        result = self.execute(
            "SELECT referral_code FROM Users WHERE telegram_id = ?",
            parameters=(telegram_id,),
            fetchone=True
        )

        if result and result[0]:
            return result[0]

        # Yo'q bo'lsa yaratish
        return self.generate_referral_code(telegram_id)

    def get_user_by_referral_code(self, code: str) -> Optional[Dict]:
        """Referal kod orqali foydalanuvchini topish"""
        result = self.execute(
            """SELECT id, telegram_id, username, full_name, referral_count
               FROM Users WHERE referral_code = ?""",
            parameters=(code,),
            fetchone=True
        )

        if result:
            return {
                'id': result[0],
                'telegram_id': result[1],
                'username': result[2],
                'full_name': result[3],
                'referral_count': result[4] or 0
            }
        return None

    def register_referral(self, referrer_telegram_id: int, referred_telegram_id: int) -> bool:
        """
        Yangi referal ro'yxatdan o'tkazish

        Args:
            referrer_telegram_id: Taklif qiluvchi (havola egasi)
            referred_telegram_id: Taklif qilingan (yangi user)
        """
        # O'zini o'zi taklif qila olmaydi
        if referrer_telegram_id == referred_telegram_id:
            return False

        referrer_id = self.get_user_id(referrer_telegram_id)
        referred_id = self.get_user_id(referred_telegram_id)

        if not referrer_id or not referred_id:
            return False

        # Allaqachon taklif qilinganmi tekshirish
        existing = self.execute(
            "SELECT 1 FROM Referrals WHERE referred_id = ?",
            parameters=(referred_id,),
            fetchone=True
        )
        if existing:
            return False

        try:
            # Referrals jadvaliga qo'shish
            self.execute(
                """INSERT INTO Referrals (referrer_id, referred_id, status)
                   VALUES (?, ?, 'registered')""",
                parameters=(referrer_id, referred_id),
                commit=True
            )

            # Users jadvalida referred_by ni yangilash
            self.execute(
                "UPDATE Users SET referred_by = ? WHERE id = ?",
                parameters=(referrer_id, referred_id),
                commit=True
            )

            # Taklif qiluvchining referral_count ni oshirish
            self.execute(
                "UPDATE Users SET referral_count = COALESCE(referral_count, 0) + 1 WHERE id = ?",
                parameters=(referrer_id,),
                commit=True
            )

            # Ro'yxatdan o'tish bonusini berish
            register_bonus = int(self.get_setting('referral_bonus_register', '5'))
            if register_bonus > 0:
                self.add_score(referrer_telegram_id, register_bonus)

                # Bonus berilganini saqlash
                self.execute(
                    "UPDATE Referrals SET bonus_given = ? WHERE referrer_id = ? AND referred_id = ?",
                    parameters=(register_bonus, referrer_id, referred_id),
                    commit=True
                )

            return True

        except Exception as e:
            print(f"❌ Referal ro'yxatda xato: {e}")
            return False

    def convert_referral(self, referred_internal_id: int, amount_paid: float) -> dict:
        """
        Referal to'lov qilganda (TUZATILGAN VA DEBUG QILINGAN VERSIYA)
        Diqqat: Bu funksiya Telegram ID emas, Bazadagi ID (user_id) ni qabul qiladi.
        """
        print(f"🔍 REFERAL DEBUG: User ID {referred_internal_id} uchun tekshirilmoqda...")

        # 1. Refererni qidiramiz
        # Diqqat: r.status = 'registered' bo'lishi shart. Agar 'paid' bo'lsa, ikkinchi marta to'lamaydi.
        res = self.execute(
            """SELECT r.id, r.referrer_id, u.telegram_id, u.full_name, u.phone 
               FROM Referrals r 
               JOIN Users u ON r.referrer_id = u.id 
               WHERE r.referred_id = ?""",
            (referred_internal_id,), fetchone=True
        )

        if not res:
            print(f"❌ REFERAL DEBUG: Bu foydalanuvchini (ID: {referred_internal_id}) hech kim taklif qilmagan.")
            return {'success': False}

        ref_id, referrer_id, referrer_tg_id, referrer_name, referrer_phone = res

        # 2. Allaqachon to'langanmi tekshirish
        check_status = self.execute("SELECT status FROM Referrals WHERE id=?", (ref_id,), fetchone=True)
        if check_status and check_status[0] == 'paid':
            print(f"⚠️ REFERAL DEBUG: Bu user uchun allaqachon bonus to'langan!")
            return {'success': False}

        # 3. Cashback hisoblash
        percent = int(self.get_setting('referral_cashback', '10'))
        cashback = amount_paid * percent / 100

        try:
            # Statusni yangilaymiz
            self.execute(
                "UPDATE Referrals SET status='paid', bonus_given=?, converted_at=? WHERE id=?",
                (cashback, datetime.now(TASHKENT_TZ).isoformat(), ref_id), commit=True
            )

            print(f"✅ REFERAL DEBUG: Muvaffaqiyatli! {referrer_name} ga {cashback} so'm yozildi.")

            return {
                'success': True,
                'referrer_tg_id': referrer_tg_id,
                'referrer_name': referrer_name,
                'referrer_phone': referrer_phone,
                'amount': cashback
            }
        except Exception as e:
            print(f"❌ REFERAL DEBUG XATO: {e}")
            return {'success': False}

    def get_user_referrals(self, telegram_id: int) -> List[Dict]:
        """Foydalanuvchi taklif qilgan odamlar ro'yxati"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return []

        results = self.execute(
            """SELECT u.telegram_id, u.username, u.full_name, 
                      r.status, r.bonus_given, r.created_at, r.converted_at
               FROM Referrals r
               JOIN Users u ON r.referred_id = u.id
               WHERE r.referrer_id = ?
               ORDER BY r.created_at DESC""",
            parameters=(user_id,),
            fetchall=True
        )

        referrals = []
        for row in results:
            referrals.append({
                'telegram_id': row[0],
                'username': row[1],
                'full_name': row[2],
                'status': row[3],
                'bonus_given': row[4] or 0,
                'created_at': row[5],
                'converted_at': row[6]
            })
        return referrals

    def get_referral_stats(self, telegram_id: int) -> Dict:
        """Foydalanuvchi referal statistikasi"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return {
                'total_referrals': 0,
                'registered': 0,
                'paid': 0,
                'total_bonus': 0,
                'referral_code': None
            }

        # Umumiy statistika
        result = self.execute(
            """SELECT 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'registered' THEN 1 ELSE 0 END) as registered,
                   SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid,
                   COALESCE(SUM(bonus_given), 0) as total_bonus
               FROM Referrals
               WHERE referrer_id = ?""",
            parameters=(user_id,),
            fetchone=True
        )

        # Referal kodini olish
        code = self.get_referral_code(telegram_id)

        return {
            'total_referrals': result[0] or 0,
            'registered': result[1] or 0,
            'paid': result[2] or 0,
            'total_bonus': result[3] or 0,
            'referral_code': code
        }

    def get_top_referrers(self, limit: int = 10) -> List[Dict]:
        """Eng ko'p taklif qilganlar reytingi"""
        results = self.execute(
            """SELECT u.telegram_id, u.username, u.full_name, 
                      COALESCE(u.referral_count, 0) as ref_count,
                      COALESCE(SUM(r.bonus_given), 0) as total_bonus
               FROM Users u
               LEFT JOIN Referrals r ON u.id = r.referrer_id
               WHERE COALESCE(u.referral_count, 0) > 0
               GROUP BY u.id
               ORDER BY ref_count DESC, total_bonus DESC
               LIMIT ?""",
            parameters=(limit,),
            fetchall=True
        )

        referrers = []
        for i, row in enumerate(results, 1):
            referrers.append({
                'rank': i,
                'telegram_id': row[0],
                'username': row[1],
                'full_name': row[2],
                'referral_count': row[3],
                'total_bonus': row[4]
            })
        return referrers


    def get_referrer_info(self, telegram_id: int) -> Optional[Dict]:
        """Foydalanuvchini kim taklif qilganini bilish"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None

        result = self.execute(
            """SELECT u.telegram_id, u.username, u.full_name
               FROM Users u
               JOIN Users referred ON referred.referred_by = u.id
               WHERE referred.id = ?""",
            parameters=(user_id,),
            fetchone=True
        )

        if result:
            return {
                'telegram_id': result[0],
                'username': result[1],
                'full_name': result[2]
            }
        return None

    def check_referral_enabled(self) -> bool:
        """Referal tizimi yoqilganmi"""
        return self.get_setting('referral_enabled', 'true').lower() == 'true'

        # =============================================================
        #           YANGI: ADMIN, RUXSAT VA VAQT METHODLARI
        # =============================================================

    def get_default_duration(self):
            """
            Sozlamalardan standart kurs muddatini oladi (kun).
            Agar belgilanmagan bo'lsa, avtomat 90 kun qaytaradi.
            """
            try:
                res = self.execute("SELECT value FROM Settings WHERE key = 'default_duration'", fetchone=True)
                return int(res[0]) if res else 90
            except:
                return 90

    def set_default_duration(self, days):
            """Admin panel orqali standart muddatni o'zgartirish"""
            self.execute(
                "INSERT OR REPLACE INTO Settings (key, value, description) VALUES ('default_duration', ?, 'Standart kurs muddati')",
                (str(days),), commit=True
            )

    def check_access(self, user_id, course_id):
            """
            Userning kursga kirishga haqqi bormi? (Bloklanmaganmi va Vaqti bormi?)
            True = Kirishi mumkin
            False = Kirishi mumkin emas
            """
            import datetime
            row = self.execute(
                "SELECT expires_at, is_active FROM ManualAccess WHERE user_id=? AND course_id=?",
                (user_id, course_id), fetchone=True
            )

            if not row: return False  # Umuman sotib olmagan

            expires_at_str, is_active = row

            # 1. Bloklangan bo'lsa (is_active=0)
            if not is_active: return False

            # 2. Agar vaqt cheksiz bo'lsa (NULL)
            if not expires_at_str: return True

            # 3. Vaqtni tekshiramiz
            try:
                exp_date = datetime.datetime.strptime(str(expires_at_str)[:19], "%Y-%m-%d %H:%M:%S")
                if datetime.datetime.now() > exp_date:
                    return False  # Vaqt tugagan
            except:
                return False

            return True

    def grant_access(self, user_id, course_id, admin_id, days):
            """
            Userga ruxsat berish (Yangi vaqt hisoblab yozadi).
            Avtomatik 'Tasdiqlash' bosilganda shu ishlaydi.
            """
            import datetime
            # Hozirgi vaqt + N kun
            expires_at = datetime.datetime.now() + datetime.timedelta(days=days)

            self.execute(
                """INSERT OR REPLACE INTO ManualAccess 
                   (user_id, course_id, granted_by, expires_at, is_active)
                   VALUES (?, ?, ?, ?, 1)""",
                (user_id, course_id, admin_id, expires_at), commit=True
            )
            return expires_at

    def block_user(self, user_id, course_id):
            """Userni bloklash (is_active = 0)"""
            self.execute(
                "UPDATE ManualAccess SET is_active=0 WHERE user_id=? AND course_id=?",
                (user_id, course_id), commit=True
            )

    def unblock_user(self, user_id, course_id):
            """Userni blokdan chiqarish (is_active = 1)"""
            self.execute(
                "UPDATE ManualAccess SET is_active=1 WHERE user_id=? AND course_id=?",
                (user_id, course_id), commit=True
            )

    def add_days_to_user(self, user_id, course_id, days):
            """
            Individual userga vaqt qo'shish.
            Agar vaqti tugagan bo'lsa -> Bugundan boshlab qo'shadi.
            Agar vaqti bor bo'lsa -> Bor vaqtini ustiga qo'shadi.
            """
            import datetime
            row = self.execute(
                "SELECT expires_at FROM ManualAccess WHERE user_id=? AND course_id=?",
                (user_id, course_id), fetchone=True
            )

            now = datetime.datetime.now()

            if row and row[0]:
                current_exp = datetime.datetime.strptime(str(row[0])[:19], "%Y-%m-%d %H:%M:%S")
                # Qaysi biri katta bo'lsa o'shandan boshlaymiz (Hozir yoki Tugash vaqti)
                start_time = max(now, current_exp)
            else:
                start_time = now

            new_expire = start_time + datetime.timedelta(days=days)

            self.execute(
                "UPDATE ManualAccess SET expires_at=?, is_active=1 WHERE user_id=? AND course_id=?",
                (new_expire, user_id, course_id), commit=True
            )
            return new_expire

    def delete_access(self, user_id, course_id):
            """User ruxsatini butunlay o'chirib tashlash"""
            self.execute(
                "DELETE FROM ManualAccess WHERE user_id=? AND course_id=?",
                (user_id, course_id), commit=True
            )

        # --- OMMAVIY (MASS) ACTIONLAR ---

    def count_active_users(self):
            """Nechta aktiv o'quvchi borligini sanash"""
            res = self.execute("SELECT COUNT(*) FROM ManualAccess WHERE is_active=1", fetchone=True)
            return res[0] if res else 0

    def mass_add_time(self, days):
            """
            BARCHA aktiv o'quvchilarga N kun qo'shish.
            Faqat vaqti borlarga (NULL emaslarga) ta'sir qiladi.
            """
            sql = f"UPDATE ManualAccess SET expires_at = datetime(expires_at, '+{days} days') WHERE is_active = 1 AND expires_at IS NOT NULL"
            self.execute(sql, commit=True)



    def reset_all_user_data(self) -> dict:
        """
        Barcha user ma'lumotlarini tozalash (DARSLAR SAQLANADI)
        Faqat super admin ishlatishi mumkin!
        """
        stats = {}

        try:
            # 1. Test natijalari
            result = self.execute("SELECT COUNT(*) FROM TestResults", fetchone=True)
            stats['test_results'] = result[0] if result else 0
            self.execute("DELETE FROM TestResults", commit=True)

            # 2. User progress
            result = self.execute("SELECT COUNT(*) FROM UserProgress", fetchone=True)
            stats['progress'] = result[0] if result else 0
            self.execute("DELETE FROM UserProgress", commit=True)

            # 3. Sertifikatlar
            result = self.execute("SELECT COUNT(*) FROM Certificates", fetchone=True)
            stats['certificates'] = result[0] if result else 0
            self.execute("DELETE FROM Certificates", commit=True)

            # 4. Fikrlar
            result = self.execute("SELECT COUNT(*) FROM Feedbacks", fetchone=True)
            stats['feedbacks'] = result[0] if result else 0
            self.execute("DELETE FROM Feedbacks", commit=True)

            # 5. To'lovlar
            result = self.execute("SELECT COUNT(*) FROM Payments", fetchone=True)
            stats['payments'] = result[0] if result else 0
            self.execute("DELETE FROM Payments", commit=True)

            # 6. Qo'lda dostuplar
            result = self.execute("SELECT COUNT(*) FROM ManualAccess", fetchone=True)
            stats['manual_access'] = result[0] if result else 0
            self.execute("DELETE FROM ManualAccess", commit=True)

            # 7. Referallar
            result = self.execute("SELECT COUNT(*) FROM Referrals", fetchone=True)
            stats['referrals'] = result[0] if result else 0
            self.execute("DELETE FROM Referrals", commit=True)

            # 8. Userlar (adminlardan tashqari)
            result = self.execute(
                "SELECT COUNT(*) FROM Users WHERE id NOT IN (SELECT user_id FROM Admins)",
                fetchone=True
            )
            stats['users'] = result[0] if result else 0
            self.execute(
                "DELETE FROM Users WHERE id NOT IN (SELECT user_id FROM Admins)",
                commit=True
            )

            # 9. Admin userlarning ballarini 0 ga tushirish
            self.execute(
                "UPDATE Users SET total_score = 0, balance = 0, referral_count = 0",
                commit=True
            )

            stats['success'] = True
            return stats

        except Exception as e:
            print(f"❌ Reset xatosi: {e}")
            stats['success'] = False
            stats['error'] = str(e)
            return stats

    def get_test_count(self) -> int:
        """
        Testli darslar soni
        """
        result = self.execute(
            """SELECT COUNT(*) FROM Lessons l
               JOIN Modules m ON l.module_id = m.id
               WHERE l.is_active = 1 AND m.is_active = 1 AND l.has_test = 1""",
            fetchone=True
        )
        return result[0] if result else 1

    def has_completed_test(self, user_id: int, test_id: int) -> bool:
        """
        User bu testdan O'TGANMI? (o'tish balidan yuqori natija bormi?)
        Faqat O'TGAN bo'lsa True qaytaradi
        """
        result = self.execute(
            """SELECT 1 FROM TestResults tr
               JOIN Tests t ON tr.test_id = t.id
               WHERE tr.user_id = ? AND tr.test_id = ? AND tr.score >= t.passing_score
               LIMIT 1""",
            parameters=(user_id, test_id),
            fetchone=True
        )
        return result is not None

    def get_first_test_score(self, user_id: int, test_id: int) -> float:
        """
        Userning shu testdagi BIRINCHI natijasi
        """
        result = self.execute(
            "SELECT score FROM TestResults WHERE user_id = ? AND test_id = ? ORDER BY id ASC LIMIT 1",
            parameters=(user_id, test_id),
            fetchone=True
        )
        return result[0] if result and result[0] else 0

    def calculate_total_score(self, telegram_id: int) -> float:
        """
        Userning umumiy balini hisoblash (100 ball tizimi)
        """
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return 0

        test_count = self.get_test_count()
        if test_count == 0:
            return 0

        ball_per_test = 100 / test_count

        results = self.execute(
            """SELECT test_id, score FROM TestResults 
               WHERE user_id = ? 
               AND id IN (
                   SELECT MIN(id) FROM TestResults 
                   WHERE user_id = ? 
                   GROUP BY test_id
               )""",
            parameters=(user_id, user_id),
            fetchall=True
        )

        if not results:
            return 0

        total = 0
        for test_id, score in results:
            total += (score / 100) * ball_per_test

        return round(total, 1)

    def update_user_total_score(self, telegram_id: int) -> float:
        """
        Userning umumiy balini qayta hisoblash va saqlash
        """
        new_score = self.calculate_total_score(telegram_id)

        self.execute(
            "UPDATE Users SET total_score = ? WHERE telegram_id = ?",
            parameters=(new_score, telegram_id),
            commit=True
        )

        return new_score

    # ============================================================
    #                    DOSTUPNI TO'LIQ YOPISH (YANGI)
    # ============================================================

    def revoke_full_access(self, telegram_id: int, course_id: int) -> bool:
        """
        Dostupni TO'LIQ yopish:
        1. ManualAccess yopiladi
        2. Payments revoked bo'ladi
        3. UserProgress locked bo'ladi
        """
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return False

        try:
            # 1. ManualAccess ni yopish
            self.execute(
                "UPDATE ManualAccess SET is_active = FALSE WHERE user_id = ? AND course_id = ?",
                parameters=(user_id, course_id),
                commit=True
            )

            # 2. Payments ni ham yopish (agar bor bo'lsa)
            self.execute(
                "UPDATE Payments SET status = 'revoked' WHERE user_id = ? AND course_id = ? AND status = 'approved'",
                parameters=(user_id, course_id),
                commit=True
            )

            # 3. UserProgress dagi darslarni yopish (locked qilish)
            self.execute(
                """UPDATE UserProgress SET status = 'locked' 
                   WHERE user_id = ? AND lesson_id IN (
                       SELECT l.id FROM Lessons l
                       JOIN Modules m ON l.module_id = m.id
                       WHERE m.course_id = ?
                   )""",
                parameters=(user_id, course_id),
                commit=True
            )

            return True

        except Exception as e:
            print(f"❌ Dostup yopishda xato: {e}")
            return False
