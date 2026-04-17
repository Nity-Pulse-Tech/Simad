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
            return JsonResponse({"status": "success"})
        except Exception as e:
            logger.error(f"Error in PayUnitWebhookView: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from simad.payments.services import StripeService
from simad.orders.models import Order, Payment
from simad.global_data.enum import PaymentStatusChoices

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Webhook handler for Stripe events.
    """
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        stripe_service = StripeService()
        result = stripe_service.construct_event(payload, sig_header)
        
        if not result['success']:
            return HttpResponse(status=400)
            
        event = result['event']
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            logger.info(f"✅ Stripe Webhook: PaymentIntent {payment_intent['id']} succeeded")
            
            # Update Payment and Order status
            try:
                # Use metadata to find the payment/order
                payment_ref = payment_intent.get('metadata', {}).get('payment_reference')
                if payment_ref:
                    payment = Payment.objects.get(reference=payment_ref)
                    payment.status = PaymentStatusChoices.COMPLETED
                    payment.gateway_response['webhook_event'] = event['type']
                    payment.save()
                    
                    order = payment.order
                    order.status = "PROCESSING"
                    order.is_paid = True
                    order.save()
                    logger.info(f"✅ Order {order.reference} marked as PAID")
            except Exception as e:
                logger.error(f"❌ Webhook Error processing success: {str(e)}")

        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            logger.warning(f"❌ Stripe Webhook: PaymentIntent {payment_intent['id']} failed")
            
            try:
                payment_ref = payment_intent.get('metadata', {}).get('payment_reference')
                if payment_ref:
                    payment = Payment.objects.get(reference=payment_ref)
                    payment.status = PaymentStatusChoices.FAILED
                    payment.gateway_response['error'] = payment_intent.get('last_payment_error', {}).get('message')
                    payment.save()
            except Exception as e:
                logger.error(f"❌ Webhook Error processing failure: {str(e)}")

        return HttpResponse(status=200)
