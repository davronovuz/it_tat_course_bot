import os
import requests
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime


def check_and_download_font(font_path):
    """
    Font fayli borligini tekshiradi, yo'q bo'lsa internetdan yuklaydi.
    Biz "Great Vibes" (chiroyli yozma shrift) ishlatamiz.
    """
    # Papka borligini tekshirish va yaratish
    os.makedirs(os.path.dirname(font_path), exist_ok=True)

    if not os.path.exists(font_path):
        print("⏳ Font topilmadi, internetdan yuklanmoqda...")
        # Great Vibes shrifti (Google Fonts)
        url = "https://github.com/google/fonts/raw/main/ofl/greatvibes/GreatVibes-Regular.ttf"
        # Agar oddiyroq shrift kerak bo'lsa, pastdagini commentdan oling:
        # url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"

        try:
            response = requests.get(url)
            with open(font_path, 'wb') as f:
                f.write(response.content)
            print("✅ Font yuklab olindi!")
        except Exception as e:
            print(f"❌ Font yuklashda xato: {e}")
            return False
    return True


def create_certificate(full_name: str, course_name: str, grade: str, cert_code: str):
    """
    Sertifikat rasmini yaratish.
    """

    # 1. SHABLONNI TANLASH
    # Yo'llarni to'g'riladim (utils/assets/ ichida bo'lishi kerak)
    base_path = "utils/assets"

    template_map = {
        'EXPERT': f'{base_path}/expert.jpg',
        'STANDARD': f'{base_path}/standard.jpg',
        'BASIC': f'{base_path}/basic.jpg',
        'PARTICIPANT': f'{base_path}/basic.jpg'
    }

    # Agar grade noto'g'ri kelsa, BASIC ni olamiz
    template_path = template_map.get(grade, f'{base_path}/basic.jpg')

    try:
        img = Image.open(template_path)
    except FileNotFoundError:
        print(f"❌ Xatolik: {template_path} rasm topilmadi! 'utils/assets' papkasini tekshiring.")
        return None

    draw = ImageDraw.Draw(img)
    W, H = img.size

    # ---------------------------------------------------------
    # 2. SHRIFTLARNI SOZLASH (Avtomatik yuklash bilan)
    # ---------------------------------------------------------
    font_path = "utils/assets/font.ttf"

    # Fontni tekshirish va yuklash
    font_exists = check_and_download_font(font_path)

    try:
        if font_exists:
            # Ism uchun juda katta shrift
            name_font = ImageFont.truetype(font_path, 180)  # Hajmini sal kattalashtirdim
            # ID va Sana uchun o'rtacha shrift
            info_font = ImageFont.truetype(font_path, 50)
        else:
            # Agar internet bo'lmasa, majburiy standart font
            raise Exception("Font file not found")
    except:
        print("⚠️ Font yuklanmadi, standart font ishlatilmoqda (xunukroq ko'rinishi mumkin).")
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()

    # Ranglar (RGB)
    black_color = (0, 0, 0)
    id_color = (80, 80, 80)  # To'q kulrang

    # ---------------------------------------------------------
    # 3. ISM FAMILYANI YOZISH (Qoq o'rtaga)
    # ---------------------------------------------------------
    # Ismning eni va bo'yini o'lchaymiz
    bbox = draw.textbbox((0, 0), full_name, font=name_font)
    text_width = bbox[2] - bbox[0]

    # Koordinata X: (RasmEni - YozuvEni) / 2 = Markaz
    x_name = (W - text_width) / 2

    # Koordinata Y: Rasm markazidan ozgina teparoqqa
    # Shablonga qarab o'zgartirishingiz mumkin: -50, -60 va hokazo
    y_name = (H / 2) - 80

    draw.text((x_name, y_name), full_name, font=name_font, fill=black_color)

    # ---------------------------------------------------------
    # 4. SANA (DATE) YOZISH
    # ---------------------------------------------------------
    date_str = datetime.now().strftime("%d.%m.%Y")

    # Chap tomondan 450px, Pastdan 460px tepada
    x_date = 450
    y_date = H - 460

    draw.text((x_date, y_date), date_str, font=info_font, fill=black_color)

    # ---------------------------------------------------------
    # 5. ID RAQAM (ENG YUQORIGA)
    # ---------------------------------------------------------
    id_text = f"№ {cert_code}"

    # ID uzunligini o'lchaymiz
    bbox_id = draw.textbbox((0, 0), id_text, font=info_font)
    id_width = bbox_id[2] - bbox_id[0]

    # O'ng tomondan 100px ichkarida, Tepadan 100px pastda
    x_id = W - id_width - 150
    y_id = 150

    draw.text((x_id, y_id), id_text, font=info_font, fill=id_color)

    # ---------------------------------------------------------
    # 6. RASMNI SAQLASH (Xotiraga)
    # ---------------------------------------------------------
    bio = io.BytesIO()
    bio.name = f"certificate_{cert_code}.jpg"
    img.save(bio, 'JPEG', quality=95)
    bio.seek(0)

    return bio