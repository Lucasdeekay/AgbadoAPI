from django.contrib import admin
from .models import DailyTask, TaskCompletion, UserReward, UserActivity, LeisureAccess


# Registering the Notification model with custom admin interface


# Registering the DailyTask model with custom admin interface
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'task_type', 'points', 'created_at', 'is_active')
    search_fields = ('title', 'description', 'task_type')
    list_filter = ('is_active', 'task_type')
    ordering = ('-created_at',)


# Registering the TaskCompletion model with custom admin interface
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'completed_at', 'otp_verified')
    search_fields = ('user__email', 'task__task_name')
    list_filter = ('otp_verified',)
    ordering = ('-completed_at',)


# Registering the UserReward model with custom admin interface
class UserRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'redeemed', 'redeemed_at')
    search_fields = ('user__email', 'redeemed')
    ordering = ('-redeemed_at',)


# Registering the UserActivity model with custom admin interface
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'created_at')
    search_fields = ('user__email', 'activity_type')
    list_filter = ('activity_type',)
    ordering = ('-created_at',)


# Registering the LeisureAccess model with custom admin interface
class LeisureAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'verified_at')
    search_fields = ('user__email', 'is_verified')
    list_filter = ('is_verified',)
    ordering = ('-verified_at',)


admin.site.register(DailyTask, DailyTaskAdmin)
admin.site.register(TaskCompletion, TaskCompletionAdmin)
admin.site.register(UserReward, UserRewardAdmin)
admin.site.register(UserActivity, UserActivityAdmin)
admin.site.register(LeisureAccess, LeisureAccessAdmin)
