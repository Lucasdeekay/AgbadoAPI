from django.contrib import admin, messages

from auth_app.models import User

from .models import Notification


# Register your models here.
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'message', 'created_at', 'is_read')
    search_fields = ('user__email', 'title', 'created_at', 'is_read')
    list_filter = ('is_read',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)  # Add this to allow display but not editing
    actions = ['send_notification_to_all']  # Ensure this is included

    def send_notification_to_all(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select only one notification to send.", level=messages.ERROR)
            return
        
        notification = queryset.first()
        users = User.objects.all()
        
        notifications = [
            Notification(user=user, title=notification.title, message=notification.message) 
            for user in users
        ]
        Notification.objects.bulk_create(notifications)

        self.message_user(request, f"Notification sent to {users.count()} users!", level=messages.SUCCESS)

    send_notification_to_all.short_description = "Send selected notification to all users"

admin.site.register(Notification, NotificationAdmin)