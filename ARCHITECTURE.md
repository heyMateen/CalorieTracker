# 🏗️ CalorieTracker Premium Subscription - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                   HTTP Request / Response
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     DJANGO APPLICATION                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              URL Router (mysite/urls.py)                │   │
│  │  /subscription/plans/    → subscription_plans view      │   │
│  │  /subscription/checkout/ → create_checkout view         │   │
│  │  /subscription/success/  → payment_success view         │   │
│  │  /stripe/webhook/        → stripe_webhook view          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│          ┌─────────────────┼─────────────────┐                  │
│          ▼                 ▼                 ▼                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │    Views     │ │ Subscription │ │   Models     │            │
│  │  (views.py)  │ │ Logic        │ │  (models.py) │            │
│  │              │ │(subscription.│ │              │            │
│  │- plans       │ │py)           │ │-UserProfile  │            │
│  │- checkout    │ │              │ │-Subscription│            │
│  │- success     │ │- Stripe API  │ │ Plan         │            │
│  │- webhook     │ │- Session Mgmt│ │-Payment      │            │
│  │- status      │ │- Validation  │ │ Log          │            │
│  │- cancel      │ │- Error Handle│ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                            │                                     │
│          ┌─────────────────┴─────────────────┐                  │
│          │                                   │                   │
│  ┌───────▼──────────┐           ┌────────────▼──────────┐       │
│  │   SQLite DB      │           │   Stripe Integration  │       │
│  │                  │           │                       │       │
│  │ Tables:          │           │ - API Calls           │       │
│  │ ├─ UserProfile   │           │ - Webhook Handling    │       │
│  │ ├─ SubscriptionPlan          │ - Session Management  │       │
│  │ ├─ SubscriptionPurchase      │ - Error Handling      │       │
│  │ └─ PaymentLog    │           │                       │       │
│  └──────────────────┘           └───────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                               │
                       Stripe API Call
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    STRIPE PAYMENT SYSTEM                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Stripe Checkout Page                        │   │
│  │        (Hosted Payment Processing)                       │   │
│  │  - Secure payment form                                   │   │
│  │  - PCI compliant                                         │   │
│  │  - Card validation                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                   Process Payment                                │
│                            │                                     │
│          ┌─────────────────┴─────────────────┐                  │
│          ▼                                   ▼                   │
│    ┌──────────────┐               ┌──────────────────────┐      │
│    │   Success    │               │      Webhook         │      │
│    │              │               │                      │      │
│    │Redirect User │               │Confirm payment async │      │
│    │to /success/  │               │Update database       │      │
│    └──────────────┘               └──────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Payment Processing

```
┌─ User at /subscription/plans/
│
├─ Selects a plan (e.g., Premium Monthly)
│
├─ Clicks "Subscribe Now"
│
├─ POST to /subscription/checkout/<plan_id>/
│  │
│  ├─ Check user is authenticated ✓
│  │
│  ├─ Load SubscriptionPlan from database
│  │
│  ├─ Call create_stripe_checkout_session()
│  │  │
│  │  ├─ Get or create Stripe customer
│  │  │
│  │  ├─ Call stripe.checkout.Session.create()
│  │  │  (Sends API request to Stripe)
│  │  │
│  │  └─ Return session object with checkout URL
│  │
│  └─ Redirect to session.url (Stripe hosted checkout)
│
├─ User on Stripe Checkout Page
│  │
│  ├─ Enter payment details
│  │
│  └─ Click "Pay"
│
├─ Stripe processes payment
│  │
│  ├─ Validates card
│  │
│  ├─ Charges user
│  │
│  └─ Sends success confirmation
│
├─ Stripe redirects to /subscription/success/?session_id=...
│
├─ retrieve_checkout_session() called
│  │
│  └─ Verify payment_status == 'paid'
│
├─ process_successful_payment() called
│  │
│  ├─ Create SubscriptionPurchase record
│  │
│  ├─ Update UserProfile:
│  │  ├─ is_premium = True
│  │  └─ premium_until = now + duration
│  │
│  └─ Create PaymentLog entry
│
└─ Redirect to /dashboard/ with success message
   (User now has premium access!)
```

---

## Webhook Flow

```
Stripe Event Occurs
(checkout.session.completed)
         │
         ├─ Stripe sends HTTP POST to /stripe/webhook/
         │
         ├─ payload + signature header included
         │
         ├─ Django receives request
         │
         ├─ verify_webhook_signature() called
         │  │
         │  ├─ Recreate signature from payload
         │  │
         │  ├─ Compare with header signature
         │  │
         │  └─ Return verified event or None
         │
         ├─ If valid:
         │  │
         │  ├─ Extract event type
         │  │
         │  ├─ Route to handler:
         │  │  ├─ checkout.session.completed → process_successful_payment()
         │  │  ├─ payment_intent.succeeded → log success
         │  │  └─ customer.subscription.deleted → log cancellation
         │  │
         │  └─ Update database
         │
         └─ Return HTTP 200 to Stripe
```

---

## Premium Feature Protection Flow

```
User requests protected feature
         │
         ├─ @require_premium decorator activated
         │
         ├─ Check if user is authenticated
         │  │
         │  └─ No? → Redirect to login
         │
         ├─ Load user.userprofile
         │
         ├─ Call is_premium_active()
         │  │
         │  ├─ Check is_premium == True
         │  │
         │  ├─ Check premium_until > now
         │  │
         │  └─ Return True/False
         │
         ├─ If premium_active:
         │  │
         │  └─ Execute view function
         │
         └─ Else:
            │
            └─ Redirect to /subscription/plans/
```

---

## Database Relationships

```
User (Django Auth)
  │
  └─ OneToOne ─► UserProfile
               ├─ is_premium (bool)
               ├─ premium_until (datetime)
               ├─ stripe_customer_id (FK to Stripe)
               └─ stripe_subscription_id (FK to Stripe)
                
SubscriptionPlan
  ├─ name, description, price
  ├─ duration_days
  └─ stripe_price_id (FK to Stripe)
    │
    └─ 1:Many ─┐
            │
            └─► SubscriptionPurchase
                ├─ user (FK)
                ├─ plan (FK)
                ├─ status
                ├─ start_date, end_date
                ├─ stripe_session_id
                └─ stripe_payment_intent_id
                  │
                  └─ 1:Many ─┐
                          │
                          └─► PaymentLog
                              ├─ user (FK)
                              ├─ transaction_type
                              ├─ amount, status
                              ├─ stripe_charge_id
                              └─ details (JSON)
```

---

## Security Layers

```
User Input
    │
    ├─► CSRF Token Verification ✓
    │
    ├─► Authentication Check ✓
    │
    ├─► Rate Limiting (Optional)
    │
    ├─► Stripe API Call
    │   └─► Stripe handles PCI compliance
    │
    ├─► Webhook Signature Verification ✓
    │
    └─► Database Constraint Checks ✓

Sensitive Data
    │
    ├─► Never store full credit card ✓
    │   (Stripe handles this)
    │
    ├─► API keys in settings.py only ✓
    │
    ├─► HTTPS recommended in production ✓
    │
    └─► Use environment variables for keys ✓
```

---

## Component Responsibilities

### Views (myapp/views.py)
- Handle HTTP requests/responses
- Validate user input
- Call subscription logic
- Render templates

### Subscription Logic (myapp/subscription.py)
- Stripe API integration
- Payment processing
- Webhook handling
- Security verification

### Models (myapp/models.py)
- Define data structure
- Validate data constraints
- Provide helper methods
- Track premium status

### Admin (myapp/admin.py)
- Plan management
- Payment monitoring
- User subscription viewing
- Transaction audit

### Templates
- Display plans
- Payment forms
- Subscription status
- User messages

---

## Error Handling Flow

```
Error Occurs
    │
    ├─ StripePaymentError exception
    │
    ├─ Caught in try/except
    │
    ├─ Log error details
    │
    ├─ Store in PaymentLog with status='failed'
    │
    ├─ Show user-friendly message
    │
    └─ Redirect to plans or dashboard
```

---

## Scalability Considerations

Current implementation supports:
- ✅ Multiple subscription plans
- ✅ Multiple payment methods (via Stripe)
- ✅ Payment history tracking
- ✅ User isolation (no cross-account access)
- ✅ Webhook async processing
- ✅ Audit logging of all transactions

Future enhancements:
- 🔄 Recurring subscriptions
- 🔄 Usage-based billing
- 🔄 Promo codes/discounts
- 🔄 Team accounts
- 🔄 Invoice generation
- 🔄 Cancellation reasons analytics

---

## Technology Stack

```
Frontend
├─ HTML5 / CSS3 / Bootstrap
├─ JavaScript (optional for AJAX)
└─ Stripe Checkout (hosted)

Backend
├─ Django 3.1+
├─ Python 3.11+
├─ SQLite (development) / PostgreSQL (production)
└─ stripe-python library

Payment Provider
├─ Stripe API
├─ Stripe Checkout
└─ Webhooks

Deployment
├─ Django development server (dev)
├─ Gunicorn + Nginx (production)
├─ HTTPS (Let's Encrypt)
└─ Environment variables for secrets
```

---

**This architecture ensures a secure, scalable, and maintainable premium subscription system for CalorieTracker!** 🚀
