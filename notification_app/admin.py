from django.contrib import admin

from .models import Notification


# Register your models here.
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read')
    search_fields = ('user__email', 'message')
    list_filter = ('is_read',)
    ordering = ('-created_at',)

admin.site.register(Notification, NotificationAdmin)