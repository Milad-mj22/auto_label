

import sys
import os

# تنظیم مسیر پروژه
sys.path.insert(0, '/home/mykaman1/auto_label/passenger_wsgi.py')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

