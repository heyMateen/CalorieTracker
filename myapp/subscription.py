"""
Subscription and payment gateway integration with Stripe
"""
import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.utils import timezone
from datetime import timedelta
import json
import logging

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class StripePaymentError(Exception):
    """Custom exception for Stripe payment errors"""
    pass


def require_premium(view_func):
    """
    Decorator to check if user has active premium subscription.
    If not, redirects to subscription plans page.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user_profile = request.user.userprofile
        
        # Check if user has active premium subscription
        if not user_profile.is_premium_active():
            # Redirect to subscription plans
            return redirect('subscription_plans')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_or_create_stripe_customer(user):
    """
    Get or create a Stripe customer for the user
    """
    user_profile = user.userprofile
    
    # If customer already exists in Stripe, return their ID
    if user_profile.stripe_customer_id:
        return user_profile.stripe_customer_id
    
    try:
        # Create new customer in Stripe
        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name() or user.username,
            metadata={
                'user_id': str(user.id),
                'username': user.username
            }
        )
        
        # Store customer ID in database
        user_profile.stripe_customer_id = customer.id
        user_profile.save()
        
        logger.info(f"Created Stripe customer {customer.id} for user {user.username}")
        return customer.id
    
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe customer: {str(e)}")
        raise StripePaymentError(f"Failed to create payment customer: {str(e)}")


def create_stripe_checkout_session(user, subscription_plan):
    """
    Create a Stripe checkout session for a subscription plan
    
    Args:
        user: User object
        subscription_plan: SubscriptionPlan object
    
    Returns:
        session: Stripe checkout session object
    """
    try:
        # Get or create Stripe customer
        customer_id = get_or_create_stripe_customer(user)
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': subscription_plan.name,
                            'description': subscription_plan.description,
                        },
                        'unit_amount': int(subscription_plan.price * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url=settings.SITE_URL + '/subscription/success/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.SITE_URL + '/subscription/plans/',
            metadata={
                'user_id': str(user.id),
                'plan_id': str(subscription_plan.id),
                'plan_name': subscription_plan.name,
            }
        )
        
        logger.info(f"Created checkout session {session.id} for user {user.username}")
        return session
    
    except stripe.error.StripeError as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise StripePaymentError(f"Failed to create checkout session: {str(e)}")


def process_successful_payment(session_id, user_id, plan_id):
    """
    Process a successful payment from Stripe webhook
    
    Args:
        session_id: Stripe checkout session ID
        user_id: Django user ID
        plan_id: SubscriptionPlan ID
    """
    from django.contrib.auth.models import User
    from .models import SubscriptionPurchase, SubscriptionPlan, PaymentLog
    
    try:
        # Retrieve session details from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        user = User.objects.get(id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        # Create subscription purchase record
        start_date = timezone.now()
        end_date = start_date + timedelta(days=plan.duration_days)
        
        subscription_purchase = SubscriptionPurchase.objects.create(
            user=user,
            plan=plan,
            stripe_session_id=session_id,
            stripe_payment_intent_id=session.payment_intent,
            status='active',
            amount=plan.price,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Update user profile
        user_profile = user.userprofile
        user_profile.is_premium = True
        user_profile.premium_until = end_date
        user_profile.save()
        
        # Log payment transaction
        PaymentLog.objects.create(
            user=user,
            subscription_purchase=subscription_purchase,
            stripe_charge_id=session.payment_intent,
            transaction_type='charge',
            amount=plan.price,
            status='succeeded',
            details=session.to_dict()
        )
        
        logger.info(f"Processed successful payment for user {user.username}")
        return subscription_purchase
    
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        raise StripePaymentError(f"Failed to process payment: {str(e)}")


def retrieve_checkout_session(session_id):
    """
    Retrieve checkout session details from Stripe
    """
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['line_items', 'payment_intent']
        )
        return session
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving session: {str(e)}")
        raise StripePaymentError(f"Failed to retrieve session: {str(e)}")


def verify_webhook_signature(body, sig_header):
    """
    Verify Stripe webhook signature
    
    Args:
        body: Raw request body
        sig_header: Stripe signature header
    
    Returns:
        event: Stripe event object if valid
    """
    try:
        event = stripe.Webhook.construct_event(
            body,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError:
        logger.error("Invalid webhook payload")
        return None
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        return None


def cancel_subscription(user):
    """
    Cancel user's premium subscription
    """
    try:
        user_profile = user.userprofile
        
        if user_profile.stripe_subscription_id:
            # Cancel subscription in Stripe
            stripe.Subscription.delete(user_profile.stripe_subscription_id)
        
        # Update user profile
        user_profile.is_premium = False
        user_profile.premium_until = None
        user_profile.stripe_subscription_id = None
        user_profile.save()
        
        logger.info(f"Cancelled subscription for user {user.username}")
        return True
    
    except stripe.error.StripeError as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        return False
