from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import os


def create_certificate(full_name: str, course_name: str, grade: str, cert_code: str):
    """
    Sertifikat chizish (Manual Font bilan)
    """
    # 1. Shablon va Font manzili
    template_path = 'utils/assets/basic.jpg'
    font_path = 'utils/assets/fonts/font.ttf'  # <--- SIZ YUKLAGAN FAYL

    try:
        img = Image.open(template_path)
    except:
        print("❌ Shablon topilmadi!")
        return None

    draw = ImageDraw.Draw(img)
    W, H = img.size

    # ------------------------------------------------
    # 2. SHRIFTLARNI YUKLASH (KATTA O'LCHAMDA)
    # ------------------------------------------------
    try:
        # Ism uchun juda katta shrift (110 px)
        name_font = ImageFont.truetype(font_path, 110)

        # ID va Sana uchun o'rtacha (35 px)
        info_font = ImageFont.truetype(font_path, 35)

        # ID raqam uchun sal kattaroq (40 px)
        id_font = ImageFont.truetype(font_path, 40)
    except Exception as e:
        print(f"❌ Font xatosi: {e}")
        # Agar font fayli topilmasa, majburan default (lekin bu kichkina bo'ladi)
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        id_font = ImageFont.load_default()

    # Ranglar
    # "Aminov Azamat" rasmidagidek to'q kulrang/qora rang
    text_color = (40, 40, 40)
    id_color = (100, 100, 100)  # ID sal ochroq

    # ------------------------------------------------
    # 3. ISM-FAMILIYA (O'RTAGA, KATTA)
    # ------------------------------------------------
    # Ismni o'lchaymiz
    bbox = draw.textbbox((0, 0), full_name, font=name_font)
    text_width = bbox[2] - bbox[0]

    # X: Qoqq o'rta
    x_name = (W - text_width) / 2

    # Y: "Aminov Azamat" sertifikatida ism biroz teparoqda turibdi
    # Taxminan balandlikning 42-45% qismida
    y_name = H * 0.45

    draw.text((x_name, y_name), full_name, font=name_font, fill=text_color)

    # ------------------------------------------------
    # 4. SANA (CHAP PASTGA)
    # ------------------------------------------------
    date_str = datetime.now().strftime("%d.%m.%Y")

    # Chap tomondan: 22% surilgan (Date chizig'i ustiga)
    # Pastdan: 72% joyda
    x_date = W * 0.22
    y_date = H * 0.68  # Sana chizig'ining ustiga tushishi kerak

    draw.text((x_date, y_date), date_str, font=info_font, fill=text_color)

    # ------------------------------------------------
    # 5. ID RAQAM (O'NG TEPAGA)
    # ------------------------------------------------
    # Format: #0112345678

    # ID ni o'lchaymiz
    bbox_id = draw.textbbox((0, 0), cert_code, font=id_font)
    id_w = bbox_id[2] - bbox_id[0]

    # O'ng tomondan 80px ichkarida
    x_id = W - id_w - 80
    # Tepadan 80px pastda
    y_id = 80

    draw.text((x_id, y_id), cert_code, font=id_font, fill=id_color)

    # ------------------------------------------------
    # SAQLASH
    # ------------------------------------------------
    bio = io.BytesIO()
    bio.name = "certificate.jpg"
    img.save(bio, 'JPEG', quality=95)
    bio.seek(0)

    return bio