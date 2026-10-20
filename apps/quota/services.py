from django.db import transaction
from django.utils import timezone
from apps.users.models import UserIdentity
from apps.settings_app.services import get_default_image_quota
from apps.audit.models import log_action, AuditLog
from .models import UsageQuota


class QuotaError(Exception):
    pass


def get_or_create_quota(identity: UserIdentity) -> UsageQuota:
    quota, _ = UsageQuota.objects.get_or_create(
        identity=identity,
        defaults={"total_quota": get_default_image_quota()},
    )
    return quota


def reserve_quota(identity: UserIdentity) -> UsageQuota:
    """
    رزرو اتمیک یک واحد سهمیه. با transaction + select_for_update از دور زدن
    هم‌زمان درخواست‌ها جلوگیری می‌کند.
    """
    with transaction.atomic():
        quota = (
            UsageQuota.objects
            .select_for_update()
            .filter(identity=identity)
            .first()
        )
        if quota is None:
            quota = UsageQuota.objects.create(
                identity=identity,
                total_quota=get_default_image_quota(),
            )
            # چون تازه ساختیم، قفل روی آن اثر ندارد؛ از همین نمونه استفاده می‌کنیم.
        else:
            quota.refresh_from_db()

        if quota.is_blocked:
            raise QuotaError("دسترسی این شماره مسدود شده است. با مدیریت تماس بگیرید.")
        if quota.remaining <= 0:
            raise QuotaError(
                "سهمیه پنج تصویر آزمایشی شما تکمیل شده است. "
                "برای ادامه با واحد فروش یا مدیریت تماس بگیرید."
            )
        quota.reserved_count += 1
        if not quota.first_use_at:
            quota.first_use_at = timezone.now()
        quota.last_use_at = timezone.now()
        quota.save(update_fields=["reserved_count", "first_use_at", "last_use_at", "updated_at"])
        return quota


def commit_quota(identity: UserIdentity, success: bool) -> UsageQuota:
    """پس از پایان پردازش: در موفقیت → used++; در شکست → آزادسازی رزرو."""
    with transaction.atomic():
        quota = UsageQuota.objects.select_for_update().get(identity=identity)
        if success:
            if quota.reserved_count > 0:
                quota.reserved_count -= 1
            quota.used_count = min(quota.total_quota, quota.used_count + 1)
        else:
            if quota.reserved_count > 0:
                quota.reserved_count -= 1
        quota.last_use_at = timezone.now()
        quota.save(update_fields=["reserved_count", "used_count", "last_use_at", "updated_at"])
        return quota


def admin_adjust_quota(identity: UserIdentity, new_total: int = None, reset_used: bool = False,
                       block: bool = None, actor=None, reason: str = "") -> UsageQuota:
    with transaction.atomic():
        quota = UsageQuota.objects.select_for_update().get(identity=identity)
        before = {
            "total": quota.total_quota,
            "used": quota.used_count,
            "blocked": quota.is_blocked,
        }
        if new_total is not None:
            if new_total < quota.used_count:
                raise QuotaError("سهمیه جدید نمی‌تواند از تعداد مصرف‌شده کمتر باشد.")
            quota.total_quota = new_total
        if reset_used:
            quota.used_count = 0
        if block is not None:
            quota.is_blocked = block
        quota.save()
        after = {
            "total": quota.total_quota,
            "used": quota.used_count,
            "blocked": quota.is_blocked,
        }
        action = AuditLog.Action.SETTING_CHANGE
        if block is True:
            action = AuditLog.Action.ACCESS_BLOCK
        elif block is False:
            action = AuditLog.Action.ACCESS_UNBLOCK
        elif reset_used:
            action = AuditLog.Action.QUOTA_RESET
        elif new_total is not None:
            action = AuditLog.Action.QUOTA_INCREASE
        log_action(
            actor=actor, action=action,
            target_type="UsageQuota", target_id=quota.pk,
            detail={"phone": identity.phone, "before": before, "after": after, "reason": reason},
        )
        return quota