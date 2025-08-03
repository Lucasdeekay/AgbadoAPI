"""
Admin interface for provider app models.

This module contains admin configurations for service provider management
including business information, approval processes, and rating management.
"""

from django.contrib import admin, messages
from django.utils.html import format_html
from django.db.models import Avg, Count

from .models import ServiceProvider


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    """
    Admin interface for ServiceProvider model.
    
    Provides comprehensive service provider management with filtering,
    searching, bulk actions, and approval processes.
    """
    list_display = (
        'company_name', 'get_user_email', 'business_category', 
        'get_business_hours', 'avg_rating_display', 'rating_population',
        'is_approved_display', 'created_at'
    )
    list_filter = ('is_approved', 'business_category', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name',
        'company_name', 'company_email', 'company_address'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'avg_rating', 'rating_population')
    list_per_page = 25
    
    fieldsets = (
        ('Company Information', {
            'fields': ('user', 'company_name', 'company_address', 'company_description')
        }),
        ('Contact Information', {
            'fields': ('company_phone_no', 'company_email', 'company_logo')
        }),
        ('Business Details', {
            'fields': ('business_category', 'opening_hour', 'closing_hour')
        }),
        ('Ratings & Approval', {
            'fields': ('avg_rating', 'rating_population', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_service_providers', 'disapprove_service_providers', 'reset_ratings']

    def get_user_email(self, obj):
        """Get user email for display."""
        return obj.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'

    def get_business_hours(self, obj):
        """Get formatted business hours."""
        return obj.get_business_hours()
    get_business_hours.short_description = 'Business Hours'

    def avg_rating_display(self, obj):
        """Display average rating with stars."""
        if obj.avg_rating > 0:
            stars = "★" * int(obj.avg_rating) + "☆" * (5 - int(obj.avg_rating))
            return format_html(
                '<span title="{}">{}</span>', 
                f"{obj.avg_rating}/5.0", 
                stars
            )
        return "No ratings"
    avg_rating_display.short_description = 'Rating'
    avg_rating_display.admin_order_field = 'avg_rating'

    def is_approved_display(self, obj):
        """Display approval status with color coding."""
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        return format_html('<span style="color: red;">✗ Pending</span>')
    is_approved_display.short_description = 'Status'
    is_approved_display.admin_order_field = 'is_approved'

    def approve_service_providers(self, request, queryset):
        """Approve selected service providers."""
        updated = queryset.update(is_approved=True)
        self.message_user(
            request, 
            f"Successfully approved {updated} service provider(s).",
            level=messages.SUCCESS
        )
    approve_service_providers.short_description = "Approve selected service providers"

    def disapprove_service_providers(self, request, queryset):
        """Disapprove selected service providers."""
        updated = queryset.update(is_approved=False)
        self.message_user(
            request, 
            f"Successfully disapproved {updated} service provider(s).",
            level=messages.SUCCESS
        )
    disapprove_service_providers.short_description = "Disapprove selected service providers"

    def reset_ratings(self, request, queryset):
        """Reset ratings for selected service providers."""
        updated = queryset.update(avg_rating=0.00, rating_population=0)
        self.message_user(
            request, 
            f"Successfully reset ratings for {updated} service provider(s).",
            level=messages.SUCCESS
        )
    reset_ratings.short_description = "Reset ratings for selected service providers"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for all users."""
        return self.readonly_fields + ('created_at',)

    def has_add_permission(self, request):
        """Allow adding service providers."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow changing service providers."""
        return True

    def has_delete_permission(self, request, obj=None):
        """Allow deleting service providers."""
        return True

    def get_actions(self, request):
        """Get available actions based on user permissions."""
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            # Remove sensitive actions for non-superusers
            if 'reset_ratings' in actions:
                del actions['reset_ratings']
        return actions
