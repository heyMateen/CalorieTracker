"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from myapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name="dashboard"),
    path('track/', views.index, name="index"),
    path('delete/<int:id>/', views.delete_consume, name="delete"),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('add-food/', views.add_food, name='add_food'),
    path('add-meal/', views.add_meal, name='add_meal'),
    path('log-weight/', views.log_weight, name='log_weight'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Subscription and Payment URLs
    path('subscription/plans/', views.subscription_plans, name='subscription_plans'),
    path('subscription/checkout/<int:plan_id>/', views.create_checkout, name='create_checkout'),
    path('subscription/success/', views.payment_success, name='payment_success'),
    path('subscription/status/', views.subscription_status, name='subscription_status'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Premium Features
    path('meal-planner/', views.meal_planner, name='meal_planner'),
    path('meal-planner/add/', views.add_meal_plan, name='add_meal_plan'),
    path('meal-planner/log/<int:plan_id>/', views.log_meal_plan, name='log_meal_plan'),
    path('meal-planner/delete/<int:item_id>/', views.delete_meal_plan_item, name='delete_meal_plan_item'),
    path('meal-planner/shopping-list/', views.generate_shopping_list, name='generate_shopping_list'),
    path('analytics/', views.advanced_analytics, name='advanced_analytics'),
    
    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='myapp/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='myapp/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='myapp/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='myapp/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
