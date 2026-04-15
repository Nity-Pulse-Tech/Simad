import os
import django
import sys

# Setup Django environment
sys.path.append("/home/mark-dilan/Documents/PROJECT/Simad")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from simad.payments.services import PayUnitService

def test_payunit_direct():
    svc = PayUnitService()
    print("Testing PayUnit Direct Payment (USSD Push) with real-ish number...")
    
    # Using the number from the user's log
    res = svc.make_direct_payment(
        total_amount=100,
        transaction_id="VERIFY-TEST-REAL-1",
        phone_number="652080685",
        payment_network="MTN",
        notify_url="https://127.0.0.1:8002/payments/payunit/webhook/",
        return_url="http://127.0.0.1:8002/checkout/success/",
        currency="XAF"
    )
    
    if res['success']:
        print("✅ SUCCESS: PayUnit direct payment call worked!")
        print(f"Message: {res['message']}")
    else:
        print(f"❌ FAILED: {res['message']}")
        if 'data' in res:
            print(f"Data: {res['data']}")

if __name__ == "__main__":
    test_payunit_direct()
