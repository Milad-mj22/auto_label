# AI Surface Defect Detection

## پیش‌نیاز
- Python 3.11+
- pip

## راه‌اندازی بک‌اند

```bash
cd backend
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env را برای AI_PROVIDER=mock یا openai و SMS_PROVIDER=console تنظیم کنید
python manage.py makemigrations users industries settings_app verification quota image_analysis conversations audit
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
cd frontend
python -m http.server 5500

AI_PROVIDER=mock
SMS_PROVIDER=console