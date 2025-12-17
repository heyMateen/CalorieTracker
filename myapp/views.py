from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from .models import Food, Consume, UserProfile, WeightLog, MEAL_TYPE_CHOICES, SubscriptionPlan, SubscriptionPurchase, PaymentLog, MealPlan, MealPlanItem, UserStreak, Achievement, UserAchievement
from .forms import SignUpForm
from django.db.models.functions import TruncDate
from .subscription import (
    create_stripe_checkout_session,
    retrieve_checkout_session,
    process_successful_payment,
    verify_webhook_signature,
    StripePaymentError,
    require_premium
)
from django.conf import settings

logger = logging.getLogger(__name__)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # UserProfile will be created automatically via signals
            # Save phone number to UserProfile
            phone_number = form.cleaned_data.get('phone_number')
            if phone_number:
                user.userprofile.phone_number = phone_number
                user.userprofile.save()
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'registration/signup.html', {
                'form': form
            })
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to your login page

    foods = Food.objects.all()
    
    if request.method == "POST":
        food_consumed = request.POST.get('food_consumed')
        if food_consumed:
            try:
                consume = Food.objects.get(name=food_consumed)
                Consume.objects.create(user=request.user, food_consumed=consume)
                return redirect('index')  # Redirect after successful POST
            except Food.DoesNotExist:
                pass  # Handle the case where the food item doesn't exist
        
    consumed_food = Consume.objects.filter(user=request.user)
    return render(request, 'myapp/index.html', {'foods': foods, 'consumed_food': consumed_food})


def delete_consume(request, id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    consumed_food = Consume.objects.get(id=id)
    # Make sure the user owns this consume object
    if consumed_food.user != request.user:
        return redirect('/')
        
    if request.method == 'POST':
        consumed_food.delete()
        return redirect('/')
    return render(request, 'myapp/delete.html')

@login_required
def dashboard(request):
    user_profile = request.user.userprofile
    today = timezone.now().date()
    
    # Get daily calories and nutrients
    today_consumption = Consume.objects.filter(
        user=request.user,
        date_consumed=today
    ).select_related('food_consumed')
    
    daily_calories = sum(consume.food_consumed.calories * consume.servings for consume in today_consumption)
    daily_carbs = sum(consume.food_consumed.carbs * consume.servings for consume in today_consumption)
    daily_protein = sum(consume.food_consumed.protein * consume.servings for consume in today_consumption)
    daily_fats = sum(consume.food_consumed.fats * consume.servings for consume in today_consumption)
    
    # Calculate calorie percentage
    calorie_percentage = min((daily_calories / user_profile.daily_calorie_goal * 100), 100)
    
    # Check if goal met (for confetti)
    goal_met = daily_calories >= user_profile.daily_calorie_goal * 0.9 and daily_calories <= user_profile.daily_calorie_goal * 1.1
    
    # Get or create user streak
    user_streak, created = UserStreak.objects.get_or_create(user=request.user)
    
    # Get user achievements
    user_achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')[:6]
    total_achievement_points = sum(ua.achievement.points for ua in user_achievements)
    
    # Calculate remaining calories and suggest foods
    remaining_calories = max(0, user_profile.daily_calorie_goal - daily_calories)
    
    # AI Meal Suggestions based on remaining calories
    meal_suggestions = []
    if remaining_calories > 0:
        # Get foods that fit within remaining calories
        suitable_foods = Food.objects.filter(calories__lte=remaining_calories).order_by('?')[:3]
        for food in suitable_foods:
            meal_suggestions.append({
                'food': food,
                'reason': get_suggestion_reason(food, remaining_calories, daily_protein, daily_carbs, daily_fats)
            })
    
    # Motivational quote based on progress
    motivational_data = get_motivational_data(calorie_percentage, user_streak.current_streak)
    
    # Get latest weight and BMI
    # First try to get weight from weight log, otherwise use profile weight
    latest_weight = WeightLog.objects.filter(user=request.user).order_by('-date').first()
    current_weight = latest_weight.weight if latest_weight else user_profile.weight
    current_bmi = user_profile.calculate_bmi(current_weight)
    
    # Determine BMI category
    bmi_category = None
    if current_bmi:
        if current_bmi < 18.5:
            bmi_category = "Underweight"
        elif current_bmi < 25:
            bmi_category = "Normal"
        elif current_bmi < 30:
            bmi_category = "Overweight"
        else:
            bmi_category = "Obese"
    
    # Get weekly average calories
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    weekly_consumption = Consume.objects.filter(
        user=request.user,
        date_consumed__gte=week_ago
    ).values('date_consumed').annotate(
        daily_total=Sum('food_consumed__calories')
    ).order_by('date_consumed')
    
    weekly_avg_calories = sum(day['daily_total'] for day in weekly_consumption) / 7 if weekly_consumption else 0
    
    # Prepare data for charts - show last 14 days for better visualization
    two_weeks_ago = today - timedelta(days=14)
    calorie_history_data = Consume.objects.filter(
        user=request.user,
        date_consumed__gte=two_weeks_ago
    ).values('date_consumed').annotate(
        daily_total=Sum('food_consumed__calories')
    ).order_by('date_consumed')
    
    calorie_history = list(calorie_history_data)
    calorie_history_dates = [entry['date_consumed'].strftime('%b %d') for entry in calorie_history]
    calorie_history_values = [entry['daily_total'] for entry in calorie_history]
    
    # Get weight history - show last 30 days
    weight_history = WeightLog.objects.filter(
        user=request.user,
        date__gte=month_ago
    ).order_by('date')
    weight_history_dates = [entry.date.strftime('%b %d') for entry in weight_history]
    weight_history_values = [entry.weight for entry in weight_history]
    
    # Get meals by type
    daily_meals = {}
    for meal_type, _ in MEAL_TYPE_CHOICES:
        daily_meals[meal_type] = Consume.objects.filter(
            user=request.user,
            date_consumed=today,
            meal_type=meal_type
        ).select_related('food_consumed')
    
    context = {
        'user_profile': user_profile,
        'daily_calories': daily_calories,
        'calorie_percentage': calorie_percentage,
        'latest_weight': latest_weight,
        'current_bmi': current_bmi,
        'bmi_category': bmi_category,
        'weekly_avg_calories': int(weekly_avg_calories),
        'daily_carbs': daily_carbs,
        'daily_protein': daily_protein,
        'daily_fats': daily_fats,
        'calorie_history_dates': calorie_history_dates,
        'calorie_history_values': calorie_history_values,
        'weight_history_dates': weight_history_dates,
        'weight_history_values': weight_history_values,
        'daily_meals': daily_meals,
        'foods': Food.objects.all(),
        'today': today,
        # New stunning features
        'goal_met': goal_met,
        'user_streak': user_streak,
        'user_achievements': user_achievements,
        'total_achievement_points': total_achievement_points,
        'remaining_calories': remaining_calories,
        'meal_suggestions': meal_suggestions,
        'motivational_data': motivational_data,
    }
    
    return render(request, 'myapp/dashboard.html', context)


def get_suggestion_reason(food, remaining_calories, daily_protein, daily_carbs, daily_fats):
    """Generate AI-like reason for food suggestion"""
    reasons = []
    
    if food.protein > 15:
        reasons.append("High in protein 💪")
    if food.calories < 200:
        reasons.append("Low calorie option 🥗")
    if food.fiber > 5 if hasattr(food, 'fiber') and food.fiber else False:
        reasons.append("Rich in fiber 🌾")
    if food.carbs < 20:
        reasons.append("Low carb friendly 🥑")
    
    if not reasons:
        if food.calories <= remaining_calories * 0.3:
            reasons.append("Perfect light snack ✨")
        else:
            reasons.append("Balanced nutrition 🎯")
    
    return reasons[0] if reasons else "Great choice! 👍"


def get_motivational_data(calorie_percentage, streak):
    """Generate motivational message based on progress"""
    import random
    
    if calorie_percentage >= 90 and calorie_percentage <= 110:
        messages = [
            {"emoji": "🎉", "title": "Perfect Balance!", "message": "You've hit your calorie goal today. Amazing work!"},
            {"emoji": "⭐", "title": "Goal Achieved!", "message": "Your dedication is paying off. Keep it up!"},
            {"emoji": "🏆", "title": "Champion!", "message": "You're crushing your nutrition goals today!"},
        ]
    elif calorie_percentage >= 70:
        messages = [
            {"emoji": "💪", "title": "Almost There!", "message": f"Just {100-calorie_percentage:.0f}% more to reach your goal!"},
            {"emoji": "🔥", "title": "Great Progress!", "message": "You're on fire! Keep going!"},
        ]
    elif calorie_percentage >= 40:
        messages = [
            {"emoji": "🌟", "title": "Good Start!", "message": "You're making progress. Time for a healthy meal!"},
            {"emoji": "💫", "title": "Keep Going!", "message": "Every bite counts towards your goal!"},
        ]
    else:
        messages = [
            {"emoji": "🌅", "title": "New Day, New Goals!", "message": "Start your healthy journey today!"},
            {"emoji": "🚀", "title": "Ready to Go!", "message": "Log your first meal to get started!"},
        ]
    
    result = random.choice(messages)
    
    if streak >= 7:
        result["streak_message"] = f"🔥 {streak} day streak! You're unstoppable!"
    elif streak >= 3:
        result["streak_message"] = f"⚡ {streak} days in a row! Keep the momentum!"
    elif streak >= 1:
        result["streak_message"] = f"✨ {streak} day streak started! Build the habit!"
    else:
        result["streak_message"] = "Start your streak today by logging a meal!"
    
    return result

@login_required
def add_meal(request):
    if request.method == 'POST':
        food_id = request.POST.get('food_consumed')
        meal_type = request.POST.get('meal_type')
        servings = float(request.POST.get('servings', 1))
        
        try:
            food = Food.objects.get(id=food_id)
            Consume.objects.create(
                user=request.user,
                food_consumed=food,
                meal_type=meal_type,
                servings=servings,
                date_consumed=timezone.now().date()
            )
            messages.success(request, f'Added {food.name} to your {meal_type}')
        except Food.DoesNotExist:
            messages.error(request, 'Selected food item does not exist')
        except Exception as e:
            messages.error(request, f'Error adding meal: {str(e)}')
            
    return redirect('dashboard')

@login_required
def log_weight(request):
    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight'))
            date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
            notes = request.POST.get('notes', '')
            
            WeightLog.objects.create(
                user=request.user,
                weight=weight,
                date=date,
                notes=notes
            )
            messages.success(request, f'Weight logged successfully: {weight} kg')
        except ValueError:
            messages.error(request, 'Invalid weight value')
        except Exception as e:
            messages.error(request, f'Error logging weight: {str(e)}')
            
    return redirect('dashboard')

@login_required
def edit_profile(request):
    user_profile = request.user.userprofile
    password_form = PasswordChangeForm(request.user)
    
    if request.method == 'POST':
        if 'change_password' in request.POST:
            # Handle Password Change
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password was successfully updated!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            # Handle Profile Update
            # Get form data
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone_number = request.POST.get('phone_number')
            height = request.POST.get('height')
            weight = request.POST.get('weight')
            date_of_birth = request.POST.get('date_of_birth')
            activity_level = request.POST.get('activity_level')
            weight_goal = request.POST.get('weight_goal')
            daily_calorie_goal = request.POST.get('daily_calorie_goal')
            
            # Update User model (Username, Email, First Name, Last Name)
            user = request.user
            if username and username != user.username:
                # Check if username is already taken
                if User.objects.filter(username=username).exclude(id=user.id).exists():
                    messages.error(request, 'Username is already taken.')
                    return redirect('edit_profile')
                user.username = username
            if email: user.email = email
            if first_name: user.first_name = first_name
            if last_name: user.last_name = last_name
            user.save()

            # Update profile
            try:
                # Handle Profile Picture Upload
                if 'profile_picture' in request.FILES:
                    user_profile.profile_picture = request.FILES['profile_picture']
                
                # Update phone number
                if phone_number is not None:
                    user_profile.phone_number = phone_number

                # Store original values
                original_values = {
                    'height': user_profile.height,
                    'weight': user_profile.weight,
                    'date_of_birth': user_profile.date_of_birth,
                    'activity_level': user_profile.activity_level,
                    'weight_goal': user_profile.weight_goal,
                    'daily_calorie_goal': user_profile.daily_calorie_goal
                }
                
                # Set new values
                user_profile.height = float(height) if height else None
                user_profile.weight = float(weight) if weight else None
                user_profile.date_of_birth = date_of_birth if date_of_birth else None
                user_profile.activity_level = activity_level
                user_profile.weight_goal = weight_goal
                user_profile.daily_calorie_goal = int(daily_calorie_goal)
                
                # Check if any values changed (including picture)
                new_values = {
                    'height': user_profile.height,
                    'weight': user_profile.weight,
                    'date_of_birth': user_profile.date_of_birth,
                    'activity_level': user_profile.activity_level,
                    'weight_goal': user_profile.weight_goal,
                    'daily_calorie_goal': user_profile.daily_calorie_goal
                }
                
                if original_values != new_values or 'profile_picture' in request.FILES:
                    user_profile.save()
                    messages.success(request, 'Profile updated successfully!')
                
                return redirect('dashboard')
            except ValueError:
                messages.error(request, 'Please enter valid values.')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
    
    # Get choices for form
    activity_choices = UserProfile.ACTIVITY_CHOICES
    goal_choices = UserProfile.GOAL_CHOICES
    
    context = {
        'user_profile': user_profile,
        'activity_choices': activity_choices,
        'goal_choices': goal_choices,
        'password_form': password_form,
    }
    
    return render(request, 'myapp/edit_profile.html', context)

@login_required
def add_food(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        carbs = request.POST.get('carbs')
        protein = request.POST.get('protein')
        fats = request.POST.get('fats')
        calories = request.POST.get('calories')
        
        try:
            # Check if food item already exists
            if Food.objects.filter(name=name).exists():
                messages.error(request, f'Food item "{name}" already exists.')
            else:
                Food.objects.create(
                    name=name,
                    carbs=carbs,
                    protein=protein,
                    fats=fats,
                    calories=calories
                )
                messages.success(request, f'Food item "{name}" has been added successfully!')
                return redirect('add_food')
        except Exception as e:
            messages.error(request, f'Error adding food item: {str(e)}')
    
    # Get all food items for display
    foods = Food.objects.all().order_by('name')
    return render(request, 'myapp/add_food.html', {'foods': foods})


# ============================================================
# PREMIUM SUBSCRIPTION VIEWS
# ============================================================

@login_required
def subscription_plans(request):
    """
    Display available subscription plans to the user
    """
    # Get all active subscription plans
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('duration_days')
    user_profile = request.user.userprofile
    
    context = {
        'plans': plans,
        'user_premium': user_profile.is_premium_active(),
        'premium_until': user_profile.premium_until,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    return render(request, 'myapp/subscription_plans.html', context)


@login_required
def create_checkout(request, plan_id):
    """
    Create a Stripe checkout session for a subscription plan
    """
    try:
        # Get the subscription plan
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        
        # Create checkout session
        session = create_stripe_checkout_session(request.user, plan)
        
        # Redirect to Stripe checkout
        return redirect(session.url)
    
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, 'Subscription plan not found.')
        return redirect('subscription_plans')
    except StripePaymentError as e:
        messages.error(request, str(e))
        return redirect('subscription_plans')
    except Exception as e:
        logger.error(f"Error creating checkout: {str(e)}")
        messages.error(request, 'An error occurred. Please try again.')
        return redirect('subscription_plans')


@login_required
def payment_success(request):
    """
    Handle successful payment from Stripe
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid session.')
        return redirect('subscription_plans')
    
    try:
        # Retrieve session from Stripe
        session = retrieve_checkout_session(session_id)
        
        # Extract metadata
        user_id = session.metadata.get('user_id')
        plan_id = session.metadata.get('plan_id')
        
        # Process the payment
        if session.payment_status == 'paid':
            subscription_purchase = process_successful_payment(session_id, user_id, plan_id)
            messages.success(
                request,
                f'🎉 Congratulations! You are now a premium member until {subscription_purchase.end_date.strftime("%B %d, %Y")}'
            )
            return redirect('dashboard')
        else:
            messages.error(request, 'Payment was not completed.')
            return redirect('subscription_plans')
    
    except StripePaymentError as e:
        logger.error(f"Payment processing error: {str(e)}")
        messages.error(request, 'An error occurred processing your payment.')
        return redirect('subscription_plans')
    except Exception as e:
        logger.error(f"Unexpected error in payment_success: {str(e)}")
        messages.error(request, 'An unexpected error occurred.')
        return redirect('subscription_plans')


@login_required
def subscription_status(request):
    """
    Display user's current subscription status
    """
    user_profile = request.user.userprofile
    
    # Get user's subscription purchases
    subscriptions = SubscriptionPurchase.objects.filter(user=request.user).order_by('-created_at')
    payment_history = PaymentLog.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'user_profile': user_profile,
        'subscriptions': subscriptions,
        'payment_history': payment_history,
        'is_premium_active': user_profile.is_premium_active(),
    }
    
    return render(request, 'myapp/subscription_status.html', context)


@login_required
def cancel_subscription(request):
    """
    Cancel user's premium subscription
    """
    if request.method == 'POST':
        from .subscription import cancel_subscription as cancel_stripe_subscription
        
        if cancel_stripe_subscription(request.user):
            messages.success(request, 'Your subscription has been cancelled.')
        else:
            messages.error(request, 'Error cancelling subscription. Please contact support.')
        
        return redirect('subscription_status')
    
    return render(request, 'myapp/cancel_subscription.html')


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    
    IMPORTANT: Configure your webhook in Stripe dashboard to point to:
    http://yourdomain.com/stripe/webhook/
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    
    try:
        # Verify webhook signature
        event = verify_webhook_signature(payload, sig_header)
        
        if not event:
            return JsonResponse({'status': 'invalid_signature'}, status=400)
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session['metadata'].get('user_id')
            plan_id = session['metadata'].get('plan_id')
            
            try:
                process_successful_payment(session['id'], user_id, plan_id)
                logger.info(f"Webhook: Processed payment for session {session['id']}")
            except Exception as e:
                logger.error(f"Webhook: Error processing payment: {str(e)}")
                return JsonResponse({'status': 'error'}, status=500)
        
        elif event['type'] == 'payment_intent.succeeded':
            logger.info("Webhook: Payment intent succeeded")
        
        elif event['type'] == 'customer.subscription.deleted':
            logger.info("Webhook: Subscription deleted")
        
        return JsonResponse({'status': 'success'}, status=200)
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JsonResponse({'status': 'error'}, status=500)


# ============================================================
# PREMIUM FEATURES - EXAMPLES
# ============================================================


@login_required
@require_premium
def meal_planner(request):
    """
    Meal planning tools - Premium feature only
    """
    user_profile = request.user.userprofile
    
    # Get date from request or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()
        
    # Get meal plans for the selected date
    meal_plans = MealPlan.objects.filter(
        user=request.user,
        date=current_date
    ).prefetch_related('mealplanitem_set__food')
    
    # Organize by meal type
    planned_meals = {}
    nutrition_summary = {
        'total_calories': 0,
        'total_protein': 0,
        'total_carbs': 0,
        'total_fats': 0
    }
    
    # Initialize all meal types
    for meal_type_code, meal_type_name in MealPlan.MEAL_TYPES:
        planned_meals[meal_type_code] = {
            'name': meal_type_name,
            'items': [],
            'calories': 0
        }
        
    # Populate with data
    for plan in meal_plans:
        meal_type = plan.meal_type
        if meal_type in planned_meals:
            for item in plan.mealplanitem_set.all():
                calories = item.food.calories * item.servings
                protein = item.food.protein * item.servings
                carbs = item.food.carbs * item.servings
                fats = item.food.fats * item.servings
                
                planned_meals[meal_type]['items'].append({
                    'food': item.food,
                    'servings': item.servings,
                    'calories': calories,
                    'id': item.id
                })
                
                planned_meals[meal_type]['calories'] += calories
                
                # Update totals
                nutrition_summary['total_calories'] += calories
                nutrition_summary['total_protein'] += protein
                nutrition_summary['total_carbs'] += carbs
                nutrition_summary['total_fats'] += fats

    # Calculate calorie progress percentage
    calorie_percentage = min((nutrition_summary['total_calories'] / user_profile.daily_calorie_goal * 100), 100) if user_profile.daily_calorie_goal > 0 else 0
    
    # Calculate remaining calories and macros for AI suggestions
    remaining_calories = user_profile.daily_calorie_goal - nutrition_summary['total_calories']
    
    # AI Meal Suggestions based on user profile and remaining calories
    ai_suggestions = []
    suggestion_criteria = None
    if remaining_calories > 50:
        # Get user's weight goal and profile info for personalized suggestions
        weight_goal = user_profile.weight_goal
        
        # Define suggestion criteria based on weight goal
        if weight_goal == 'lose':
            # For weight loss: suggest high protein, low calorie foods
            suggestion_criteria = {
                'type': 'weight_loss',
                'focus': 'High Protein, Low Calorie',
                'calorie_limit': min(remaining_calories, 500),
                'protein_priority': True
            }
        elif weight_goal == 'gain':
            # For weight gain: suggest calorie-dense, high protein foods
            suggestion_criteria = {
                'type': 'weight_gain',
                'focus': 'High Calorie, High Protein',
                'calorie_limit': remaining_calories,
                'protein_priority': True
            }
        else:
            # For maintenance: balanced nutrition
            suggestion_criteria = {
                'type': 'maintenance',
                'focus': 'Balanced Nutrition',
                'calorie_limit': remaining_calories,
                'protein_priority': False
            }
        
        # Get suitable foods based on criteria
        suitable_foods = Food.objects.filter(calories__lte=suggestion_criteria['calorie_limit'])
        
        if suggestion_criteria['protein_priority']:
            suitable_foods = suitable_foods.order_by('-protein', 'calories')[:8]
        else:
            suitable_foods = suitable_foods.order_by('-calories')[:8]
        
        for food in suitable_foods:
            # Calculate optimal servings
            if food.calories > 0:
                optimal_servings = min(remaining_calories / food.calories, 3)
                optimal_servings = round(optimal_servings * 2) / 2  # Round to nearest 0.5
                if optimal_servings >= 0.5:
                    # Generate AI reasoning
                    reasons = []
                    if food.protein >= 15:
                        reasons.append("High protein")
                    if food.calories <= 200:
                        reasons.append("Low calorie")
                    if food.protein > 0 and food.calories / food.protein <= 20:
                        reasons.append("Protein efficient")
                    if food.carbs <= 20:
                        reasons.append("Low carb")
                    if not reasons:
                        reasons.append("Balanced")
                    
                    ai_suggestions.append({
                        'food': food,
                        'servings': optimal_servings,
                        'total_calories': int(food.calories * optimal_servings),
                        'total_protein': round(food.protein * optimal_servings, 1),
                        'total_carbs': round(food.carbs * optimal_servings, 1),
                        'total_fats': round(food.fats * optimal_servings, 1),
                        'reason': reasons[0],
                        'all_reasons': reasons
                    })
        
        # Limit to top 6 suggestions
        ai_suggestions = ai_suggestions[:6]
    
    # Get today's date and calculate the current month boundaries
    today = timezone.now().date()
    
    # Calculate the first and last day of the current month
    first_day_of_month = today.replace(day=1)
    # Get the last day of the month
    if today.month == 12:
        last_day_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    # Ensure current_date is within the current month (restrict to current month only)
    if current_date < first_day_of_month:
        current_date = first_day_of_month
    elif current_date > last_day_of_month:
        current_date = last_day_of_month
    
    # Get the week offset from the first week of the month
    week_offset = request.GET.get('week', None)
    
    # Calculate which week of the month to show
    if week_offset is not None:
        try:
            week_offset = int(week_offset)
        except ValueError:
            week_offset = 0
    else:
        # Calculate which week the current_date falls into
        days_from_start = (current_date - first_day_of_month).days
        week_offset = days_from_start // 7
    
    # Calculate start of the selected week
    start_of_week = first_day_of_month + timedelta(days=week_offset * 7)
    
    # Ensure we don't go before the start of the month
    if start_of_week < first_day_of_month:
        start_of_week = first_day_of_month
        week_offset = 0
    
    # Calculate the maximum week offset (number of weeks in the month)
    total_days_in_month = (last_day_of_month - first_day_of_month).days + 1
    max_week_offset = (total_days_in_month - 1) // 7
    
    # Ensure week_offset doesn't exceed maximum
    if week_offset > max_week_offset:
        week_offset = max_week_offset
        start_of_week = first_day_of_month + timedelta(days=week_offset * 7)
    
    # Generate dates for the weekly bar (7 days from start_of_week, but only within current month)
    week_dates = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        # Only include days within the current month
        if day <= last_day_of_month:
            week_dates.append({
                'date': day,
                'day_name': day.strftime('%a'),
                'day_num': day.day,
                'is_today': day == today,
                'is_selected': day == current_date
            })
    
    # Calculate navigation info
    has_prev_week = week_offset > 0
    has_next_week = week_offset < max_week_offset
    prev_week = week_offset - 1 if has_prev_week else None
    next_week = week_offset + 1 if has_next_week else None
    
    # Month info for display
    month_name = today.strftime('%B %Y')
    current_week_num = week_offset + 1
    total_weeks = max_week_offset + 1

    context = {
        'user_profile': user_profile,
        'current_date': current_date,
        'week_dates': week_dates,
        'planned_meals': planned_meals,
        'nutrition_summary': nutrition_summary,
        'calorie_percentage': calorie_percentage,
        'meal_types': MealPlan.MEAL_TYPES,
        'all_foods': Food.objects.all().order_by('name'),
        # Month navigation
        'month_name': month_name,
        'current_week_num': current_week_num,
        'total_weeks': total_weeks,
        'week_offset': week_offset,
        'has_prev_week': has_prev_week,
        'has_next_week': has_next_week,
        'prev_week': prev_week,
        'next_week': next_week,
        'first_day_of_month': first_day_of_month,
        'last_day_of_month': last_day_of_month,
        # AI Suggestions
        'ai_suggestions': ai_suggestions,
        'remaining_calories': remaining_calories,
        'suggestion_criteria': suggestion_criteria,
    }
    
    return render(request, 'myapp/meal_planner.html', context)

@login_required
@require_premium
def add_meal_plan(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        meal_type = request.POST.get('meal_type')
        food_id = request.POST.get('food_consumed')
        servings = float(request.POST.get('servings', 1))
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            food = Food.objects.get(id=food_id)
            
            # Get or create MealPlan for this user, date, and meal_type
            meal_plan, created = MealPlan.objects.get_or_create(
                user=request.user,
                date=date,
                meal_type=meal_type
            )
            
            # Add item to meal plan
            MealPlanItem.objects.create(
                meal_plan=meal_plan,
                food=food,
                servings=servings
            )
            
            messages.success(request, f'Added {food.name} to your plan for {date.strftime("%b %d")}')
        except Exception as e:
            messages.error(request, f'Error adding to plan: {str(e)}')
            
        return redirect(f'/meal-planner/?date={date_str}')
    return redirect('meal_planner')

@login_required
@require_premium
def log_meal_plan(request, plan_id):
    """Convert a planned meal item into a consumed log"""
    try:
        # We are actually receiving the MealPlanItem id here for granularity
        item = MealPlanItem.objects.get(id=plan_id)
        
        # Verify ownership through the parent MealPlan
        if item.meal_plan.user != request.user:
            return redirect('meal_planner')
            
        # Create Consume record
        Consume.objects.create(
            user=request.user,
            food_consumed=item.food,
            meal_type=item.meal_plan.meal_type,
            servings=item.servings,
            date_consumed=item.meal_plan.date
        )
        
        # Optional: Remove from plan after logging? 
        # For now, let's keep it but maybe mark it visually in UI if we added a status field.
        # Or just delete it to "move" it. Let's delete it to "move" it for now as per "Check off" metaphor.
        date_str = item.meal_plan.date.strftime('%Y-%m-%d')
        item.delete()
        
        # If meal plan is empty, delete it too
        if not item.meal_plan.mealplanitem_set.exists():
            item.meal_plan.delete()
            
        messages.success(request, f'Logged {item.food.name} as consumed!')
        return redirect(f'/meal-planner/?date={date_str}')
        
    except Exception as e:
        messages.error(request, f'Error logging meal: {str(e)}')
        return redirect('meal_planner')

@login_required
@require_premium
def delete_meal_plan_item(request, item_id):
    try:
        item = MealPlanItem.objects.get(id=item_id)
        if item.meal_plan.user != request.user:
            return redirect('meal_planner')
            
        date_str = item.meal_plan.date.strftime('%Y-%m-%d')
        item.delete()
        
        if not item.meal_plan.mealplanitem_set.exists():
            item.meal_plan.delete()
            
        messages.success(request, 'Removed item from plan.')
        return redirect(f'/meal-planner/?date={date_str}')
    except Exception as e:
        messages.error(request, 'Error removing item.')
        return redirect('meal_planner')

@login_required
@require_premium
def generate_shopping_list(request):
    user = request.user
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=7)
    
    # Get all meal plan items for the next 7 days
    items = MealPlanItem.objects.filter(
        meal_plan__user=user,
        meal_plan__date__range=[start_date, end_date]
    ).select_related('food')
    
    # Aggregate ingredients
    shopping_list = {}
    
    for item in items:
        food_name = item.food.name
        if food_name in shopping_list:
            shopping_list[food_name]['quantity'] += item.servings
            shopping_list[food_name]['calories'] += item.food.calories * item.servings
        else:
            shopping_list[food_name] = {
                'food': item.food,
                'quantity': item.servings,
                'calories': item.food.calories * item.servings
            }
            
    context = {
        'shopping_list': shopping_list,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'myapp/shopping_list.html', context)


@login_required
def advanced_analytics(request):
    """Advanced analytics page - redirects to dashboard with info message"""
    return render(request, 'myapp/advanced_analytics.html')
