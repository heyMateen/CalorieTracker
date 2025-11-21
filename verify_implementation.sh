#!/usr/bin/env bash
# Verification Script for Premium Subscription Implementation
# Run: bash verify_implementation.sh

echo "🔍 CalorieTracker Premium Integration - Verification"
echo "=================================================="
echo ""

# Check Python files
echo "📄 Checking Python Files..."
python_files=(
    "myapp/subscription.py"
    "myapp/views.py"
    "myapp/models.py"
    "myapp/admin.py"
    "myapp/init_plans.py"
    "mysite/settings.py"
    "mysite/urls.py"
)

for file in "${python_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
    fi
done

echo ""
echo "📄 Checking Template Files..."
template_files=(
    "myapp/templates/myapp/subscription_plans.html"
    "myapp/templates/myapp/subscription_status.html"
    "myapp/templates/myapp/cancel_subscription.html"
)

for file in "${template_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
    fi
done

echo ""
echo "📚 Checking Documentation Files..."
doc_files=(
    "README_PREMIUM.md"
    "QUICK_START.md"
    "STRIPE_SETUP.md"
    "PREMIUM_FEATURES_EXAMPLES.md"
    "IMPLEMENTATION_CHECKLIST.md"
    "ARCHITECTURE.md"
    "CHANGES.md"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ⚠️  $file (MISSING)"
    fi
done

echo ""
echo "📦 Checking Dependencies..."
if grep -q "stripe" requirements.txt; then
    echo "  ✅ stripe package in requirements.txt"
else
    echo "  ❌ stripe package NOT in requirements.txt"
fi

echo ""
echo "🗄️  Checking Database..."
python manage.py migrate --check >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Database migrations applied"
else
    echo "  ⚠️  Database needs migration"
fi

echo ""
echo "⚙️  Checking Django Configuration..."

# Check for Stripe settings
if grep -q "STRIPE_PUBLIC_KEY" mysite/settings.py; then
    echo "  ✅ STRIPE_PUBLIC_KEY configured"
else
    echo "  ❌ STRIPE_PUBLIC_KEY NOT configured"
fi

if grep -q "STRIPE_SECRET_KEY" mysite/settings.py; then
    echo "  ✅ STRIPE_SECRET_KEY configured"
else
    echo "  ❌ STRIPE_SECRET_KEY NOT configured"
fi

if grep -q "STRIPE_WEBHOOK_SECRET" mysite/settings.py; then
    echo "  ✅ STRIPE_WEBHOOK_SECRET configured"
else
    echo "  ❌ STRIPE_WEBHOOK_SECRET NOT configured"
fi

echo ""
echo "🔗 Checking URL Routes..."

if grep -q "subscription_plans" mysite/urls.py; then
    echo "  ✅ /subscription/plans/ route"
else
    echo "  ❌ /subscription/plans/ route MISSING"
fi

if grep -q "create_checkout" mysite/urls.py; then
    echo "  ✅ /subscription/checkout/ route"
else
    echo "  ❌ /subscription/checkout/ route MISSING"
fi

if grep -q "payment_success" mysite/urls.py; then
    echo "  ✅ /subscription/success/ route"
else
    echo "  ❌ /subscription/success/ route MISSING"
fi

if grep -q "subscription_status" mysite/urls.py; then
    echo "  ✅ /subscription/status/ route"
else
    echo "  ❌ /subscription/status/ route MISSING"
fi

if grep -q "stripe_webhook" mysite/urls.py; then
    echo "  ✅ /stripe/webhook/ route"
else
    echo "  ❌ /stripe/webhook/ route MISSING"
fi

echo ""
echo "📊 Checking Models..."

if grep -q "class SubscriptionPlan" myapp/models.py; then
    echo "  ✅ SubscriptionPlan model"
else
    echo "  ❌ SubscriptionPlan model MISSING"
fi

if grep -q "class SubscriptionPurchase" myapp/models.py; then
    echo "  ✅ SubscriptionPurchase model"
else
    echo "  ❌ SubscriptionPurchase model MISSING"
fi

if grep -q "class PaymentLog" myapp/models.py; then
    echo "  ✅ PaymentLog model"
else
    echo "  ❌ PaymentLog model MISSING"
fi

if grep -q "is_premium_active" myapp/models.py; then
    echo "  ✅ UserProfile.is_premium_active() method"
else
    echo "  ❌ UserProfile.is_premium_active() method MISSING"
fi

echo ""
echo "✨ Checking Views..."

if grep -q "def subscription_plans" myapp/views.py; then
    echo "  ✅ subscription_plans view"
else
    echo "  ❌ subscription_plans view MISSING"
fi

if grep -q "def create_checkout" myapp/views.py; then
    echo "  ✅ create_checkout view"
else
    echo "  ❌ create_checkout view MISSING"
fi

if grep -q "def payment_success" myapp/views.py; then
    echo "  ✅ payment_success view"
else
    echo "  ❌ payment_success view MISSING"
fi

if grep -q "def stripe_webhook" myapp/views.py; then
    echo "  ✅ stripe_webhook view"
else
    echo "  ❌ stripe_webhook view MISSING"
fi

if grep -q "def require_premium" myapp/subscription.py; then
    echo "  ✅ require_premium decorator"
else
    echo "  ❌ require_premium decorator MISSING"
fi

echo ""
echo "=================================================="
echo "✅ Verification Complete!"
echo ""
echo "Next Steps:"
echo "1. Add Stripe keys to mysite/settings.py"
echo "2. Run: python manage.py shell"
echo "3. Execute: exec(open('myapp/init_plans.py').read())"
echo "4. Visit: http://localhost:8000/subscription/plans/"
echo ""
echo "📚 Start with README_PREMIUM.md for full documentation"
echo "=================================================="
