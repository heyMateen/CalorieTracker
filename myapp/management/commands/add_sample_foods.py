from django.core.management.base import BaseCommand
from myapp.models import Food

class Command(BaseCommand):
    help = 'Add sample food items to the database'

    def handle(self, *args, **kwargs):
        foods = [
            {'name': 'Banana', 'carbs': 23, 'protein': 1.1, 'fats': 0.3, 'calories': 89},
            {'name': 'Apple', 'carbs': 25, 'protein': 0.5, 'fats': 0.3, 'calories': 95},
            {'name': 'Chicken Breast', 'carbs': 0, 'protein': 31, 'fats': 3.6, 'calories': 165},
            {'name': 'Egg', 'carbs': 0.6, 'protein': 6.3, 'fats': 5, 'calories': 74},
            {'name': 'Rice', 'carbs': 45, 'protein': 4.3, 'fats': 0.4, 'calories': 206},
        ]

        for food_data in foods:
            Food.objects.get_or_create(
                name=food_data['name'],
                defaults={
                    'carbs': food_data['carbs'],
                    'protein': food_data['protein'],
                    'fats': food_data['fats'],
                    'calories': food_data['calories'],
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully added sample food items'))