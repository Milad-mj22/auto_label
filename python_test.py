"""
اسکریپت تست اتصال به OpenAI API
اجرا: python test_openai.py
"""
import os
import base64
import json
import mimetypes
import requests
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

API_KEY = ""
MODEL =  "deepseek-ai/DeepSeek-V4.1-Flash-1017"
BASE_URL ="https://inference.baseten.co/v1"


def print_separator(title):
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def test_text_completion():
    """تست ساده متن (بدون تصویر) برای بررسی اتصال"""
    print_separator("تست ۱: اتصال متنی ساده")
    
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "فقط کلمه 'سلام' را بنویس."}
        ],
        "max_tokens": 20,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        print(f"📍 آدرس: {url}")
        print(f"📦 مدل: {MODEL}")
        print(f"🔑 کلید: {API_KEY[:15]}...")
        print("⏳ در حال ارسال درخواست...")
        
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"\n📡 کد وضعیت: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ موفق! پاسخ مدل: {content.strip()}")
            return True
        else:
            print(f"❌ خطا!")
            print(f"📄 پاسخ سرور: {r.text[:500]}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ خطای شبکه: {e}")
        return False


def test_vision_with_generated_image():
    """تست تحلیل تصویر با یک تصویر تستی ساده (تولید شده در حافظه)"""
    print_separator("تست ۲: تحلیل تصویر (Vision)")
    
    # ساخت یک تصویر ساده ۱۰۰x۱۰۰ با رنگ قرمز
    try:
        from PIL import Image
        import io
        
        img = Image.new("RGB", (100, 100), color=(200, 50, 50))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        print("✅ تصویر تستی تولید شد (100x100 قرمز)")
    except ImportError:
        print("❌ Pillow نصب نیست. نصب: pip install Pillow")
        return False
    
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "این تصویر چه رنگی است؟ فقط یک کلمه پاسخ بده."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ],
            }
        ],
        "max_tokens": 50,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        print("⏳ در حال ارسال درخواست Vision...")
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"\n📡 کد وضعیت: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ موفق! پاسخ مدل: {content.strip()}")
            return True
        else:
            print(f"❌ خطا!")
            print(f"📄 پاسخ سرور: {r.text[:500]}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ خطای شبکه: {e}")
        return False


def main():
    print_separator("بررسی تنظیمات")
    print(f"OPENAI_API_KEY: {'✅ تنظیم شده' if API_KEY else '❌ تنظیم نشده'}")
    print(f"OPENAI_MODEL: {MODEL}")
    print(f"OPENAI_BASE_URL: {BASE_URL}")
    
    # بررسی پروکسی
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    print(f"HTTP_PROXY: {http_proxy or 'تنظیم نشده'}")
    print(f"HTTPS_PROXY: {https_proxy or 'تنظیم نشده'}")
    
    if not API_KEY:
        print("\n❌ کلید API تنظیم نشده است. فایل .env را بررسی کنید.")
        return
    
    # اجرای تست‌ها
    result1 = test_text_completion()
    result2 = test_vision_with_generated_image()
    
    # خلاصه
    print_separator("خلاصه نتایج")
    print(f"تست متنی: {'✅ موفق' if result1 else '❌ ناموفق'}")
    print(f"تست تصویری: {'✅ موفق' if result2 else '❌ ناموفق'}")
    
    if not result1 and not result2:
        print("\n💡 نکته: اگر خطای 'unsupported_country_region_territory' دیدید،")
        print("   به دلیل محدودیت جغرافیایی OpenAI است. راه‌حل‌ها:")
        print("   1. استفاده از پروکسی/VPN در سطح سرور")
        print("   2. استفاده از سرویس واسط (Relay) با تغییر OPENAI_BASE_URL")
        print("   3. تغییر به مدل‌های جایگزین (مثل OpenRouter یا مدل‌های لوکال)")


if __name__ == "__main__":
    main()