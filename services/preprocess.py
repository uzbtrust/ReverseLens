from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path


def preprocess(filepath, size=512):
    img = Image.open(filepath).convert("RGB")

    # resize
    img = img.resize((size, size), Image.LANCZOS)

    # sharpen - rasm aniqroq bo'ladi qidiruv uchun
    img = img.filter(ImageFilter.SHARPEN)

    # contrast biroz oshiramiz
    img = ImageEnhance.Contrast(img).enhance(1.15)

    # brightness normalize
    img = ImageEnhance.Brightness(img).enhance(1.05)

    img.save(filepath, "JPEG", quality=92)
    return filepath


def get_img_info(filepath):
    img = Image.open(filepath)
    return {
        "size": img.size,
        "mode": img.mode,
        "format": img.format or "unknown",
    }
