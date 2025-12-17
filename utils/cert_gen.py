import os
import requests
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime


# --- YORDAMCHI FUNKSIYA: Font yuklash ---
def download_font(url, save_path):
    """Internetdan font faylini yuklab olish"""
    if not os.path.exists(save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        print(f"⏳ Font yuklanmoqda: {save_path}...")
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print("✅ Font muvaffaqiyatli yuklandi!")
                return True
            else:
                print(f"❌ Font yuklashda xato. Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Font yuklashda xatolik: {e}")
            return False
    return True


# ----------------------------------------

def create_certificate(full_name: str, course_name: str, grade: str, cert_code: str):
    """
    Sertifikat rasmini yaratish (Yangi Roboto shrifti bilan)
    """

    # 1. SHABLONNI TANLASH
    base_path = "utils/assets"
    # Shablon nomlari sizda qanday bo'lsa shunday qoldiring
    template_path = f'{base_path}/basic.jpg'  # Hozircha hammasiga basic ishlatamiz

    try:
        img = Image.open(template_path)
    except FileNotFoundError:
        print(f"❌ Xatolik: {template_path} topilmadi!")
        return None

    draw = ImageDraw.Draw(img)
    W, H = img.size

    # ---------------------------------------------------------
    # 2. YANGI SHRIFTLARNI SOZLASH (Roboto)
    # ---------------------------------------------------------
    # Google Fonts havolalari (ishonchli manba)
    FONT_BOLD_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    FONT_REGULAR_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"

    # Saqlash manzillari
    font_bold_path = f"{base_path}/fonts/Roboto-Bold.ttf"
    font_reg_path = f"{base_path}/fonts/Roboto-Regular.ttf"

    # Fontlarni yuklashga harakat qilamiz
    has_bold = download_font(FONT_BOLD_URL, font_bold_path)
    has_reg = download_font(FONT_REGULAR_URL, font_reg_path)

    try:
        if has_bold and has_reg:
            # Ism uchun QALIN (Bold) shrift. O'lchamini (120) o'zingizga moslab o'zgartiring
            name_font = ImageFont.truetype(font_bold_path, 120)
            # ID va sana uchun ODDIY (Regular) shrift
            info_font = ImageFont.truetype(font_reg_path, 40)
        else:
            raise Exception("Fontlar yuklanmadi")
    except:
        print("⚠️ Fontlar yuklanmadi, tizimning standart shrifti ishlatilmoqda.")
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()

    # Ranglar (RGB)
    black_color = (0, 0, 0)
    id_color = (60, 60, 60)  # To'q kulrang

    # ---------------------------------------------------------
    # 3. ISM-FAMILIYANI YOZISH (O'rtaga)
    # ---------------------------------------------------------
    bbox = draw.textbbox((0, 0), full_name, font=name_font)
    text_width = bbox[2] - bbox[0]
    x_name = (W - text_width) / 2
    # Y koordinatasini shablonga qarab o'zgartiring (tepa-pastga surish uchun)
    y_name = (H / 2) - 40

    draw.text((x_name, y_name), full_name, font=name_font, fill=black_color)

    # ---------------------------------------------------------
    # 4. SANA (DATE) YOZISH
    # ---------------------------------------------------------
    date_str = datetime.now().strftime("%d.%m.%Y")
    # Koordinatalarni shabloningizdagi chiziqqa moslang
    x_date = 480
    y_date = H - 475
    draw.text((x_date, y_date), date_str, font=info_font, fill=black_color)

    # ---------------------------------------------------------
    # 5. ID RAQAM (Tepaga, yangi formatda)
    # ---------------------------------------------------------
    # cert_code endi bazadan #01... shaklida keladi
    id_text = cert_code

    bbox_id = draw.textbbox((0, 0), id_text, font=info_font)
    id_width = bbox_id[2] - bbox_id[0]

    # O'ng tomondan joy tashlash
    x_id = W - id_width - 180
    y_id = 160

    draw.text((x_id, y_id), id_text, font=info_font, fill=id_color)

    # ---------------------------------------------------------
    # 6. RASMNI SAQLASH
    # ---------------------------------------------------------
    bio = io.BytesIO()
    bio.name = f"certificate.jpg"
    img.save(bio, 'JPEG', quality=95)
    bio.seek(0)

    return bio