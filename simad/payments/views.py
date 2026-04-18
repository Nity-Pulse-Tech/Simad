import json
import logging
import uuid
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import get_object_or_404

from simad.orders.models import Payment, Order
from simad.global_data.enum import PaymentStatusChoices, PaymentProviderChoices, PaymentMethodChoices
from simad.payments.services import StripeService

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
            
            transaction_id = data.get('transaction_id')
            status = data.get('status') # Usually 'SUCCESS' or 'FAILED'
            
            if not transaction_id:
                logger.error("No transaction_id in PayUnit webhook")
                return JsonResponse({"status": "error", "message": "No transaction_id"}, status=400)
                
            try:
                payment = Payment.objects.get(reference=transaction_id)
                
                # Check if already processed
                if payment.status in [PaymentStatusChoices.SUCCEEDED, PaymentStatusChoices.FAILED]:
                    return JsonResponse({"status": "ok", "message": "Already processed"})

                if status == 'SUCCESS':
                    payment.status = PaymentStatusChoices.SUCCEEDED
                    payment.paid_at = timezone.now()
                    payment.gateway_response = data
                    payment.save()
                    
                    # Update Order status
                    order = payment.order
                    order.is_paid = True
                    order.status = "PROCESSING"
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
            logger.error(f"Error in PayUnitWebhookView: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CreateStripePaymentIntentView(View):
    """
    Creates a Stripe PaymentIntent and returns the client_secret.
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        try:
            data = json.loads(request.body)
            order_reference = data.get('order_reference')
            
            if not order_reference:
                return JsonResponse({"error": "order_reference is required"}, status=400)
            
            order = get_object_or_404(Order, reference=order_reference, user=request.user)
            
            # Check if there's already an active payment for this order
            # We allow retrying if the previous one failed or was canceled
            
            with transaction.atomic():
                payment_ref = f"ST-{uuid.uuid4().hex[:12].upper()}"
                payment = Payment.objects.create(
                    order=order,
                    user=request.user,
                    reference=payment_ref,
                    method=PaymentMethodChoices.CREDIT_CARD,
                    provider=PaymentProviderChoices.STRIPE,
                    status=PaymentStatusChoices.PENDING,
                    amount=order.total,
                    currency="XAF"
                )
                
                stripe_service = StripeService()
                result = stripe_service.create_payment_intent(
                    amount=int(order.total),
                    currency="XAF",
                    metadata={
                        "order_reference": order.reference,
                        "payment_reference": payment_ref,
                        "user_id": str(request.user.id)
                    },
                    idempotency_key=payment_ref
                )
                
                if result['success']:
                    payment.stripe_payment_intent_id = result['intent_id']
                    payment.status = PaymentStatusChoices.PROCESSING
                    payment.save()
                    
                    return JsonResponse({
                        "client_secret": result['client_secret'],
                        "payment_reference": payment_ref,
                        "intent_id": result['intent_id']
                    })
                else:
                    payment.status = PaymentStatusChoices.FAILED
                    payment.gateway_response = result
                    payment.save()
                    return JsonResponse({"error": result['message']}, status=400)
                    
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.exception("Error creating payment intent")
            return JsonResponse({"error": "Internal server error"}, status=500)

class GetPaymentStatusView(View):
    """
    Returns the current status of a payment.
    """
    def get(self, request, *args, **kwargs):
        payment_reference = request.GET.get('reference')
        if not payment_reference:
            return JsonResponse({"error": "reference is required"}, status=400)
        
        payment = get_object_or_404(Payment, reference=payment_reference)
        
        # Security check: only the owner or staff can see status
        if payment.user != request.user and not request.user.is_staff:
             return JsonResponse({"error": "Permission denied"}, status=403)

        return JsonResponse({
            "reference": payment.reference,
            "status": payment.status,
            "status_display": payment.get_status_display(),
            "is_paid": payment.status == PaymentStatusChoices.SUCCEEDED,
            "order_reference": payment.order.reference
        })

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Webhook handler for Stripe events.
    Source of truth for payment confirmation.
    """
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        stripe_service = StripeService()
        result = stripe_service.construct_event(payload, sig_header)
        
        if not result['success']:
            logger.error(f"Webhook Signature Verification Failed: {result.get('message')}")
            return HttpResponse(status=400)
            
        event = result['event']
        event_id = event['id']
        
        # Handle the event
        # 1. Success
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self._process_payment_success(payment_intent, event_id)

        # 2. Failure
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self._process_payment_failure(payment_intent, event_id)

        # 3. Canceled
        elif event['type'] == 'payment_intent.canceled':
            payment_intent = event['data']['object']
            self._process_payment_canceled(payment_intent, event_id)

        return HttpResponse(status=200)

    def _process_payment_success(self, payment_intent, event_id):
        payment_ref = payment_intent.get('metadata', {}).get('payment_reference')
        if not payment_ref:
            logger.error(f"No payment_reference in Stripe metadata for intent {payment_intent['id']}")
            return

        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(reference=payment_ref)
                
                # Idempotency check
                if event_id in (payment.webhook_events or []):
                    logger.info(f"Event {event_id} already processed for payment {payment_ref}")
                    return

                # Record event
                if payment.webhook_events is None:
                    payment.webhook_events = []
                payment.webhook_events.append(event_id)

                if payment.status != PaymentStatusChoices.SUCCEEDED:
                    payment.status = PaymentStatusChoices.SUCCEEDED
                    payment.paid_at = timezone.now()
                    payment.gateway_response['latest_event'] = payment_intent
                    payment.save()
                    
                    order = payment.order
                    order.is_paid = True
                    order.status = "PROCESSING" # Or whatever fulfillment status you use
                    order.save()
                    
                    logger.info(f"✅ Webhook: Payment {payment_ref} and Order {order.reference} marked as SUCCEEDED")
                
            except Payment.DoesNotExist:
                logger.error(f"Payment {payment_ref} not found during webhook processing")

    def _process_payment_failure(self, payment_intent, event_id):
        payment_ref = payment_intent.get('metadata', {}).get('payment_reference')
        if not payment_ref: return

        try:
            payment = Payment.objects.get(reference=payment_ref)
            if event_id in (payment.webhook_events or []): return
            
            if payment.webhook_events is None: payment.webhook_events = []
            payment.webhook_events.append(event_id)
            
            payment.status = PaymentStatusChoices.FAILED
            payment.gateway_response['error'] = payment_intent.get('last_payment_error', {}).get('message')
            payment.save()
            logger.warning(f"❌ Webhook: Payment {payment_ref} marked as FAILED")
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_ref} not found during webhook failure processing")

    def _process_payment_canceled(self, payment_intent, event_id):
        payment_ref = payment_intent.get('metadata', {}).get('payment_reference')
        if not payment_ref: return

        try:
            payment = Payment.objects.get(reference=payment_ref)
            if event_id in (payment.webhook_events or []): return
            
            if payment.webhook_events is None: payment.webhook_events = []
            payment.webhook_events.append(event_id)
            
            payment.status = PaymentStatusChoices.CANCELED
            payment.save()
            logger.info(f"⚪ Webhook: Payment {payment_ref} marked as CANCELED")
        except Payment.DoesNotExist:
            pass
