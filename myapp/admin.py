from django.contrib import admin
from .models import Food, Consume, UserProfile, SubscriptionPlan, SubscriptionPurchase, PaymentLog, WeightLog

# Register your models here.
admin.site.register(Food)
admin.site.register(Consume)
admin.site.register(UserProfile)
admin.site.register(WeightLog)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'duration', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'description', 'duration', 'duration_days')
        }),
        ('Pricing', {
            'fields': ('price', 'stripe_price_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubscriptionPurchase)
class SubscriptionPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'amount', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'created_at', 'plan')
    search_fields = ('user__username', 'user__email', 'stripe_session_id')
    readonly_fields = ('stripe_session_id', 'stripe_payment_intent_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan')
        }),
        ('Subscription Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Payment', {
            'fields': ('amount', 'status')
        }),
        ('Stripe Information', {
            'fields': ('stripe_session_id', 'stripe_payment_intent_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request):
        # Prevent accidental deletion of subscription records
        return request.user.is_superuser and request.user.has_perm('myapp.delete_subscriptionpurchase')


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('user__username', 'stripe_charge_id')
    readonly_fields = ('stripe_charge_id', 'created_at', 'details')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User & Transaction', {
            'fields': ('user', 'transaction_type', 'subscription_purchase')
        }),
        ('Amount', {
            'fields': ('amount', 'currency')
        }),
        ('Status', {
            'fields': ('status', 'stripe_charge_id')
        }),
        ('Details', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request):
        # Prevent deletion of payment logs (audit trail)
        return False
