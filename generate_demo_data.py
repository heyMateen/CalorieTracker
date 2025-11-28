#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

# Now import Django models
from django.contrib.auth.models import User
from myapp.models import Food, Consume, WeightLog, UserProfile
from datetime import datetime, timedelta
from django.utils import timezone
import random

# Get or create admin user
try:
    admin_user = User.objects.get(username='admin')
    print(f"✅ Found admin user: {admin_user.username}")
except User.DoesNotExist:
    print("❌ Admin user not found. Creating admin user...")
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )
    print(f"✅ Created admin user: {admin_user.username}")

# Ensure admin has a profile
if not hasattr(admin_user, 'userprofile'):
    UserProfile.objects.create(
        user=admin_user,
        height=175,
        daily_calorie_goal=2200,
        activity_level='moderate',
        weight_goal='maintain'
    )
    print("✅ Created user profile for admin")

# Get some food items
foods = list(Food.objects.all()[:20])
if not foods:
    print("⚠️  No food items found in database. Please add some foods first.")
    sys.exit(1)

print(f"📊 Using {len(foods)} food items for demo data")

# Generate data for the last 30 days
end_date = timezone.now().date()
start_date = end_date - timedelta(days=30)

print(f"\n🗓️  Generating data from {start_date} to {end_date}")

# Delete existing data for admin user to start fresh
Consume.objects.filter(user=admin_user).delete()
WeightLog.objects.filter(user=admin_user).delete()
print("🧹 Cleared existing data for admin user")

# Generate weight history (gradual decrease from 80kg to 76kg over 30 days)
print("\n⚖️  Generating weight history...")
current_weight = 80.0
weight_count = 0

for i in range(31):
    date = start_date + timedelta(days=i)
    
    # Add some realistic variation
    daily_change = random.uniform(-0.3, 0.1)  # Slight downward trend
    current_weight += daily_change
    current_weight = max(75, min(82, current_weight))  # Keep in realistic range
    
    # Log weight every 2-3 days
    if i % 2 == 0 or i == 0 or i == 30:
        WeightLog.objects.create(
            user=admin_user,
            weight=round(current_weight, 1),
            date=date,
            notes=f"Day {i+1} weight check"
        )
        weight_count += 1

print(f"✅ Created {weight_count} weight log entries")

# Generate calorie consumption history
print("\n🍽️  Generating calorie consumption history...")
meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
consume_count = 0

for i in range(31):
    date = start_date + timedelta(days=i)
    
    # Target calories with some variation (1800-2400 range)
    daily_target = random.randint(1800, 2400)
    daily_calories = 0
    
    # Add meals for each day
    for meal_type in meal_types:
        # Number of items per meal
        num_items = random.randint(1, 3) if meal_type != 'snack' else random.randint(0, 2)
        
        for _ in range(num_items):
            food = random.choice(foods)
            servings = round(random.uniform(0.5, 2.0), 1)
            
            # Create consume entry
            Consume.objects.create(
                user=admin_user,
                food_consumed=food,
                meal_type=meal_type,
                servings=servings,
                date_consumed=date,
                time_consumed=timezone.now().time()
            )
            
            daily_calories += food.calories * servings
            consume_count += 1
            
            # Stop if we've reached daily target
            if daily_calories >= daily_target:
                break
        
        if daily_calories >= daily_target:
            break

print(f"✅ Created {consume_count} food consumption entries")

# Calculate statistics
total_calories = Consume.objects.filter(user=admin_user).count()
total_weight_logs = WeightLog.objects.filter(user=admin_user).count()
first_weight = WeightLog.objects.filter(user=admin_user).order_by('date').first()
last_weight = WeightLog.objects.filter(user=admin_user).order_by('date').last()

print("\n" + "="*60)
print("📈 DEMO DATA GENERATION COMPLETE!")
print("="*60)
print(f"👤 User: {admin_user.username}")
print(f"📅 Date Range: {start_date} to {end_date} (30 days)")
print(f"🍽️  Total Meals Logged: {total_calories}")
print(f"⚖️  Total Weight Logs: {total_weight_logs}")
if first_weight and last_weight:
    weight_change = last_weight.weight - first_weight.weight
    print(f"📊 Weight Change: {first_weight.weight}kg → {last_weight.weight}kg ({weight_change:+.1f}kg)")
print("\n💡 Login credentials:")
print("   Username: admin")
print("   Password: admin123")
print("\n🌐 View dashboard at: http://localhost:8000/dashboard/")
print("="*60)
