from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.FloatField(help_text="Weight in kg")
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']

class Food(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack')
    ]

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

class Consume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_consumed = models.ForeignKey(Food, on_delete=models.CASCADE)
    meal_type = models.CharField(max_length=20, choices=Food.MEAL_TYPE_CHOICES, default='snack')
    servings = models.FloatField(default=1.0)
    date_consumed = models.DateField(default=timezone.now)
    time_consumed = models.TimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_consumed', '-time_consumed']
