"""
Django Admin configuration for user app models.

This module contains admin configurations for user-related models
including users, gifts, and user gifts with comprehensive
management capabilities.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Avg
from django.utils import timezone

from .models import Gift, UserGift


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    """
    Admin configuration for Gift model.
    
    Provides comprehensive gift management including gift details,
    pricing, and availability status.
    """
    list_display = [
        'name', 'get_coin_amount_display', 'get_description_preview',
        'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'description'
    ]
    readonly_fields = [
        'created_at'
    ]
    ordering = ['name']
    list_per_page = 25

    fieldsets = (
        ('Gift Information', {
            'fields': ('name', 'description', 'image', 'coin_amount')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_gifts', 'deactivate_gifts']

    def get_coin_amount_display(self, obj):
        """Get formatted coin amount display."""
        return f"{obj.coin_amount} coins"
    get_coin_amount_display.short_description = 'Coin Amount'
    get_coin_amount_display.admin_order_field = 'coin_amount'

    def get_description_preview(self, obj):
        """Get description preview."""
        if hasattr(obj, 'description') and obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return 'No description'
    get_description_preview.short_description = 'Description'

    def activate_gifts(self, request, queryset):
        """Activate selected gifts."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} gifts activated.')
    activate_gifts.short_description = 'Activate selected gifts'

    def deactivate_gifts(self, request, queryset):
        """Deactivate selected gifts."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} gifts deactivated.')
    deactivate_gifts.short_description = 'Deactivate selected gifts'

    def has_delete_permission(self, request, obj=None):
        """Disable gift deletion."""
        return False


@admin.register(UserGift)
class UserGiftAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserGift model.
    
    Provides comprehensive user gift management including
    gift assignments, delivery status, and user information.
    """
    list_display = [
        'get_user_email', 'get_gift_name', 'get_delivery_status',
        'date_won', 'delivery_date'
    ]
    list_filter = [
        'delivery_status', 'date_won', 'delivery_date'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'gift__name'
    ]
    readonly_fields = [
        'user', 'gift', 'date_won'
    ]
    ordering = ['-date_won']
    list_per_page = 25

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Gift Information', {
            'fields': ('gift',)
        }),
        ('Delivery Status', {
            'fields': ('delivery_status', 'delivery_date')
        }),
        ('Timestamps', {
            'fields': ('date_won',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def get_user_email(self, obj):
        """Get user email for display."""
        return obj.user.email if obj.user else 'N/A'
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'

    def get_gift_name(self, obj):
        """Get gift name for display."""
        return obj.gift.name if obj.gift else 'N/A'
    get_gift_name.short_description = 'Gift'
    get_gift_name.admin_order_field = 'gift__name'

    def get_delivery_status(self, obj):
        """Get delivery status with formatting."""
        status_colors = {
            'Pending': '#ffc107',
            'Shipped': '#17a2b8',
            'Delivered': '#28a745',
            'Cancelled': '#dc3545',
        }
        color = status_colors.get(obj.delivery_status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_delivery_status_display()
        )
    get_delivery_status.short_description = 'Delivery Status'
    get_delivery_status.admin_order_field = 'delivery_status'

    def mark_as_shipped(self, request, queryset):
        """Mark selected gifts as shipped."""
        updated = queryset.filter(delivery_status='Pending').update(
            delivery_status='Shipped'
        )
        self.message_user(request, f'{updated} gifts marked as shipped.')
    mark_as_shipped.short_description = 'Mark as shipped'

    def mark_as_delivered(self, request, queryset):
        """Mark selected gifts as delivered."""
        from django.utils import timezone
        updated = queryset.filter(delivery_status='Shipped').update(
            delivery_status='Delivered',
            delivery_date=timezone.now()
        )
        self.message_user(request, f'{updated} gifts marked as delivered.')
    mark_as_delivered.short_description = 'Mark as delivered'

    def mark_as_cancelled(self, request, queryset):
        """Mark selected gifts as cancelled."""
        updated = queryset.filter(delivery_status='Pending').update(
            delivery_status='Cancelled'
        )
        self.message_user(request, f'{updated} gifts marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark as cancelled'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'gift')

    def has_add_permission(self, request):
        """Allow user gift creation."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow user gift editing."""
        return True

    def has_delete_permission(self, request, obj=None):
        """Disable user gift deletion."""
        return False