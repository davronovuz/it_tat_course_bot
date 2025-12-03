"""
Admin Handlers
==============
Admin panel uchun barcha handlerlar

Tartib: kichik handlerlar yuqorida, katta (muhim) handlerlar pastda
"""

# Kichik/yordamchi handlerlar
from . import admin_broadcast      # Ommaviy xabar
from . import admin_feedbacks      # Fikrlar
from . import admin_settings       # Sozlamalar
from . import admin_reports        # Hisobotlar

# O'rtacha handlerlar
from . import admin_users          # Foydalanuvchilar
from . import admin_payments       # To'lovlar
from . import admin_materials      # Materiallar
from . import admin_tests          # Testlar

# Katta/asosiy handlerlar
from . import admin_lessons        # Darslar
from . import admin_modules        # Modullar
from . import admin_courses        # Kurslar

# Eng muhim - asosiy handler
from . import admin_start          # Admin kirish, bosh menyu