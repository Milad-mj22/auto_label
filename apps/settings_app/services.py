from django.conf import settings
from .models import (
    SystemSetting,
    KEY_MANAGEMENT_PHONE,
    KEY_DEFAULT_IMAGE_QUOTA,
    KEY_DEFAULT_QUESTION_LIMIT,
    KEY_MAX_IMAGE_SIZE_MB,
)


def get_management_phone() -> str:
    return SystemSetting.get(KEY_MANAGEMENT_PHONE, settings.MANAGEMENT_PHONE)


def get_default_image_quota() -> int:
    return SystemSetting.get_int(KEY_DEFAULT_IMAGE_QUOTA, settings.DEFAULT_IMAGE_QUOTA)


def get_default_question_limit() -> int:
    return SystemSetting.get_int(KEY_DEFAULT_QUESTION_LIMIT, settings.DEFAULT_QUESTION_LIMIT)


def get_max_image_size_mb() -> int:
    return SystemSetting.get_int(KEY_MAX_IMAGE_SIZE_MB, settings.MAX_IMAGE_SIZE_MB)