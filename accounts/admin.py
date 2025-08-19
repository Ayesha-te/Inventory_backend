from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, UserSession, EmailVerification, PasswordReset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'username', 'first_name', 'last_name', 
        'subscription_plan', 'is_verified', 'is_active', 'date_joined'
    ]
    list_filter = [
        'subscription_plan', 'is_verified', 'is_active', 
        'is_staff', 'is_superuser', 'date_joined'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name', 'company_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': (
                'phone', 'company_name', 'address', 'profile_picture',
                'is_verified', 'last_login_ip'
            )
        }),
        ('Subscription', {
            'fields': (
                'subscription_plan', 'subscription_start_date', 
                'subscription_end_date', 'is_subscription_active'
            )
        }),
        ('Preferences', {
            'fields': ('timezone', 'language', 'email_notifications')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'company_name')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_type', 'created_at', 'updated_at']
    list_filter = ['business_type', 'low_stock_alerts', 'expiry_alerts', 'created_at']
    search_fields = ['user__email', 'user__username', 'business_type']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'location', 'is_active', 'created_at', 'last_activity']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['user__email', 'ip_address', 'location']
    readonly_fields = ['created_at', 'last_activity']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['created_at']


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['created_at']