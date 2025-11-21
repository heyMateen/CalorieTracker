"""
EXAMPLE: How to Add Premium Features to Your CalorieTracker

This file shows examples of how to protect features with the @require_premium decorator
and how to handle premium access in your views.

Copy these patterns into your actual views.py file as needed.
"""

# ============================================================
# EXAMPLE 1: Protect an entire view with @require_premium
# ============================================================

from myapp.subscription import require_premium
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@require_premium
def advanced_nutrition_analysis(request):
    """
    Premium Feature: Advanced nutrition analysis with AI-powered insights
    
    This view requires the user to have an active premium subscription.
    If not, they'll be redirected to the subscription plans page.
    """
    user_profile = request.user.userprofile
    
    # Get user's consumption data
    from .models import Consume
    from django.utils import timezone
    from datetime import timedelta
    
    last_7_days = Consume.objects.filter(
        user=request.user,
        date_consumed__gte=timezone.now().date() - timedelta(days=7)
    )
    
    context = {
        'weekly_data': last_7_days,
        'premium_feature': True,
    }
    
    return render(request, 'premium/advanced_analysis.html', context)


# ============================================================
# EXAMPLE 2: Check premium status within a view
# ============================================================

@login_required
def meal_planning_dashboard(request):
    """
    View that partially uses premium features
    Non-premium users see limited version, premium get full access
    """
    user_profile = request.user.userprofile
    is_premium = user_profile.is_premium_active()
    
    if is_premium:
        # Premium user - show all features
        template = 'premium/meal_planner_full.html'
        context = {
            'advanced_features': True,
            'premium_until': user_profile.premium_until,
        }
    else:
        # Free user - show limited features
        template = 'premium/meal_planner_limited.html'
        context = {
            'advanced_features': False,
            'upgrade_url': '/subscription/plans/',
        }
    
    return render(request, template, context)


# ============================================================
# EXAMPLE 3: Redirect non-premium users to subscription page
# ============================================================

from django.shortcuts import redirect
from django.contrib import messages

@login_required
def recipe_collection(request):
    """
    View that requires premium subscription with custom message
    """
    user_profile = request.user.userprofile
    
    # Check premium status
    if not user_profile.is_premium_active():
        messages.info(
            request,
            "🔓 Recipe collections are a premium feature! Upgrade now to save and organize your favorite recipes."
        )
        return redirect('subscription_plans')
    
    # User is premium - show recipe collection
    recipes = user_profile.user.recipe_set.all()
    
    context = {
        'recipes': recipes,
        'premium_until': user_profile.premium_until,
    }
    
    return render(request, 'premium/recipes.html', context)


# ============================================================
# EXAMPLE 4: Custom permission logic
# ============================================================

def advanced_meal_plan_generation(request):
    """
    Premium Feature: AI-powered meal plan generation
    Shows how to implement custom permission checks
    """
    from django.http import JsonResponse
    
    user_profile = request.user.userprofile
    
    # Check multiple conditions
    if not request.user.is_authenticated:
        return redirect('login')
    
    if not user_profile.is_premium_active():
        return JsonResponse({
            'error': 'Premium feature',
            'message': 'This feature requires a premium subscription',
            'redirect_url': '/subscription/plans/'
        }, status=403)
    
    if not user_profile.height or not user_profile.date_of_birth:
        messages.warning(request, "Please complete your profile first")
        return redirect('edit_profile')
    
    # User has all required permissions and data
    # Generate meal plan...
    
    return render(request, 'premium/meal_plan_generator.html')


# ============================================================
# EXAMPLE 5: Template-level checks (in HTML template)
# ============================================================

"""
HTML Example:

{% extends 'myapp/base.html' %}

{% block content %}
<div class="container">
    {% if user.userprofile.is_premium_active %}
        <!-- Premium user content -->
        <div class="premium-feature">
            <h2>Advanced Analytics</h2>
            <p>Premium until: {{ user.userprofile.premium_until|date:"F d, Y" }}</p>
            <!-- Show premium features -->
        </div>
    {% else %}
        <!-- Free user content -->
        <div class="upgrade-prompt">
            <h2>Unlock Advanced Analytics</h2>
            <p>Want to see detailed insights about your nutrition?</p>
            <a href="{% url 'subscription_plans' %}" class="btn btn-primary">
                Upgrade to Premium
            </a>
        </div>
    {% endif %}
</div>
{% endblock %}
"""


# ============================================================
# EXAMPLE 6: Protect API endpoints (for AJAX calls)
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["POST"])
@login_required
def get_detailed_nutrition_stats(request):
    """
    API endpoint for premium nutrition analysis
    Can be called via AJAX
    """
    user_profile = request.user.userprofile
    
    if not user_profile.is_premium_active():
        return JsonResponse({
            'success': False,
            'error': 'Premium feature',
            'message': 'This feature requires a premium subscription',
            'premium_required': True,
            'upgrade_url': '/subscription/plans/',
        }, status=403)
    
    # Process the request
    try:
        data = json.loads(request.body)
        stats = calculate_premium_stats(request.user, data)
        
        return JsonResponse({
            'success': True,
            'data': stats,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


# ============================================================
# EXAMPLE 7: Using in a Class-Based View (if using Django's CBV)
# ============================================================

from django.views import View
from django.utils.decorators import method_decorator

class PremiumFeatureView(View):
    """Example class-based view with premium protection"""
    
    @method_decorator(require_premium)
    @method_decorator(login_required)
    def get(self, request):
        user_profile = request.user.userprofile
        
        context = {
            'premium_until': user_profile.premium_until,
        }
        
        return render(request, 'premium/feature.html', context)


# ============================================================
# EXAMPLE 8: Trial period integration
# ============================================================

from datetime import timedelta
from django.utils import timezone

def give_trial_period(user, days=7):
    """
    Give a user free trial access to premium features
    """
    user_profile = user.userprofile
    
    user_profile.is_premium = True
    user_profile.premium_until = timezone.now() + timedelta(days=days)
    user_profile.save()
    
    from django.contrib import messages
    messages.success(user.request, f"You now have {days} days of free premium access!")


# ============================================================
# HOW TO IMPLEMENT IN YOUR APP:
# ============================================================

"""
1. Add @require_premium decorator to views you want to protect:
   
   from myapp.subscription import require_premium
   
   @require_premium
   def my_feature(request):
       ...

2. Check premium status in views:
   
   if request.user.userprofile.is_premium_active():
       # Show premium features
   else:
       # Show upgrade prompt

3. In templates, show/hide premium features:
   
   {% if user.userprofile.is_premium_active %}
       <!-- Premium content -->
   {% else %}
       <!-- Free content -->
   {% endif %}

4. Common premium features to add:
   - Advanced meal planning
   - AI nutrition insights
   - Recipe management
   - Detailed analytics & charts
   - Custom goal setting
   - Priority support
   - Export data
   - Sync with wearables
"""
