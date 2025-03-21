from rest_framework import serializers
from .models import DailyTask, TaskCompletion, UserReward, UserActivity, LeisureAccess


# Serializer for DailyTask model
class DailyTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyTask
        fields = ('title', 'description', 'task_type', 'points', 'created_at', 'is_active')


# Serializer for TaskCompletion model
class TaskCompletionSerializer(serializers.ModelSerializer):
    task = DailyTaskSerializer()

    class Meta:
        model = TaskCompletion
        fields = ('user', 'task', 'completed_at', 'otp_verified')


# Serializer for UserReward model
class UserRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReward
        fields = ('user', 'points', 'redeemed', 'redeemed_at')


# Serializer for UserActivity model
class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ('user', 'activity_type', 'description', 'created_at')


# Serializer for LeisureAccess model
class LeisureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeisureAccess
        fields = ('user', 'is_verified', 'verified_at')
