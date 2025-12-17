from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserProfile
from datetime import date
import random


class Command(BaseCommand):
    help = 'Creates 20 dummy users for testing pagination'

    def handle(self, *args, **options):
        first_names = [
            'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'Chris', 'Lisa',
            'James', 'Anna', 'Robert', 'Maria', 'William', 'Emma', 'Joseph', 'Olivia',
            'Daniel', 'Sophia', 'Matthew', 'Isabella', 'Andrew', 'Mia', 'Ryan', 'Charlotte'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White'
        ]
        
        activity_levels = ['sedentary', 'light', 'moderate', 'very', 'super']
        goals = ['lose', 'maintain', 'gain']
        
        created_count = 0
        
        for i in range(1, 21):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"testuser{i}"
            email = f"testuser{i}@example.com"
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User {username} already exists, skipping...'))
                continue
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123',
                first_name=first_name,
                last_name=last_name
            )
            
            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.date_of_birth = date(
                random.randint(1980, 2000),
                random.randint(1, 12),
                random.randint(1, 28)
            )
            profile.height = random.randint(150, 190)
            profile.weight = random.randint(50, 100)
            profile.activity_level = random.choice(activity_levels)
            profile.weight_goal = random.choice(goals)
            profile.daily_calorie_goal = random.randint(1500, 2500)
            profile.is_premium = random.choice([True, False])
            profile.save()
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created user: {username} ({first_name} {last_name})'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} dummy users!'))
        self.stdout.write(self.style.NOTICE('All users have password: testpass123'))
