"""
User Handlers
=============
Foydalanuvchi uchun barcha handlerlar

Tartib: kichik handlerlar yuqorida, katta (muhim) handlerlar pastda
"""

# Kichik/yordamchi handlerlar

# from . import channel_subscription    # Kanal obuna

# O'rtacha handlerlar


from . import tests                   # Test yechish

# Katta/asosiy handlerlar
from . import lessons                 # Darslar
from . import courses                 # Kurslar, sotib olish

# Eng muhim - asosiy handler
from . import start                   # /start, ro'yxatdan o'tish, bosh menyu