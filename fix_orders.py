import os
import environ
from pathlib import Path
import django
from django.conf import settings

# Setup django
BASE_DIR = Path(__file__).resolve().parent
env = environ.Env()
environ.Env.read_env(str(BASE_DIR / ".env"))

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()

from simad.users.models import User
from simad.orders.models import Order
from simad.global_data.enum import OrderStatusChoices

def fix():
    user = User.objects.filter(phone_number='691327257').first()
    if not user:
        print("User not found")
        return
    
    orders = Order.objects.filter(user=user)
    print(f"Updating {orders.count()} orders for {user.email}")
    
    for i, order in enumerate(orders):
        # Mark every other order as paid and delivered
        if i % 2 == 0:
            order.is_paid = True
            order.status = OrderStatusChoices.DELIVERED
            order.save()
            print(f"Order {order.reference} marked as PAID")
        else:
            order.is_paid = False
            order.save()

    print(f"Done. User now has {Order.objects.filter(user=user, is_paid=True).count()} paid orders.")

if __name__ == "__main__":
    fix()
