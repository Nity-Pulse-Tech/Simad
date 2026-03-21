import os
import environ
from pathlib import Path

# Setup django environment
import django
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent
env = environ.Env()
environ.Env.read_env(str(BASE_DIR / ".env"))

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()

from simad.users.models import User
from simad.orders.models import Order

def check():
    print(f"DB NAME: {settings.DATABASES['default']['NAME']}")
    print(f"DB USER: {settings.DATABASES['default']['USER']}")
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Orders: {Order.objects.count()}")
    
    target_user = User.objects.filter(phone_number='691327257').first()
    if target_user:
        print(f"Target User found: {target_user.email}")
        user_orders = Order.objects.filter(user=target_user)
        print(f"User Orders: {user_orders.count()}")
        print(f"User Paid Orders: {user_orders.filter(is_paid=True).count()}")
    else:
        print("Target User NOT found")

if __name__ == "__main__":
    check()
