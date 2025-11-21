from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum
from .models import Food, Consume, UserProfile, WeightLog, MEAL_TYPE_CHOICES
from .forms import SignUpForm
from django.db.models.functions import TruncDate

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # UserProfile will be created automatically via signals
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
    
    # Get latest weight and BMI
    latest_weight = WeightLog.objects.filter(user=request.user).order_by('-date').first()
    current_bmi = user_profile.calculate_bmi(latest_weight.weight if latest_weight else None)
    
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
    weekly_consumption = Consume.objects.filter(
        user=request.user,
        date_consumed__gte=week_ago
    ).values('date_consumed').annotate(
        daily_total=Sum('food_consumed__calories')
    ).order_by('date_consumed')
    
    weekly_avg_calories = sum(day['daily_total'] for day in weekly_consumption) / 7 if weekly_consumption else 0
    
    # Prepare data for charts
    calorie_history = list(weekly_consumption)
    calorie_history_dates = [entry['date_consumed'].strftime('%b %d') for entry in calorie_history]
    calorie_history_values = [entry['daily_total'] for entry in calorie_history]
    
    # Get weight history
    weight_history = WeightLog.objects.filter(
        user=request.user,
        date__gte=week_ago
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
    }
    
    return render(request, 'myapp/dashboard.html', context)

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
    
    if request.method == 'POST':
        # Get form data
        height = request.POST.get('height')
        date_of_birth = request.POST.get('date_of_birth')
        activity_level = request.POST.get('activity_level')
        weight_goal = request.POST.get('weight_goal')
        daily_calorie_goal = request.POST.get('daily_calorie_goal')
        
        # Update profile
        try:
            # Store original values
            original_values = {
                'height': user_profile.height,
                'date_of_birth': user_profile.date_of_birth,
                'activity_level': user_profile.activity_level,
                'weight_goal': user_profile.weight_goal,
                'daily_calorie_goal': user_profile.daily_calorie_goal
            }
            
            # Set new values
            user_profile.height = float(height) if height else None
            user_profile.date_of_birth = date_of_birth if date_of_birth else None
            user_profile.activity_level = activity_level
            user_profile.weight_goal = weight_goal
            user_profile.daily_calorie_goal = int(daily_calorie_goal)
            
            # Check if any values changed
            new_values = {
                'height': user_profile.height,
                'date_of_birth': user_profile.date_of_birth,
                'activity_level': user_profile.activity_level,
                'weight_goal': user_profile.weight_goal,
                'daily_calorie_goal': user_profile.daily_calorie_goal
            }
            
            if original_values != new_values:
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
