"""
Setup script to create the $10 Premium Meal Planner subscription plan
Run this with: python manage.py shell < setup_subscription_plan.py
"""

from myapp.models import SubscriptionPlan

# Create or update the $10 monthly subscription plan
plan, created = SubscriptionPlan.objects.update_or_create(
    name="Premium Monthly - Meal Planner",
    defaults={
        'description': 'Access to Smart Meal Planner and all premium features including meal planning, shopping lists, and nutrition tracking.',
        'duration': 'monthly',
        'price': 10.00,
        'duration_days': 30,
        'is_active': True,
    }
)

if created:
    print(f"✅ Created new subscription plan: {plan.name}")
else:
    print(f"✅ Updated existing subscription plan: {plan.name}")

print(f"   Price: ${plan.price}")
print(f"   Duration: {plan.duration_days} days")
print(f"   Status: {'Active' if plan.is_active else 'Inactive'}")
print(f"\n🎉 Subscription plan is ready!")
print(f"   Users can now subscribe at: http://localhost:8000/subscription/plans/")
