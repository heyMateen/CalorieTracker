"""
Script to initialize sample subscription plans in the database
Run with: python manage.py shell < init_plans.py
Or inside Django shell: exec(open('myapp/init_plans.py').read())
"""

from myapp.models import SubscriptionPlan

# Check if plans already exist
if SubscriptionPlan.objects.exists():
    print("⚠️  Subscription plans already exist. Skipping initialization.")
    print("Existing plans:")
    for plan in SubscriptionPlan.objects.all():
        print(f"  - {plan.name}: ${plan.price}")
else:
    print("📋 Creating sample subscription plans...")
    
    plans = [
        {
            'name': 'Premium Monthly',
            'description': 'One month of unlimited premium access to all features',
            'duration': 'monthly',
            'price': 9.99,
            'duration_days': 30,
        },
        {
            'name': 'Premium Quarterly',
            'description': 'Three months of premium access with 17% savings',
            'duration': 'quarterly',
            'price': 24.99,
            'duration_days': 90,
        },
        {
            'name': 'Premium Yearly',
            'description': 'Full year of premium access with 25% savings',
            'duration': 'yearly',
            'price': 89.99,
            'duration_days': 365,
        },
    ]
    
    created_plans = []
    for plan_data in plans:
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=plan_data['name'],
            defaults={
                'description': plan_data['description'],
                'duration': plan_data['duration'],
                'price': plan_data['price'],
                'duration_days': plan_data['duration_days'],
                'is_active': True,
            }
        )
        
        if created:
            created_plans.append(plan)
            print(f"✅ Created: {plan.name} - ${plan.price}")
        else:
            print(f"ℹ️  Already exists: {plan.name}")
    
    if created_plans:
        print(f"\n✨ Successfully created {len(created_plans)} subscription plans!")
        print("\n📝 Next steps:")
        print("1. Go to Django admin: /admin/")
        print("2. Go to 'Subscription Plans'")
        print("3. (Optional) Update stripe_price_id for each plan if you have them")
        print("4. Test the subscription flow at /subscription/plans/")
    else:
        print("ℹ️  All plans already exist.")

# Display summary
print("\n" + "="*50)
print("Current Subscription Plans:")
print("="*50)
for plan in SubscriptionPlan.objects.filter(is_active=True):
    print(f"\n📦 {plan.name}")
    print(f"   Price: ${plan.price}")
    print(f"   Duration: {plan.duration_days} days")
    print(f"   Description: {plan.description}")
    print(f"   Active: {plan.is_active}")
