from PIL import Image
from django.core.exceptions import ValidationError
from apps.settings_app.services import get_max_image_size_mb

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image_file(file) -> None:
    max_bytes = get_max_image_size_mb() * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f"حجم تصویر بیش از {get_max_image_size_mb()} مگابایت است.")
    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
        img = Image.open(file)
        fmt = (img.format or "").upper()
        if fmt not in ALLOWED_FORMATS:
            raise ValidationError("فرمت تصویر پشتیبانی نمی‌شود (JPEG/PNG/WEBP).")
        if img.width < 64 or img.height < 64:
            raise ValidationError("ابعاد تصویر بسیار کوچک است.")
        file.seek(0)
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("فایل تصویر معتبر نیست.")