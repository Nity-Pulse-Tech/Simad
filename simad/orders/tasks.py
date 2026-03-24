import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from config.celery_app import app
from simad.orders.models import Order
from simad.users.utils import send_whatsapp_order_confirmation

logger = logging.getLogger(__name__)

@app.task(name="simad.orders.send_order_notifications")
def send_order_notifications(order_id):
    """
    Asynchronous task to send order confirmation email and WhatsApp.
    """
    try:
        order = Order.objects.get(id=order_id)
        user = order.user
        
        if not user or not user.email:
            logger.warning(f"No user or email for order {order_id}. Skipping notifications.")
            return False

        # 1. Send Email Confirmation
        context = {
            'order': order,
            'user': user,
            'site_url': getattr(settings, 'SITE_URL', 'https://simad.cm')
        }
        html_message = render_to_string('email/order_created.html', context)
        
        send_mail(
            subject=f"Confirmation de commande - {order.reference}",
            message=f"Merci pour votre commande {order.reference}. Votre total est de {order.total} XOF.",
            from_email=None,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Order confirmation email sent for order {order.reference}")

        # 2. Send WhatsApp Confirmation
        if hasattr(user, 'phone_number') and user.phone_number:
            send_whatsapp_order_confirmation(user, order)
        
        return True

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} does not exist. Notification failed.")
        return False
    except Exception as e:
        logger.exception(f"Error in send_order_notifications: {e}")
        return False
