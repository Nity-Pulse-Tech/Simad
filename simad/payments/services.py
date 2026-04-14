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

    def verify_payment(self, t_id):
        """
        Optional: Verify a payment status using t_id if needed.
        PayUnit usually sends webhooks, but this can be useful for polling or manual checks.
        """
        # Note: Polling endpoint might be different, 
        # but the main integration flow uses return_url and notify_url.
        pass
