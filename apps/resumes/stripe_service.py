# ============================================
# resumes/stripe_service.py
# ============================================

"""
Stripe integration for payment processing
pip install stripe==7.0.0
"""

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from .models import Subscription, Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Handle all Stripe operations"""
    
    PLAN_PRICES = {
        'basic': 'price_basic_monthly',  # Replace with your Stripe Price IDs
        'pro': 'price_pro_monthly',
        'enterprise': 'price_enterprise_monthly',
    }
    
    @classmethod
    def create_customer(cls, user):
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name(),
                metadata={'user_id': user.id}
            )
            
            # Update subscription with customer ID
            subscription, created = Subscription.objects.get_or_create(user=user)
            subscription.stripe_customer_id = customer.id
            subscription.save()
            
            return customer
        
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @classmethod
    def create_checkout_session(cls, user, plan):
        """Create Stripe Checkout session for subscription"""
        
        # Get or create customer
        subscription = Subscription.objects.get(user=user)
        if not subscription.stripe_customer_id:
            customer = cls.create_customer(user)
            customer_id = customer.id
        else:
            customer_id = subscription.stripe_customer_id
        
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': cls.PLAN_PRICES[plan],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.SITE_URL + '/subscription/success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_URL + '/subscription/cancelled/',
                metadata={
                    'user_id': user.id,
                    'plan': plan,
                }
            )
            
            return checkout_session
        
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @classmethod
    def create_billing_portal_session(cls, user):
        """Create customer portal session for managing subscription"""
        subscription = Subscription.objects.get(user=user)
        
        if not subscription.stripe_customer_id:
            raise Exception("No Stripe customer found")
        
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=settings.SITE_URL + '/dashboard/',
            )
            
            return portal_session
        
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @classmethod
    def cancel_subscription(cls, user):
        """Cancel user's subscription at period end"""
        subscription = Subscription.objects.get(user=user)
        
        if not subscription.stripe_subscription_id:
            raise Exception("No active subscription found")
        
        try:
            stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            subscription.cancel_at_period_end = True
            subscription.save()
            
            return stripe_sub
        
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @classmethod
    def handle_webhook(cls, payload, sig_header):
        """Handle Stripe webhooks"""
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise Exception("Invalid signature")
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            cls._handle_checkout_completed(event['data']['object'])
        
        elif event['type'] == 'customer.subscription.updated':
            cls._handle_subscription_updated(event['data']['object'])
        
        elif event['type'] == 'customer.subscription.deleted':
            cls._handle_subscription_deleted(event['data']['object'])
        
        elif event['type'] == 'invoice.payment_succeeded':
            cls._handle_payment_succeeded(event['data']['object'])
        
        elif event['type'] == 'invoice.payment_failed':
            cls._handle_payment_failed(event['data']['object'])
        
        return event
    
    @classmethod
    def _handle_checkout_completed(cls, session):
        """Handle successful checkout"""
        user_id = session['metadata']['user_id']
        plan = session['metadata']['plan']
        
        user = User.objects.get(id=user_id)
        subscription = Subscription.objects.get(user=user)
        
        # Get subscription details from Stripe
        stripe_sub = stripe.Subscription.retrieve(session['subscription'])
        
        # Update subscription
        subscription.plan = plan
        subscription.status = 'active'
        subscription.stripe_subscription_id = stripe_sub.id
        subscription.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start)
        subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
        
        # Set features based on plan
        if plan == 'basic':
            subscription.max_resumes = 10
            subscription.ai_credits = 10
        elif plan == 'pro':
            subscription.max_resumes = -1  # Unlimited
            subscription.ai_credits = 50
        elif plan == 'enterprise':
            subscription.max_resumes = -1  # Unlimited
            subscription.ai_credits = 200
        
        subscription.save()
        
        # Send confirmation email
        from .email_service import EmailService
        EmailService.send_subscription_confirmation(user, plan)
    
    @classmethod
    def _handle_subscription_updated(cls, stripe_sub):
        """Handle subscription updates"""
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub.id
            )
            
            subscription.status = stripe_sub.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
            subscription.cancel_at_period_end = stripe_sub.cancel_at_period_end
            subscription.save()
        
        except Subscription.DoesNotExist:
            pass
    
    @classmethod
    def _handle_subscription_deleted(cls, stripe_sub):
        """Handle subscription cancellation"""
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub.id
            )
            
            subscription.status = 'cancelled'
            subscription.plan = 'free'
            subscription.max_resumes = 3
            subscription.ai_credits = 0
            subscription.save()
        
        except Subscription.DoesNotExist:
            pass
    
    @classmethod
    def _handle_payment_succeeded(cls, invoice):
        """Record successful payment"""
        customer_id = invoice['customer']
        
        try:
            subscription = Subscription.objects.get(stripe_customer_id=customer_id)
            
            Payment.objects.create(
                user=subscription.user,
                amount=invoice['amount_paid'] / 100,  # Convert cents to dollars
                currency=invoice['currency'].upper(),
                stripe_payment_intent_id=invoice['payment_intent'],
                stripe_charge_id=invoice['charge'],
                status='succeeded',
                description=f"Subscription payment - {subscription.get_plan_display()}"
            )
        
        except Subscription.DoesNotExist:
            pass
    
    @classmethod
    def _handle_payment_failed(cls, invoice):
        """Handle failed payment"""
        customer_id = invoice['customer']
        
        try:
            subscription = Subscription.objects.get(stripe_customer_id=customer_id)
            
            # Send payment failure email
            from .email_service import EmailService
            EmailService.send_payment_failed_email(subscription.user)
        
        except Subscription.DoesNotExist:
            pass
