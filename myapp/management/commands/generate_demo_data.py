from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import (
    Food, Consume, UserProfile, WeightLog, MealPlan, MealPlanItem,
    UserStreak, Achievement, UserAchievement
)
from django.utils import timezone
from datetime import timedelta, datetime
import random

class Command(BaseCommand):
    help = 'Generate demo data to showcase the app'

    def handle(self, *args, **options):
        # Get the first user (or create demo user)
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='demo_user',
                email='demo@example.com',
                password='demo123',
                first_name='John',
                last_name='Doe'
            )
            self.stdout.write(self.style.SUCCESS(f"Created demo user: {user.username}"))
        
        self.stdout.write(f"Generating data for user: {user.username}")
        
        # ===== 1. ADD MORE FOODS =====
        foods_data = [
            # Breakfast items
            {'name': 'Scrambled Eggs', 'calories': 147, 'protein': 10, 'carbs': 2, 'fats': 11, 'category': 'Breakfast'},
            {'name': 'Avocado Toast', 'calories': 280, 'protein': 7, 'carbs': 24, 'fats': 18, 'category': 'Breakfast'},
            {'name': 'Greek Yogurt with Berries', 'calories': 180, 'protein': 15, 'carbs': 20, 'fats': 5, 'category': 'Breakfast'},
            {'name': 'Protein Pancakes', 'calories': 320, 'protein': 25, 'carbs': 35, 'fats': 8, 'category': 'Breakfast'},
            {'name': 'Overnight Oats', 'calories': 350, 'protein': 12, 'carbs': 55, 'fats': 9, 'category': 'Breakfast'},
            {'name': 'Smoothie Bowl', 'calories': 280, 'protein': 8, 'carbs': 45, 'fats': 7, 'category': 'Breakfast'},
            
            # Lunch items
            {'name': 'Grilled Chicken Salad', 'calories': 350, 'protein': 35, 'carbs': 15, 'fats': 18, 'category': 'Lunch'},
            {'name': 'Turkey Sandwich', 'calories': 420, 'protein': 28, 'carbs': 45, 'fats': 14, 'category': 'Lunch'},
            {'name': 'Quinoa Buddha Bowl', 'calories': 480, 'protein': 18, 'carbs': 62, 'fats': 16, 'category': 'Lunch'},
            {'name': 'Tuna Wrap', 'calories': 380, 'protein': 30, 'carbs': 35, 'fats': 12, 'category': 'Lunch'},
            {'name': 'Chicken Caesar Wrap', 'calories': 450, 'protein': 32, 'carbs': 38, 'fats': 18, 'category': 'Lunch'},
            {'name': 'Mediterranean Salad', 'calories': 320, 'protein': 12, 'carbs': 25, 'fats': 20, 'category': 'Lunch'},
            
            # Dinner items
            {'name': 'Grilled Salmon', 'calories': 367, 'protein': 40, 'carbs': 0, 'fats': 22, 'category': 'Dinner'},
            {'name': 'Chicken Stir Fry', 'calories': 420, 'protein': 35, 'carbs': 30, 'fats': 18, 'category': 'Dinner'},
            {'name': 'Beef Tacos', 'calories': 520, 'protein': 28, 'carbs': 42, 'fats': 26, 'category': 'Dinner'},
            {'name': 'Vegetable Curry', 'calories': 380, 'protein': 12, 'carbs': 45, 'fats': 16, 'category': 'Dinner'},
            {'name': 'Pasta Primavera', 'calories': 450, 'protein': 15, 'carbs': 65, 'fats': 14, 'category': 'Dinner'},
            {'name': 'Grilled Steak', 'calories': 580, 'protein': 52, 'carbs': 0, 'fats': 40, 'category': 'Dinner'},
            {'name': 'Shrimp Scampi', 'calories': 420, 'protein': 28, 'carbs': 35, 'fats': 18, 'category': 'Dinner'},
            
            # Snacks
            {'name': 'Protein Bar', 'calories': 200, 'protein': 20, 'carbs': 22, 'fats': 7, 'category': 'Snack'},
            {'name': 'Mixed Nuts', 'calories': 180, 'protein': 5, 'carbs': 6, 'fats': 16, 'category': 'Snack'},
            {'name': 'Apple with Peanut Butter', 'calories': 250, 'protein': 7, 'carbs': 30, 'fats': 14, 'category': 'Snack'},
            {'name': 'Hummus with Veggies', 'calories': 180, 'protein': 6, 'carbs': 18, 'fats': 10, 'category': 'Snack'},
            {'name': 'Cottage Cheese', 'calories': 120, 'protein': 14, 'carbs': 5, 'fats': 5, 'category': 'Snack'},
            {'name': 'Dark Chocolate', 'calories': 170, 'protein': 2, 'carbs': 13, 'fats': 12, 'category': 'Snack'},
            {'name': 'Rice Cakes', 'calories': 70, 'protein': 2, 'carbs': 14, 'fats': 0.5, 'category': 'Snack'},
            
            # Beverages
            {'name': 'Protein Shake', 'calories': 180, 'protein': 30, 'carbs': 8, 'fats': 3, 'category': 'Beverage'},
            {'name': 'Green Smoothie', 'calories': 220, 'protein': 5, 'carbs': 40, 'fats': 4, 'category': 'Beverage'},
            {'name': 'Iced Coffee', 'calories': 80, 'protein': 1, 'carbs': 12, 'fats': 2, 'category': 'Beverage'},
        ]
        
        created_foods = 0
        for food_data in foods_data:
            food, created = Food.objects.get_or_create(
                name=food_data['name'],
                defaults={
                    'calories': food_data['calories'],
                    'protein': food_data['protein'],
                    'carbs': food_data['carbs'],
                    'fats': food_data['fats'],
                    'category': food_data['category'],
                    'fiber': random.uniform(1, 8),
                    'sugar': random.uniform(2, 15),
                }
            )
            if created:
                created_foods += 1
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {created_foods} new foods"))
        
        # ===== 2. GENERATE HISTORICAL FOOD LOGS (Last 30 days) =====
        all_foods = list(Food.objects.all())
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        today = timezone.now().date()
        
        # Delete old consume data for clean demo
        Consume.objects.filter(user=user).delete()
        
        consume_count = 0
        for days_ago in range(30):
            log_date = today - timedelta(days=days_ago)
            
            # Random number of meals per day (3-5)
            num_meals = random.randint(3, 5)
            
            for meal_type in random.sample(meal_types, min(num_meals, 4)):
                # 1-2 foods per meal
                foods_in_meal = random.sample(all_foods, random.randint(1, 2))
                for food in foods_in_meal:
                    Consume.objects.create(
                        user=user,
                        food_consumed=food,
                        date_consumed=log_date,
                        meal_type=meal_type,
                        servings=round(random.uniform(0.5, 2.0), 1)
                    )
                    consume_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {consume_count} food log entries (30 days)"))
        
        # ===== 3. GENERATE WEIGHT LOGS (Last 60 days) =====
        WeightLog.objects.filter(user=user).delete()
        
        # Get user profile weight or default
        user_profile = user.userprofile
        starting_weight = user_profile.weight if user_profile.weight else 85.0
        
        # Simulate weight loss journey
        weight_logs_count = 0
        current_weight = starting_weight + 5  # Started 5kg heavier
        
        for days_ago in range(60, -1, -3):  # Every 3 days
            log_date = today - timedelta(days=days_ago)
            
            # Gradual weight loss with some fluctuation
            weight_change = random.uniform(-0.3, 0.1)  # Trending down
            current_weight = max(current_weight + weight_change, starting_weight - 3)
            
            WeightLog.objects.create(
                user=user,
                weight=round(current_weight, 1),
                date=log_date,
                notes=random.choice([
                    'Feeling great!',
                    'Good workout today',
                    'Stayed on track with diet',
                    'Had a cheat meal yesterday',
                    'Drinking more water',
                    'Sleep was good',
                    '',
                ])
            )
            weight_logs_count += 1
        
        # Update profile with current weight
        user_profile.weight = round(current_weight, 1)
        user_profile.save()
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {weight_logs_count} weight log entries"))
        
        # ===== 4. UPDATE STREAK =====
        streak, created = UserStreak.objects.get_or_create(user=user)
        streak.current_streak = 14  # 2 week streak
        streak.longest_streak = 21  # 3 weeks was the record
        streak.total_days_logged = 45
        streak.last_log_date = today
        streak.save()
        
        self.stdout.write(self.style.SUCCESS(f"✅ Set streak to {streak.current_streak} days"))
        
        # ===== 5. UNLOCK ACHIEVEMENTS =====
        UserAchievement.objects.filter(user=user).delete()
        
        achievements_to_unlock = [
            'First Step',
            'Week Warrior',
            'Fortnight Fighter',
            'Food Explorer',
            'Weight Watcher',
            'Balanced Diet',
        ]
        
        # Add Premium Pioneer if user is premium
        if user_profile.is_premium_active():
            achievements_to_unlock.append('Premium Pioneer')
        
        unlocked = 0
        for ach_name in achievements_to_unlock:
            achievement = Achievement.objects.filter(name=ach_name).first()
            if achievement:
                ua, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    # Set earned_at to different times for variety
                    ua.earned_at = timezone.now() - timedelta(days=random.randint(1, 20))
                    ua.save()
                    unlocked += 1
        
        self.stdout.write(self.style.SUCCESS(f"✅ Unlocked {unlocked} achievements"))
        
        # ===== 6. CREATE MEAL PLANS =====
        # Clear old meal plans
        MealPlan.objects.filter(user=user).delete()
        
        meal_plan_count = 0
        for days_ahead in range(7):  # Next 7 days
            plan_date = today + timedelta(days=days_ahead)
            
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                meal_plan, _ = MealPlan.objects.get_or_create(
                    user=user,
                    date=plan_date,
                    meal_type=meal_type
                )
                
                # Add 1-3 foods to each meal plan
                foods_for_plan = random.sample(all_foods, random.randint(1, 3))
                for food in foods_for_plan:
                    MealPlanItem.objects.get_or_create(
                        meal_plan=meal_plan,
                        food=food,
                        defaults={'servings': round(random.uniform(0.5, 1.5), 1)}
                    )
                meal_plan_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {meal_plan_count} meal plans"))
        
        # ===== SUMMARY =====
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("🎉 DEMO DATA GENERATION COMPLETE!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"📊 Total Foods: {Food.objects.count()}")
        self.stdout.write(f"🍽️  Food Logs: {Consume.objects.filter(user=user).count()}")
        self.stdout.write(f"⚖️  Weight Logs: {WeightLog.objects.filter(user=user).count()}")
        self.stdout.write(f"🔥 Current Streak: {streak.current_streak} days")
        self.stdout.write(f"🏆 Achievements Unlocked: {UserAchievement.objects.filter(user=user).count()}")
        self.stdout.write(f"📅 Meal Plans: {MealPlan.objects.filter(user=user).count()}")
        self.stdout.write(self.style.SUCCESS("=" * 50))
