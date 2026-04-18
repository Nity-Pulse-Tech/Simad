import json
import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock
from simad.orders.models import Payment, Order
from simad.global_data.enum import PaymentStatusChoices, PaymentProviderChoices, PaymentMethodChoices
from django.utils import timezone

@pytest.mark.django_db
class TestStripeWebhook:
    def setup_method(self):
        # Create a user, order and payment for testing
        from simad.users.models import User
        self.user = User.objects.create_user(
            email="test@example.com", 
            password="password", 
            phone_number="123456789",
            is_active=True
        )
        self.order = Order.objects.create(
            user=self.user,
            reference="ORD-TEST-123",
            total=5000,
            status="PENDING"
        )
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            reference="ST-TEST-REF",
            method=PaymentMethodChoices.CREDIT_CARD,
            provider=PaymentProviderChoices.STRIPE,
            status=PaymentStatusChoices.PROCESSING,
            amount=5000,
            currency="XAF",
            stripe_payment_intent_id="pi_123"
        )
        self.webhook_url = reverse('core:stripe-webhook')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_success(self, mock_construct):
        # Mock Stripe Event
        mock_event = MagicMock()
        mock_event.id = "evt_123"
        mock_event.__getitem__.side_effect = lambda key: {
            'type': 'payment_intent.succeeded',
            'id': 'evt_123',
            'data': {
                'object': {
                    'id': 'pi_123',
                    'status': 'succeeded',
                    'metadata': {'payment_reference': 'ST-TEST-REF'}
                }
            }
        }[key]
        mock_construct.return_value = mock_event

        payload = {"id": "evt_123", "type": "payment_intent.succeeded"}
        response = MagicMock() # We'll use client.post
        
        # We need to use the real client to test the view
        from django.test import Client
        client = Client()
        resp = client.post(self.webhook_url, 
                          data=json.dumps(payload), 
                          content_type='application/json',
                          HTTP_STRIPE_SIGNATURE='valid_sig')

        assert resp.status_code == 200
        
        # Verify payment updated
        self.payment.refresh_from_db()
        assert self.payment.status == PaymentStatusChoices.SUCCEEDED
        assert self.payment.webhook_events == ["evt_123"]
        
        # Verify order updated
        self.order.refresh_from_db()
        assert self.order.is_paid is True

    @patch('stripe.Webhook.construct_event')
    def test_webhook_idempotency(self, mock_construct):
        # Setup payment with existing event
        self.payment.webhook_events = ["evt_123"]
        self.payment.save()

        mock_event = MagicMock()
        mock_event.id = "evt_123"
        mock_event.__getitem__.side_effect = lambda key: {
            'type': 'payment_intent.succeeded',
            'id': 'evt_123',
            'data': {
                'object': {
                    'id': 'pi_123',
                    'status': 'succeeded',
                    'metadata': {'payment_reference': 'ST-TEST-REF'}
                }
            }
        }[key]
        mock_construct.return_value = mock_event

        from django.test import Client
        client = Client()
        resp = client.post(self.webhook_url, 
                          data=json.dumps({}), 
                          content_type='application/json',
                          HTTP_STRIPE_SIGNATURE='valid_sig')

        assert resp.status_code == 200
        # No change should happen, verified by mocking or checking logs (here we just check status code)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_failure(self, mock_construct):
        mock_event = MagicMock()
        mock_event.id = "evt_failed"
        mock_event.__getitem__.side_effect = lambda key: {
            'type': 'payment_intent.payment_failed',
            'id': 'evt_failed',
            'data': {
                'object': {
                    'id': 'pi_123',
                    'last_payment_error': {'message': 'Insufficient funds'},
                    'metadata': {'payment_reference': 'ST-TEST-REF'}
                }
            }
        }[key]
        mock_construct.return_value = mock_event

        from django.test import Client
        client = Client()
        resp = client.post(self.webhook_url, 
                          data=json.dumps({}), 
                          content_type='application/json',
                          HTTP_STRIPE_SIGNATURE='valid_sig')

        assert resp.status_code == 200
        self.payment.refresh_from_db()
        assert self.payment.status == PaymentStatusChoices.FAILED

@pytest.mark.django_db
class TestStripeViews:
    def setup_method(self):
        from django.test import Client
        from simad.users.models import User
        self.user = User.objects.create_user(
            email="user@example.com", 
            password="password", 
            phone_number="987654321",
            is_active=True # Crucial for force_login
        )
        self.order = Order.objects.create(user=self.user, reference="ORD-VIEW-1", total=1000)
        self.create_url = reverse('core:stripe-create-intent')
        self.status_url = reverse('core:payment-status')
        self.client = Client()
        self.client.force_login(self.user)

    @patch('simad.payments.services.StripeService.create_checkout_session')
    def test_payment_view_checkout_redirect(self, mock_create):
        mock_create.return_value = {
            'success': True,
            'session_id': 'sess_123',
            'url': 'https://checkout.stripe.com/pay/sess_123'
        }
        
        from django.test import Client
        url = reverse('core:payment')
        
        # Set session
        session = self.client.session
        session['order_ref'] = self.order.reference
        session.save()
        
        resp = self.client.post(url, data={'payment_method': 'card'})
        
        assert resp.status_code == 302, f"Expected 302, got {resp.status_code}. Content: {resp.content}"
        assert resp.url == 'https://checkout.stripe.com/pay/sess_123'
        
        # Verify payment record
        assert Payment.objects.filter(order=self.order, provider=PaymentProviderChoices.STRIPE).exists()
        payment = Payment.objects.get(order=self.order, provider=PaymentProviderChoices.STRIPE)
        assert payment.stripe_checkout_session_id == 'sess_123'

    def test_get_status_view(self):
        payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            reference="ST-STATUS-CHECK",
            status=PaymentStatusChoices.SUCCEEDED,
            amount=1000,
            currency="XAF"
        )
        
        resp = self.client.get(f"{self.status_url}?reference=ST-STATUS-CHECK")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}. Content: {resp.content}"
        data = resp.json()
        assert data['is_paid'] is True, f"Expected is_paid=True, got {data}"

    @patch('simad.payments.services.PayUnitService.make_direct_payment')
    def test_payunit_polling_render(self, mock_make):
        mock_make.return_value = {
            'success': True,
            'message': 'Prompt sent',
            'data': {'t_id': '123'}
        }
        
        url = reverse('core:payment')
        session = self.client.session
        session['order_ref'] = self.order.reference
        session.save()
        
        resp = self.client.post(url, data={
            'payment_method': 'mtn_momo',
            'mtn_phone': '677777777'
        })
        
        assert resp.status_code == 200
        assert b"Confirmation requise" in resp.content
        assert b"Un message de confirmation a" in resp.content
