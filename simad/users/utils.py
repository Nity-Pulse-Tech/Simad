import requests
import logging
from django.conf import settings
from .models import User

logger = logging.getLogger(__name__)

def send_whatsapp_verification_link(user: User, activation_url):
    """
    Helper to send WhatsApp message using Meta Cloud API.
    Reference Template: 'activated'
    Vars: {{1}} for user name, {{1}} for dynamic URL path
    """
    api_token = getattr(settings, 'WHATSAPP_API_TOKEN', None)
    phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
    template_name = getattr(settings, 'WHATSAPP_TEMPLATE_NAME', 'activated')
    
    if not api_token or not phone_id:
        print(f"WhatsApp API not configured. Activation URL: {activation_url}")
        return False

    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # If the user's template has a fixed example.com, we can only send the dynamic suffix.
    # However, if SITE_URL is configured, we can use it to construct a better path if the template allows.
    # Use the relative path from the activation URL
    # If the URL is https://domain.com/users/activate/TOKEN/, we want 'users/activate/TOKEN/'
    # or just the token depending on how the Meta Template button is configured.
    # Given the 404 logs, the template button likely starts with /activate/ 
    # so we provide the part after that.
    if '/activate/' in activation_url:
        url_path = activation_url.split('/activate/')[-1]
    else:
        url_path = activation_url.split(getattr(settings, 'SITE_URL', ''))[-1].lstrip('/')

    url_path = url_path.replace('%7B%7B1%7D%7D', '').replace('{{1}}', '')
    
    # Log the sending attempt
    logger.info(f"Attempting to send WhatsApp verification to {user.phone_number}. Path: {url_path}")

    data = {
        "messaging_product": "whatsapp",
        "to": user.phone_number if hasattr(user, 'phone_number') else "",
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": user.first_name or "User"}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {"type": "text", "text": url_path}
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"WhatsApp message sent successfully to {user.phone_number}")
            return True
        else:
            logger.error(f"Failed to send WhatsApp message. Status: {response.status_code}. Response: {response.text}")
            return False
    except Exception as e:
        logger.exception(f"Exception occurred while sending WhatsApp message: {e}")
        return False

def send_whatsapp_order_confirmation(user: User, order):
    """
    Helper to send order confirmation via WhatsApp.
    Template: 'order_confirmation'
    Vars: {{1}} for name, {{2}} for ref, {{3}} for total
    """
    api_token = getattr(settings, 'WHATSAPP_API_TOKEN', None)
    phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
    
    if not api_token or not phone_id:
        logger.warning(f"WhatsApp API not configured. Order: {order.reference}")
        return False

    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": user.phone_number if hasattr(user, 'phone_number') else "",
        "type": "template",
        "template": {
            "name": "order_confirmation",
            "language": {"code": "fr"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": user.first_name or "Client"},
                        {"type": "text", "text": order.reference},
                        {"type": "text", "text": f"{order.total} XOF"}
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            logger.info(f"WhatsApp order confirmation sent to {user.phone_number}")
            return True
        else:
            logger.error(f"Failed to send WhatsApp order message. Status: {response.status_code}. Response: {response.text}")
            return False
    except Exception as e:
        logger.exception(f"Exception occurred while sending WhatsApp order message: {e}")
        return False
