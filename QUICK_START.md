# 🚀 Quick Reference - Stripe Integration for CalorieTracker

## ⚡ 5-Minute Setup

### 1️⃣ Get Stripe Keys
Visit: https://dashboard.stripe.com/apikeys
- Copy **Publishable Key** (pk_test_...)
- Copy **Secret Key** (sk_test_...)

### 2️⃣ Update Settings
Edit `mysite/settings.py`:
```python
STRIPE_PUBLIC_KEY = 'pk_test_YOUR_KEY_HERE'
STRIPE_SECRET_KEY = 'sk_test_YOUR_KEY_HERE'
STRIPE_WEBHOOK_SECRET = 'whsec_YOUR_KEY_HERE'
```

### 3️⃣ Create Plans
```bash
python manage.py shell
exec(open('myapp/init_plans.py').read())
```

### 4️⃣ Test Payment
Go to: http://localhost:8000/subscription/plans/

---

## 📚 File Reference

| File | Purpose |
|------|---------|
| `myapp/subscription.py` | Stripe API integration |
| `myapp/views.py` | Subscription views |
| `myapp/models.py` | Database models |
| `mysite/settings.py` | Stripe configuration |
| `mysite/urls.py` | Subscription routes |
| `myapp/admin.py` | Admin panel setup |

---

## 🔑 Key Components

### Decorator for Protection
```python
from myapp.subscription import require_premium

@require_premium
def my_feature(request):
    pass
```

### Check Premium Status
```python
if request.user.userprofile.is_premium_active():
    # Show premium features
else:
    # Show upgrade prompt
```

### In Templates
```html
{% if user.userprofile.is_premium_active %}
    <!-- Premium content -->
{% endif %}
```

---

## 💳 Test Card: `4242 4242 4242 4242`

Expiry: Any future date (MM/YY)  
CVC: Any 3 digits

---

## 📍 URL Routes

```
/subscription/plans/          - View plans
/subscription/checkout/1/     - Start payment for plan 1
/subscription/success/        - Payment confirmation
/subscription/status/         - View subscription
/subscription/cancel/         - Cancel subscription
/stripe/webhook/              - Webhook endpoint
```

---

## 🛡️ Security

✅ Webhook signature verification  
✅ CSRF protection  
✅ Secure API keys in settings  
✅ User isolation  
✅ Audit logging  

---

## 🐛 Test Scenarios

| Scenario | Card | Result |
|----------|------|--------|
| Success | 4242 4242 4242 4242 | ✅ Payment succeeds |
| Decline | 4000 0000 0000 0002 | ❌ Payment fails |
| 3D Secure | 4000 0025 0000 3155 | ⚠️ Requires auth |

---

## 🔗 Useful Links

- Stripe Dashboard: https://dashboard.stripe.com
- Stripe Docs: https://stripe.com/docs
- Django Docs: https://docs.djangoproject.com
- Test Cards: https://stripe.com/docs/testing

---

## 📞 Troubleshooting

**"Invalid API Key"**
→ Check keys in dashboard, use test keys (pk_test_, sk_test_)

**"ModuleNotFoundError: stripe"**
→ `pip install stripe`

**Payment not processing**
→ Check PaymentLog in admin for errors

**Webhook not working**
→ Configure in Stripe dashboard, verify signing secret

---

## 🎯 Next Steps

1. Add your Stripe keys
2. Create subscription plans
3. Test payment flow
4. Protect features with `@require_premium`
5. Deploy to production

---

## ✨ You're All Set!

Your premium subscription system is ready to go. Start protecting features and accepting payments! 💰
