import base64
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class PayUnitService:
    """
    Service class to handle interactions with PayUnit API.
    Docs: https://developer.payunit.net/rest-api/initialize-payment
    """

    def __init__(self):
        self.api_key = getattr(settings, "PAYUNIT_API_KEY", "")
        self.api_user = getattr(settings, "PAYUNIT_USER", "")
        self.api_password = getattr(settings, "PAYUNIT_PASSWORD", "")
        self.mode = getattr(settings, "PAYUNIT_MODE", "test")
        self.base_url = "https://gateway.payunit.net"
        
        # Prepare Basic Auth header
        auth_str = f"{self.api_user}:{self.api_password}"
        self.auth_header = base64.b64encode(auth_str.encode()).decode()

    def initialize_payment(self, total_amount, transaction_id, return_url, notify_url, currency="XAF", country="CM"):
        """
        Initializes a transaction on PayUnit.
        """
        endpoint = f"{self.base_url}/api/gateway/initialize" # Removed trailing slash
        
        # CloudFront (AWS WAF) blocks 127.0.0.1 and localhost in payloads.
        # We replace them with a placeholder or the public domain if configured.
        # Note: Browsers will need to be redirected back to the correct local URL manually 
        # or via a host file entry if testing locally, but initialization will at least succeed.
        site_url = getattr(settings, "SITE_URL", "https://simad.cm")
        
        def sanitize_url(url):
            if not url:
                return url
            if "127.0.0.1" in url or "localhost" in url:
                logger.warning("Replacing local address in URL %s to bypass PayUnit WAF", url)
                return url.replace("127.0.0.1", "simad.cm").replace("localhost", "simad.cm")
            return url

        sanitized_return_url = sanitize_url(return_url)
        sanitized_notify_url = sanitize_url(notify_url)

        headers = {
            "x-api-key": self.api_key,
            "mode": self.mode,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        payload = {
            "total_amount": int(float(total_amount)),
            "currency": currency,
            "transaction_id": transaction_id,
            "return_url": sanitized_return_url,
            "notify_url": sanitized_notify_url,
            "payment_country": country
        }
        
        logger.info("Initializing PayUnit payment: %s", payload)
        
        try:
            response = requests.post(
                endpoint, 
                json=payload, 
                headers=headers, 
                auth=(self.api_user, self.api_password),
                timeout=60 # Increased timeout
            )
            
            if response.status_code == 403:
                logger.error("❌ PayUnit 403 Forbidden. Headers: %s", response.headers)
                try:
                    error_data = response.json()
                    logger.error("❌ PayUnit Response Body: %s", error_data)
                except Exception:
                    logger.error("❌ PayUnit Response Body: %s", response.text)
                return {"success": False, "message": "Authentication failed or request blocked by WAF"}
                
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "SUCCESS":
                logger.info("✅ PayUnit Success: Transaction created! URL: %s", data["data"]["transaction_url"])
                return {
                    "success": True,
                    "transaction_url": data["data"]["transaction_url"],
                    "t_id": data["data"]["t_id"],
                    "data": data
                }
            else:
                logger.error("❌ PayUnit Error: %s", data.get("message"))
                return {"success": False, "message": data.get("message"), "data": data}
                
        except requests.exceptions.Timeout:
            logger.error("❌ PayUnit Timeout Error (60s)")
            return {"success": False, "message": "PayUnit server timed out. Please try again."}
        except requests.exceptions.RequestException as e:
            logger.error("❌ PayUnit Connection Error: %s", str(e))
            return {"success": False, "message": str(e)}

    def make_direct_payment(self, total_amount, transaction_id, phone_number, payment_network, notify_url, return_url=None, currency="XAF", country="CM"):
        """
        Triggers a direct payment (USSD Push) on PayUnit.
        """
        endpoint = f"{self.base_url}/api/gateway/makepayment"
        
        # Sanitize URLs for WAF
        def sanitize_url(url):
            if not url:
                return url
            if "127.0.0.1" in url or "localhost" in url:
                logger.warning("Replacing local address in URL %s to bypass PayUnit WAF", url)
                # Replace along with port if present
                import re
                url = re.sub(r'127\.0\.0\.1(:\d+)?', 'simad.cm', url)
                url = re.sub(r'localhost(:\d+)?', 'simad.cm', url)
                return url
            return url

        sanitized_notify_url = sanitize_url(notify_url)
        # return_url is required by the API even for direct payments
        sanitized_return_url = sanitize_url(return_url or "https://simad.cm/checkout/success/")

        headers = {
            "x-api-key": self.api_key,
            "mode": self.mode,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # PayUnit Direct Pay field names can be tricky. Trying lowercase underscore names.
        gateway = "mtn_momo" if payment_network.upper() == "MTN" else "orange_money"
        payment_type_val = "button" 
        
        # Ensure phone number is exactly 9 digits for Cameroon (unprefixed)
        clean_phone = str(phone_number).replace(" ", "").replace("+", "")
        if clean_phone.startswith("237") and len(clean_phone) > 9:
            clean_phone = clean_phone[3:]
            
        payload = {
            "amount": int(float(total_amount)),
            "currency": currency,
            "transaction_id": str(transaction_id),
            "phone_number": clean_phone,
            "gateway": gateway,
            "paymentType": "button",
            "notify_url": sanitized_notify_url.replace("http://", "https://"),
            "return_url": sanitized_return_url.replace("http://", "https://"),
        }
        
        logger.info("Triggering PayUnit Direct Payment (JSON/HTTPS): %s", payload)
        
        try:
            response = requests.post(
                endpoint, 
                json=payload, 
                headers=headers, 
                auth=(self.api_user, self.api_password),
                timeout=60
            )
            
            if response.status_code == 403:
                logger.error("❌ PayUnit 403 Forbidden on Direct Pay. Headers: %s", response.headers)
                return {"success": False, "message": "Request blocked by WAF"}
            
            if response.status_code == 400:
                logger.error("❌ PayUnit 400 Bad Request. Body: %s", response.text)
                return {"success": False, "message": f"Bad Request: {response.text}"}
                
            response.raise_for_status()
            data = response.json()
            
            # If successful, it triggers USSD Push. Status is usually 'SUCCESS'
            if data.get("status") == "SUCCESS":
                logger.info("✅ PayUnit Direct Pay Success: USSD Push triggered for %s", phone_number)
                return {
                    "success": True,
                    "message": "Payment prompt sent to your phone. Please confirm to complete transaction.",
                    "data": data
                }
            else:
                logger.error("❌ PayUnit Direct Pay Error: %s", data.get("message"))
                return {"success": False, "message": data.get("message"), "data": data}
                
        except requests.exceptions.Timeout:
            logger.error("❌ PayUnit Direct Pay Timeout (60s)")
            return {"success": False, "message": "PayUnit server timed out. Please try again."}
        except requests.exceptions.RequestException as e:
            logger.error("❌ PayUnit Direct Pay Connection Error: %s", str(e))
            return {"success": False, "message": str(e)}

    def verify_payment(self, t_id):
        """
        Optional: Verify a payment status using t_id if needed.
        PayUnit usually sends webhooks, but this can be useful for polling or manual checks.
        """
        # Note: Polling endpoint might be different, 
        # but the main integration flow uses return_url and notify_url.
        pass

import stripe

class StripeService:
    """
    Service class to handle interactions with Stripe API.
    """

    def __init__(self):
        self.secret_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        stripe.api_key = self.secret_key

    def create_payment_intent(self, amount, currency="xaf", metadata=None):
        """
        Creates a Stripe PaymentIntent.
        Amount should be in the smallest unit of the currency (e.g., cents for USD, subunits for XAF).
        Note: Stripe supports XAF, but it's a zero-decimal currency.
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "intent_id": intent.id,
                "data": intent
            }
        except stripe.error.StripeError as e:
            logger.error("❌ Stripe Error: %s", str(e))
            return {"success": False, "message": str(e)}

    def construct_event(self, payload, sig_header):
        """
        Verifies and constructs a Stripe event from a webhook payload.
        """
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return {"success": True, "event": event}
        except ValueError as e:
            # Invalid payload
            logger.error("❌ Stripe Webhook Error: Invalid payload - %s", str(e))
            return {"success": False, "message": "Invalid payload"}
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error("❌ Stripe Webhook Error: Invalid signature - %s", str(e))
            return {"success": False, "message": "Invalid signature"}
