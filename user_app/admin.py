# gifts/admin.py
from django.contrib import admin
from .models import DailyTask, TaskCompletion, UserReward, LeisureAccess, UserActivity, Gift, UserGift

@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'points', 'is_active', 'created_at')
    list_filter = ('task_type', 'is_active', 'created_at')
    search_fields = ('title', 'description')

@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'completed_at', 'otp_verified')
    list_filter = ('task__task_type', 'otp_verified', 'completed_at')
    search_fields = ('user__email', 'task__title')
    raw_id_fields = ('user', 'task')

@admin.register(UserReward)
class UserRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'redeemed', 'redeemed_at')
    list_filter = ('redeemed', 'redeemed_at')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)

@admin.register(LeisureAccess)
class LeisureAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'instagram_handle', 'youtube_channel', 'is_verified', 'verified_at')
    list_filter = ('is_verified',)
    search_fields = ('user__email', 'instagram_handle', 'youtube_channel')
    raw_id_fields = ('user',)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__email', 'description')
    raw_id_fields = ('user',)

@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'coin_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)

@admin.register(UserGift)
class UserGiftAdmin(admin.ModelAdmin):
    list_display = ('user', 'gift', 'date_won', 'delivery_status', 'delivery_date')
    list_filter = ('delivery_status', 'date_won', 'delivery_date')
    search_fields = ('user__email', 'gift__name')
    raw_id_fields = ('user', 'gift')