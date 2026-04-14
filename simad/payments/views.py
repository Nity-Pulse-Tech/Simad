import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from simad.orders.models import Payment, Order
from simad.global_data.enum import PaymentStatusChoices, OrderStatusChoices
from django.utils import timezone

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class PayUnitWebhookView(View):
    """
    Handles notifications from PayUnit.
    """
    def post(self, request, *args, **kwargs):
        logger.info("Received PayUnit Webhook Notification")
        
        try:
            data = json.loads(request.body)
            logger.debug("Webhook Data: %s", data)
            
            # PayUnit notification payload fields (assuming based on common patterns)
            # You might need to adjust these based on actual PayUnit behavior
            transaction_id = data.get('transaction_id')
            status = data.get('status') # Usually 'SUCCESS' or 'FAILED'
            
            if not transaction_id:
                logger.error("No transaction_id in PayUnit webhook")
                return JsonResponse({"status": "error", "message": "No transaction_id"}, status=400)
                
            try:
                payment = Payment.objects.get(reference=transaction_id)
                
                if status == 'SUCCESS':
                    payment.status = PaymentStatusChoices.COMPLETED
                    payment.paid_at = timezone.now()
                    payment.gateway_response = data
                    payment.save()
                    
                    # Update Order status
                    order = payment.order
                    order.is_paid = True
                    # order.status = OrderStatusChoices.CONFIRMED # Or PROCESSING
                    order.save()
                    
                    logger.info("Payment %s marked as SUCCESS via Webhook", transaction_id)
                elif status == 'FAILED':
                    payment.status = PaymentStatusChoices.FAILED
                    payment.gateway_response = data
                    payment.save()
                    logger.warning("Payment %s marked as FAILED via Webhook", transaction_id)
                    
                return JsonResponse({"status": "ok"})
                
            except Payment.DoesNotExist:
                logger.error("Payment with reference %s not found for webhook", transaction_id)
                return JsonResponse({"status": "error", "message": "Payment not found"}, status=404)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in PayUnit webhook")
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.exception("Error processing PayUnit webhook")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
