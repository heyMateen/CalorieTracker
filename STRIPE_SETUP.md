# Stripe Premium Subscription Integration Guide

## Overview
Your CalorieTracker application now has a complete Stripe payment gateway integration for premium subscription features. Users can subscribe to premium plans and access exclusive features.

---

## 🔧 Setup Instructions

### 1. **Get Your Stripe API Keys**

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Sign up or log in to your Stripe account
3. You'll find:
   - **Publishable Key** (starts with `pk_test_`)
   - **Secret Key** (starts with `sk_test_`)
4. Copy both keys

### 2. **Configure Settings**

Edit `/mysite/settings.py` and replace the placeholder keys:

```python
# In settings.py
STRIPE_PUBLIC_KEY = 'pk_test_YOUR_ACTUAL_KEY_HERE'
STRIPE_SECRET_KEY = 'sk_test_YOUR_ACTUAL_KEY_HERE'
STRIPE_WEBHOOK_SECRET = 'whsec_YOUR_WEBHOOK_SECRET_HERE'
SITE_URL = 'http://localhost:8000'  # Change for production
```

### 3. **Install Required Package**

```bash
pip install stripe
# Or update requirements.txt
pip install -r requirements.txt
```

### 4. **Run Migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 📋 Database Models

### **SubscriptionPlan**
Defines available subscription tiers:
- Name, description, price
- Duration (monthly, quarterly, yearly)
- Stripe Price ID (set after creating in Stripe)

### **SubscriptionPurchase**
Tracks individual subscription purchases:
- Links users to subscription plans
- Stores Stripe session and payment intent IDs
- Tracks subscription period (start_date, end_date)

### **PaymentLog**
Audit trail for all transactions:
- Transaction type (charge, refund, dispute)
- Status and amount
- Stores full Stripe response

### **UserProfile Enhancement**
Added fields:
- `is_premium`: Boolean flag
- `premium_until`: Expiration datetime
- `stripe_customer_id`: Stripe customer reference
- `stripe_subscription_id`: Active subscription reference

---

## 🎯 How It Works

### **User Flow**

```
1. Non-premium user visits protected feature
                ↓
2. @require_premium decorator redirects to /subscription/plans/
                ↓
3. User views available plans and clicks "Subscribe Now"
                ↓
4. Application creates Stripe checkout session
                ↓
5. User is redirected to Stripe checkout page
                ↓
6. User enters payment details & completes purchase
                ↓
7. Stripe confirms payment & redirects to success page
                ↓
8. User profile updated with premium status
                ↓
9. User gains access to premium features!
```

---

## 🔐 Protecting Premium Features

### **Using the @require_premium Decorator**

Wrap any view that should be premium-only:

```python
from myapp.subscription import require_premium

@require_premium
def my_premium_feature(request):
    """This feature is only accessible to premium members"""
    # Your code here
    pass
```

Example: Make meal planning a premium feature:

```python
from .subscription import require_premium

@require_premium
@login_required
def create_meal_plan(request):
    """Create a meal plan - Premium feature only"""
    # Implementation
    pass
```

---

## 💳 Testing

### **Test Card Numbers** (Stripe Sandbox)

| Card Type | Number | Expiry | CVC |
|-----------|--------|--------|-----|
| Visa | 4242 4242 4242 4242 | Any future date | Any 3 digits |
| Visa (Declined) | 4000 0000 0000 0002 | Any future date | Any 3 digits |
| American Express | 3782 822463 10005 | Any future date | Any 4 digits |

### **Test Process**

1. Start your Django server: `python manage.py runserver`
2. Go to `/subscription/plans/`
3. Click "Subscribe Now" on any plan
4. You'll be redirected to Stripe test checkout
5. Use test card `4242 4242 4242 4242`
6. Enter any future expiry date (e.g., 12/25)
7. Enter any 3-digit CVC
8. Complete the payment
9. You should be redirected to success page with premium access!

---

## 🔔 Webhook Setup (Important for Production)

Webhooks allow Stripe to notify your application of payment events.

### **In Stripe Dashboard:**

1. Go to Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/stripe/webhook/`
3. Select events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `customer.subscription.deleted`
4. Copy the signing secret to `STRIPE_WEBHOOK_SECRET`

### **Local Testing with Stripe CLI:**

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to your account
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/stripe/webhook/

# Copy the signing secret and add to settings.py
```

---

## 📊 Admin Panel Management

### **Create Subscription Plans**

1. Go to Django admin: `/admin/`
2. Click "Subscription Plans"
3. Click "Add Subscription Plan"
4. Fill in details:
   - **Name**: "Premium Monthly"
   - **Description**: "Monthly premium access"
   - **Duration**: "monthly"
   - **Price**: 9.99
   - **Duration Days**: 30
   - **Is Active**: ✓

Example Plans to Create:

```
1. Premium Monthly - $9.99 - 30 days
2. Premium Quarterly - $24.99 - 90 days
3. Premium Yearly - $89.99 - 365 days
```

### **View Subscriptions**

- **SubscriptionPurchase**: See user purchases & payment history
- **PaymentLog**: Audit all transactions
- **UserProfile**: Check premium status & expiration

---

## 📍 URL Routes

| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/subscription/plans/` | View available plans | Yes |
| `/subscription/checkout/<plan_id>/` | Create checkout session | Yes |
| `/subscription/success/` | Handle successful payment | Yes |
| `/subscription/status/` | View subscription details | Yes |
| `/subscription/cancel/` | Cancel active subscription | Yes |
| `/stripe/webhook/` | Receive Stripe events | No (CSRF exempt) |

---

## 🚀 Code Examples

### **Example 1: Protect a Feature**

```python
from django.shortcuts import render
from myapp.subscription import require_premium

@require_premium
def advanced_nutrition_analysis(request):
    """Premium feature: Advanced nutrition insights"""
    user_profile = request.user.userprofile
    
    context = {
        'premium_features': get_premium_analytics(request.user)
    }
    return render(request, 'premium/nutrition_analysis.html', context)
```

### **Example 2: Check Premium Status in Templates**

```html
{% if user.userprofile.is_premium_active %}
    <p>You have premium access until {{ user.userprofile.premium_until|date:"F d, Y" }}</p>
    <a href="{% url 'meal_planner' %}">Open Smart Meal Planner</a>
{% else %}
    <p>Upgrade to premium to unlock advanced features!</p>
    <a href="{% url 'subscription_plans' %}" class="btn btn-primary">
        Upgrade Now
    </a>
{% endif %}
```

### **Example 3: Redirect Non-Premium Users**

```python
from django.shortcuts import redirect

def meal_planning_view(request):
    user_profile = request.user.userprofile
    
    if not user_profile.is_premium_active():
        messages.info(request, 'Meal planning is a premium feature.')
        return redirect('subscription_plans')
    
    # Rest of meal planning logic
    return render(request, 'premium/meal_planner.html')
```

---

## 🔍 Troubleshooting

### **"ModuleNotFoundError: No module named 'stripe'"**
```bash
pip install stripe
```

### **"Invalid API Key"**
- Check that your key is correctly copied
- Make sure you're using the test key (starts with `pk_test_` or `sk_test_`)
- Don't share secret keys in code!

### **Webhook Not Receiving Events**
- Check webhook URL in Stripe dashboard
- Ensure signing secret is correct in settings.py
- Use Stripe CLI to test locally

### **User Stays Non-Premium After Payment**
- Check PaymentLog in admin to see transaction status
- Verify webhook is configured (if using production)
- Check Django logs for errors

---

## 📧 Email Notifications (Optional Enhancement)

You can add email confirmations to `views.py`:

```python
from django.core.mail import send_mail

def payment_success(request):
    # ... existing code ...
    
    # Send confirmation email
    send_mail(
        'Premium Subscription Confirmed',
        f'Your subscription is active until {subscription_purchase.end_date}',
        'noreply@calorietracker.com',
        [request.user.email]
    )
    
    return redirect('dashboard')
```

---

## 🛡️ Security Best Practices

✅ **DO:**
- Use environment variables for API keys in production
- Keep STRIPE_WEBHOOK_SECRET secure
- Validate webhook signatures (already implemented)
- Use HTTPS in production
- Regularly check payment logs

❌ **DON'T:**
- Commit API keys to GitHub
- Expose secret key in frontend
- Skip webhook signature verification
- Test with real credit cards
- Use test keys in production

---

## 📞 API Key Placeholder Locations

These need your actual Stripe keys:

1. **mysite/settings.py:**
   - `STRIPE_PUBLIC_KEY`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`

2. **Environment Variables (Recommended for Production):**
```python
import os
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
```

---

## 📚 Key Files Modified/Created

- `myapp/subscription.py` - Stripe integration logic
- `myapp/models.py` - Added SubscriptionPlan, SubscriptionPurchase, PaymentLog
- `myapp/views.py` - Subscription views and webhook handler
- `mysite/settings.py` - Stripe configuration
- `mysite/urls.py` - Subscription URLs
- `myapp/templates/myapp/subscription_*.html` - UI templates
- `requirements.txt` - Added stripe package
- `myapp/migrations/0005_*.py` - Database schema

---

## ✨ Next Steps

1. **Get Stripe Account**: [stripe.com/register](https://stripe.com/register)
2. **Add API Keys** to settings.py
3. **Create Plans** in Django admin
4. **Test with** test card: `4242 4242 4242 4242`
5. **Protect Features** with `@require_premium` decorator
6. **Deploy** to production with real keys
7. **Configure Webhooks** for production domain

---

## 🤝 Support Resources

- [Stripe Python Docs](https://stripe.com/docs/stripe-js)
- [Stripe Checkout Documentation](https://stripe.com/docs/payments/checkout)
- [Django Payment Integration Guide](https://stripe.com/docs/plugins/django)
- [Webhook Signature Verification](https://stripe.com/docs/webhooks/signatures)

---

**Your CalorieTracker is now ready for premium subscriptions! 🎉**
