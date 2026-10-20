from django.test import TestCase

# Create your tests here.
import threading
import pytest
from django.db import connection, connections
from django.test.utils import setup_test_environment, teardown_test_environment

from apps.users.models import UserIdentity
from apps.users.utils import normalize_phone
from apps.quota.services import reserve_quota, commit_quota, get_or_create_quota, QuotaError
from apps.quota.models import UsageQuota


@pytest.mark.django_db
def test_normalize_phone_variants():
    assert normalize_phone("+989121234567") == "09121234567"
    assert normalize_phone("989121234567") == "09121234567"
    assert normalize_phone("0912 123 4567") == "09121234567"
    assert normalize_phone("00989121234567") == "09121234567"
    with pytest.raises(ValueError):
        normalize_phone("12345")


@pytest.mark.django_db
def test_reserve_and_commit_success():
    identity = UserIdentity.objects.create(phone="09120000001", is_verified=True)
    get_or_create_quota(identity)
    for _ in range(5):
        reserve_quota(identity)
        commit_quota(identity, success=True)
    q = UsageQuota.objects.get(identity=identity)
    assert q.used_count == 5
    assert q.remaining == 0
    with pytest.raises(QuotaError):
        reserve_quota(identity)


@pytest.mark.django_db
def test_reserve_release_on_failure():
    identity = UserIdentity.objects.create(phone="09120000002", is_verified=True)
    get_or_create_quota(identity)
    reserve_quota(identity)
    commit_quota(identity, success=False)
    q = UsageQuota.objects.get(identity=identity)
    assert q.used_count == 0
    assert q.remaining == 5


@pytest.mark.django_db(transaction=True)
def test_concurrent_reserves_do_not_exceed_limit():
    identity = UserIdentity.objects.create(phone="09120000003", is_verified=True)
    get_or_create_quota(identity)

    errors = []
    successes = []
    lock = threading.Lock()

    def worker():
        try:
            reserve_quota(identity)
            with lock:
                successes.append(1)
        except QuotaError as e:
            with lock:
                errors.append(str(e))
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # در تنظیمات sqlite، select_for_update پشتیبانی محدودی دارد.
    # حداکثر ۵ موفقیت مجاز است (ممکن است خطای قفل هم رخ دهد که در errors ثبت می‌شود).
    assert len(successes) <= 5