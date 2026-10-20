from abc import ABC, abstractmethod


class SmsService(ABC):
    @abstractmethod
    def send_otp(self, phone: str, code: str) -> None:
        ...