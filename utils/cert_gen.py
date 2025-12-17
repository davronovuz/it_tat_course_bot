import os
import requests
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime


def ensure_font_exists():
    """
    Montserrat-Bold shriftini internetdan yuklab olish.
    """
    folder = "utils/assets/fonts"
    file_path = f"{folder}/font.ttf"

    os.makedirs(folder, exist_ok=True)

    if not os.path.exists(file_path):
        print(f"⏳ Montserrat-Bold shrifti yuklanmoqda...")
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf"
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print("✅ Font muvaffaqiyatli o'rnatildi!")
            else:
                return None
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            return None

    return file_path


def create_certificate(full_name: str, course_name: str, grade: str, cert_code: str):
    """
    Sertifikat chizish (Tuzatilgan koordinatalar bilan)
    """
    font_path = ensure_font_exists()
    template_path = 'utils/assets/basic.jpg'

    try:
        img = Image.open(template_path)
    except:
        return None

    draw = ImageDraw.Draw(img)
    W, H = img.size

    # ------------------------------------------------
    # 1. SHRIFT O'LCHAMLARI (O'ZGARTIRILDI)
    # ------------------------------------------------
    if font_path:
        try:
            # Ism: 110 dan 90 ga KICHRAYTIRILDI
            name_font = ImageFont.truetype(font_path, 90)

            # Sana: 35 ligicha qoldi
            info_font = ImageFont.truetype(font_path, 35)

            # ID: 40 ligicha qoldi
            id_font = ImageFont.truetype(font_path, 40)
        except:
            name_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
            id_font = ImageFont.load_default()
    else:
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        id_font = ImageFont.load_default()

    text_color = (30, 30, 30)
    id_color = (80, 80, 80)

    # ------------------------------------------------
    # 2. ISM-FAMILIYA (O'RTAGA)
    # ------------------------------------------------
    bbox = draw.textbbox((0, 0), full_name, font=name_font)
    text_width = bbox[2] - bbox[0]

    x_name = (W - text_width) / 2

    # Ismni sal pastroqqa tushirdim (45% dan 48% ga)
    # Shunda chiziqqa chiroyli o'tiradi
    y_name = H * 0.48

    draw.text((x_name, y_name), full_name, font=name_font, fill=text_color)

    # ------------------------------------------------
    # 3. SANA (CHAP PASTGA - KOTARILDI)
    # ------------------------------------------------
    date_str = datetime.now().strftime("%d.%m.%Y")

    x_date = W * 0.22
    # Sana chiziqni bosib qolgani uchun TEPAGA ko'tardim
    # (0.68 dan 0.65 ga - raqam qancha kichik bo'lsa, shuncha tepaga chiqadi)
    y_date = H * 0.755

    draw.text((x_date, y_date), date_str, font=info_font, fill=text_color)

    # ------------------------------------------------
    # 4. ID RAQAM (O'NG TEPAGA - TUSHIRILDI)
    # ------------------------------------------------
    bbox_id = draw.textbbox((0, 0), cert_code, font=id_font)
    id_w = bbox_id[2] - bbox_id[0]

    x_id = W - id_w - 80

    # ID shiftdaga tegib turgandi, PASTGA tushirdim
    # (80 px dan 130 px ga)
    y_id = 130

    draw.text((x_id, y_id), cert_code, font=id_font, fill=id_color)

    # ------------------------------------------------
    # SAQLASH
    # ------------------------------------------------
    bio = io.BytesIO()
    bio.name = "certificate.jpg"
    img.save(bio, 'JPEG', quality=95)
    bio.seek(0)

    return bio