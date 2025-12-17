from django.core.management.base import BaseCommand
from myapp.models import Achievement

class Command(BaseCommand):
    help = 'Setup initial achievements'

    def handle(self, *args, **options):
        achievements = [
            # Streak Achievements
            {
                'name': 'First Step',
                'description': 'Log your first meal',
                'icon': 'fa-shoe-prints',
                'color': '#4CAF50',
                'achievement_type': 'logging',
                'requirement_value': 1,
                'points': 10
            },
            {
                'name': 'Week Warrior',
                'description': 'Maintain a 7-day logging streak',
                'icon': 'fa-fire',
                'color': '#FF5722',
                'achievement_type': 'streak',
                'requirement_value': 7,
                'points': 50
            },
            {
                'name': 'Fortnight Fighter',
                'description': 'Maintain a 14-day logging streak',
                'icon': 'fa-fire-flame-curved',
                'color': '#FF9800',
                'achievement_type': 'streak',
                'requirement_value': 14,
                'points': 100
            },
            {
                'name': 'Month Master',
                'description': 'Maintain a 30-day logging streak',
                'icon': 'fa-medal',
                'color': '#FFD700',
                'achievement_type': 'streak',
                'requirement_value': 30,
                'points': 200
            },
            # Nutrition Achievements
            {
                'name': 'Balanced Diet',
                'description': 'Hit your calorie goal 5 times',
                'icon': 'fa-scale-balanced',
                'color': '#2196F3',
                'achievement_type': 'nutrition',
                'requirement_value': 5,
                'points': 30
            },
            {
                'name': 'Protein Power',
                'description': 'Log 100g+ protein in a day',
                'icon': 'fa-dumbbell',
                'color': '#9C27B0',
                'achievement_type': 'nutrition',
                'requirement_value': 100,
                'points': 40
            },
            # Logging Achievements
            {
                'name': 'Food Explorer',
                'description': 'Log 10 different foods',
                'icon': 'fa-compass',
                'color': '#00BCD4',
                'achievement_type': 'logging',
                'requirement_value': 10,
                'points': 25
            },
            {
                'name': 'Meal Prep Pro',
                'description': 'Create 10 meal plans',
                'icon': 'fa-calendar-check',
                'color': '#8BC34A',
                'achievement_type': 'logging',
                'requirement_value': 10,
                'points': 35
            },
            # Weight Achievements
            {
                'name': 'Weight Watcher',
                'description': 'Log your weight 10 times',
                'icon': 'fa-weight-scale',
                'color': '#607D8B',
                'achievement_type': 'weight',
                'requirement_value': 10,
                'points': 30
            },
            {
                'name': 'Transformation',
                'description': 'Reach your weight goal',
                'icon': 'fa-trophy',
                'color': '#E91E63',
                'achievement_type': 'weight',
                'requirement_value': 1,
                'points': 100
            },
            # Special Achievements
            {
                'name': 'Early Bird',
                'description': 'Log breakfast before 8 AM',
                'icon': 'fa-sun',
                'color': '#FFEB3B',
                'achievement_type': 'special',
                'requirement_value': 1,
                'points': 15
            },
            {
                'name': 'Premium Pioneer',
                'description': 'Subscribe to Premium',
                'icon': 'fa-crown',
                'color': '#FFD700',
                'achievement_type': 'special',
                'requirement_value': 1,
                'points': 50
            },
        ]

        created_count = 0
        for ach_data in achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=ach_data['name'],
                defaults=ach_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created achievement: {achievement.name}"))
            else:
                self.stdout.write(f"Achievement already exists: {achievement.name}")

        self.stdout.write(self.style.SUCCESS(f"\nTotal achievements created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Total achievements in database: {Achievement.objects.count()}"))
