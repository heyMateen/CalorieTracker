from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Consume, UserStreak, Achievement, UserAchievement

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        # Also create streak tracker for new users
        UserStreak.objects.create(user=instance)
    else:
        # Only save existing profile, don't create
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()


@receiver(post_save, sender=Consume)
def update_streak_on_consume(sender, instance, created, **kwargs):
    """Update user streak when they log food"""
    if created:
        # Get or create streak
        streak, _ = UserStreak.objects.get_or_create(user=instance.user)
        streak.update_streak(instance.date_consumed)
        
        # Check for achievements
        check_achievements(instance.user, streak)


def check_achievements(user, streak):
    """Check and award achievements to user"""
    # Check streak achievements
    streak_achievements = Achievement.objects.filter(achievement_type='streak')
    for achievement in streak_achievements:
        if streak.current_streak >= achievement.requirement_value:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
    
    # Check logging achievements (first meal)
    if Consume.objects.filter(user=user).count() == 1:
        first_step = Achievement.objects.filter(name='First Step').first()
        if first_step:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=first_step
            )
    
    # Check food explorer (10 different foods)
    unique_foods = Consume.objects.filter(user=user).values('food_consumed').distinct().count()
    if unique_foods >= 10:
        explorer = Achievement.objects.filter(name='Food Explorer').first()
        if explorer:
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=explorer
            )