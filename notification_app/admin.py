"""
Admin interface for notification app models.

This module contains admin configurations for notification management
including user notifications, message handling, and bulk operations.
"""

from django.contrib import admin, messages
from django.utils.html import format_html
from django.db.models import Count

from auth_app.models import User
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    
    Provides comprehensive notification management with filtering,
    searching, bulk actions, and user targeting.
    """
    list_display = (
        'user', 'get_title_display', 'get_message_preview', 
        'created_at', 'is_read_display', 'get_user_email'
    )
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'title', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    list_per_page = 25
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_notification_to_all']

    def get_title_display(self, obj):
        """Display title or 'No Title' if empty."""
        return obj.title or "No Title"
    get_title_display.short_description = 'Title'
    get_title_display.admin_order_field = 'title'

    def get_message_preview(self, obj):
        """Display message preview (first 50 characters)."""
        preview = obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
        return preview
    get_message_preview.short_description = 'Message Preview'

    def is_read_display(self, obj):
        """Display read status with color coding."""
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: red;">✗ Unread</span>')
    is_read_display.short_description = 'Status'
    is_read_display.admin_order_field = 'is_read'

    def get_user_email(self, obj):
        """Get user email for display."""
        return obj.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(
            request, 
            f"Successfully marked {updated} notification(s) as read.",
            level=messages.SUCCESS
        )
    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(
            request, 
            f"Successfully marked {updated} notification(s) as unread.",
            level=messages.SUCCESS
        )
    mark_as_unread.short_description = "Mark selected notifications as unread"

    def send_notification_to_all(self, request, queryset):
        """Send selected notification to all users."""
        if queryset.count() != 1:
            self.message_user(
                request, 
                "Please select only one notification to send.", 
                level=messages.ERROR
            )
            return
        
        notification = queryset.first()
        users = User.objects.filter(is_active=True)
        
        # Create notifications in batches to avoid memory issues
        batch_size = 1000
        notifications = []
        
        for user in users:
            notifications.append(Notification(
                user=user, 
                title=notification.title, 
                message=notification.message
            ))
            
            if len(notifications) >= batch_size:
                Notification.objects.bulk_create(notifications)
                notifications = []
        
        # Create remaining notifications
        if notifications:
            Notification.objects.bulk_create(notifications)

        self.message_user(
            request, 
            f"Notification sent to {users.count()} users!", 
            level=messages.SUCCESS
        )
    send_notification_to_all.short_description = "Send selected notification to all users"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')

    def get_readonly_fields(self, request, obj=None):
        """Make created_at readonly for all users."""
        return self.readonly_fields + ('created_at',)

    def has_add_permission(self, request):
        """Allow adding notifications."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow changing notifications."""
        return True

    def has_delete_permission(self, request, obj=None):
        """Allow deleting notifications."""
        return True