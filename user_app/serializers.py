"""
Serializers for user app models.

This module contains serializers for handling data validation and transformation
for user-related models including tasks, rewards, activities, and gifts.
"""

from rest_framework import serializers
from .models import DailyTask, Gift, TaskCompletion, UserReward, UserActivity, LeisureAccess, UserGift


class DailyTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for DailyTask model.
    
    Handles serialization and deserialization of daily task data.
    """
    class Meta:
        model = DailyTask
        fields = ('id', 'title', 'description', 'task_type', 'youtube_link', 'points', 'created_at', 'is_active')
        read_only_fields = ('id', 'created_at')


class TaskCompletionSerializer(serializers.ModelSerializer):
    """
    Serializer for TaskCompletion model.
    
    Includes nested task data for complete task completion information.
    """
    task = DailyTaskSerializer(read_only=True)

    class Meta:
        model = TaskCompletion
        fields = ('id', 'user', 'task', 'completed_at', 'otp_verified')
        read_only_fields = ('id', 'completed_at')


class UserRewardSerializer(serializers.ModelSerializer):
    """
    Serializer for UserReward model.
    
    Handles user reward data including points and redemption status.
    """
    class Meta:
        model = UserReward
        fields = ('id', 'user', 'points', 'redeemed', 'redeemed_at')
        read_only_fields = ('id', 'redeemed_at')


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for UserActivity model.
    
    Handles user activity tracking and logging.
    """
    class Meta:
        model = UserActivity
        fields = ('id', 'user', 'activity_type', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class LeisureAccessSerializer(serializers.ModelSerializer):
    """
    Serializer for LeisureAccess model.
    
    Handles social media verification and access control.
    """
    class Meta:
        model = LeisureAccess
        fields = ('id', 'user', 'instagram_handle', 'youtube_channel', 'is_verified', 'verified_at')
        read_only_fields = ('id', 'verified_at')

class GiftSerializer(serializers.ModelSerializer):
    """
    Serializer for Gift model.
    
    Handles gift information including images and coin requirements.
    """
    class Meta:
        model = Gift
        fields = ('id', 'name', 'image', 'coin_amount', 'created_at')
        read_only_fields = ('id', 'created_at')

class UserGiftSerializer(serializers.ModelSerializer):
    """
    Serializer for UserGift model.
    
    Includes nested user and gift information for complete gift tracking.
    """
    user_email = serializers.ReadOnlyField(source='user.email')
    gift_name = serializers.ReadOnlyField(source='gift.name')
    gift_image = serializers.ImageField(source='gift.image', read_only=True)

    class Meta:
        model = UserGift
        fields = ('id', 'user', 'user_email', 'gift', 'gift_name', 'gift_image', 
                 'date_won', 'delivery_status', 'delivery_date')
        read_only_fields = ('id', 'date_won')
        