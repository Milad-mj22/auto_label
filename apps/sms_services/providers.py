import logging
import requests
from django.conf import settings
from sms_ir import SmsIr #pip install smsir-python

from apps.sms_services.models import OTPVar_Enum, SMS_Template, SMSServiceName_Enum, SMSServiceTemplate_Enum
from .base import SmsService

logger = logging.getLogger(__name__)


class ConsoleSmsService(SmsService):
    """پیاده‌سازی پیش‌فرض توسعه: کد را فقط لاگ می‌کند."""
    def send_otp(self, phone: str, code: str) -> None:
        logger.info("[SMS-CONSOLE] OTP for %s: %s", phone, code)


class KavenegarSmsService(SmsService):
    """آداپتور نمونه Kavenegar. کلید از env."""
    def send_otp(self, phone: str, code: str) -> None:
        if not settings.SMS_API_KEY:
            raise RuntimeError("SMS_API_KEY not configured for Kavenegar")
        url = f"{settings.SMS_BASE_URL or 'https://api.kavenegar.com/v1'}/{settings.SMS_API_KEY}/sms/send.json"
        params = {
            "receptor": phone,
            "sender": settings.SMS_SENDER,
            "message": f"کد تأیید سامانه: {code}",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()


class SMS_IR(SmsService):


    def send_otp(self, phone: str, code: str) -> None:
        ret = False
        template_obj = SMS_Template.objects.filter(name =SMSServiceTemplate_Enum.OTP ).first()
        vars = {OTPVar_Enum.OTP_CODE:code}
        if template_obj.service.sms_panel  == SMSServiceName_Enum.SMS_IR:
            ret = sms_ir(template_obj,phone,vars)

        return ret



def sms_ir(template_obj:SMS_Template,phone_number,vars):

    api_key = template_obj.service.api_key
    linenumber = template_obj.service.line_number
    template_id = template_obj.template_id
    print('vars: ',vars)
    parameters = []
    for key,value in vars.items():
        parms = {"name":key,"value":value}
        parameters.append(parms)



    sms_ir = SmsIr(api_key,linenumber,)
    ret = sms_ir.send_verify_code(phone_number,template_id,parameters,)
    return ret.ok


def get_sms_service() -> SmsService:
    provider = (settings.SMS_PROVIDER or "console").lower()
    if provider == "kavenegar":
        return KavenegarSmsService()
    if provider == "sms_ir":
        return SMS_IR()
    return ConsoleSmsService()