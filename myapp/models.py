from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

# Choices Constants
MEAL_TYPE_CHOICES = [
    ('breakfast', 'Breakfast'),
    ('lunch', 'Lunch'),
    ('dinner', 'Dinner'),
    ('snack', 'Snack')
]

class Food(models.Model):
    name = models.CharField(max_length=100)
    carbs = models.FloatField()
    protein = models.FloatField()
    fats = models.FloatField()
    calories = models.IntegerField()
    fiber = models.FloatField(default=0)
    sugar = models.FloatField(default=0)
    serving_size = models.CharField(max_length=50, default='100g')
    category = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Food'
        verbose_name_plural = 'Foods'

class UserProfile(models.Model):
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly active (light exercise/sports 1-3 days/week)'),
        ('moderate', 'Moderately active (moderate exercise/sports 3-5 days/week)'),
        ('very', 'Very active (hard exercise/sports 6-7 days/week)'),
        ('super', 'Super active (very hard exercise & physical job or training twice per day)')
    ]

    GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)
    height = models.FloatField(help_text="Height in cm", null=True, blank=True)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='moderate')
    weight_goal = models.CharField(max_length=10, choices=GOAL_CHOICES, default='maintain')
    daily_calorie_goal = models.IntegerField(default=2000)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    def calculate_bmi(self, weight):
        if self.height and weight:
            height_m = self.height / 100  # Convert cm to m
            bmi = weight / (height_m * height_m)
            return round(bmi, 1)
        return None

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.FloatField(help_text="Weight in kg")
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']

class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    servings = models.PositiveIntegerField(default=1)
    preparation_time = models.PositiveIntegerField(help_text="Time in minutes")
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_nutrition(self):
        totals = {
            'calories': 0,
            'carbs': 0,
            'protein': 0,
            'fats': 0
        }
        for ingredient in self.recipeingredient_set.all():
            totals['calories'] += ingredient.food.calories * (ingredient.quantity / 100)
            totals['carbs'] += ingredient.food.carbs * (ingredient.quantity / 100)
            totals['protein'] += ingredient.food.protein * (ingredient.quantity / 100)
            totals['fats'] += ingredient.food.fats * (ingredient.quantity / 100)
        return totals

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.FloatField(help_text="Quantity in grams")
    notes = models.CharField(max_length=100, blank=True)

class MealPlan(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('morning_snack', 'Morning Snack'),
        ('lunch', 'Lunch'),
        ('afternoon_snack', 'Afternoon Snack'),
        ('dinner', 'Dinner'),
        ('evening_snack', 'Evening Snack')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    foods = models.ManyToManyField(Food, through='MealPlanItem')
    recipes = models.ManyToManyField(Recipe, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'meal_type']
        unique_together = ['user', 'date', 'meal_type']

class MealPlanItem(models.Model):
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    servings = models.FloatField(default=1.0)

class FavoriteFood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'food']

class NutritionGoal(models.Model):
    GOAL_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    goal_type = models.CharField(max_length=10, choices=GOAL_TYPES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    target_calories = models.IntegerField(null=True, blank=True)
    target_carbs = models.FloatField(null=True, blank=True)
    target_protein = models.FloatField(null=True, blank=True)
    target_fats = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def get_progress(self, date=None):
        if not date:
            date = timezone.now().date()
        
        # Calculate consumption for the period
        if self.goal_type == 'daily':
            start = date
            end = date
        elif self.goal_type == 'weekly':
            start = date - timedelta(days=date.weekday())
            end = start + timedelta(days=6)
        else:  # monthly
            start = date.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
        consumption = Consume.objects.filter(
            user=self.user,
            date_consumed__range=[start, end]
        ).aggregate(
            total_calories=Sum('food_consumed__calories'),
            total_carbs=Sum('food_consumed__carbs'),
            total_protein=Sum('food_consumed__protein'),
            total_fats=Sum('food_consumed__fats')
        )
        
        return {
            'period': {'start': start, 'end': end},
            'consumed': consumption,
            'remaining': {
                'calories': (self.target_calories or 0) - (consumption['total_calories'] or 0),
                'carbs': (self.target_carbs or 0) - (consumption['total_carbs'] or 0),
                'protein': (self.target_protein or 0) - (consumption['total_protein'] or 0),
                'fats': (self.target_fats or 0) - (consumption['total_fats'] or 0)
            }
        }

class Consume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_consumed = models.ForeignKey(Food, on_delete=models.CASCADE)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, default='snack')
    servings = models.FloatField(default=1.0)
    date_consumed = models.DateField(default=timezone.now)
    time_consumed = models.TimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_consumed', '-time_consumed']