"""
Serializers for notification app models.

This module contains serializers for handling data validation and transformation
for notification-related models including user notifications and message handling.
"""

from rest_framework import serializers
from .models import Notification

import logging

logger = logging.getLogger(__name__)


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    
    Handles notification data serialization and deserialization including
    message content, read status, and user association.
    """
    
    class Meta:
        model = Notification
        fields = ('id', 'user', 'title', 'message', 'created_at', 'is_read')
        read_only_fields = ('id', 'created_at')
        extra_kwargs = {
            'user': {'required': True},
            'message': {'required': True},
            'title': {'required': False}
        }

    def validate_message(self, value):
        """
        Validate message content.
        
        Ensures message is not empty and has reasonable length.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        
        if len(value) > 1000:
            raise serializers.ValidationError("Message is too long. Maximum 1000 characters.")
        
        return value.strip()

    def validate_title(self, value):
        """
        Validate title content.
        
        Ensures title has reasonable length if provided.
        """
        if value and len(value) > 200:
            raise serializers.ValidationError("Title is too long. Maximum 200 characters.")
        
        return value.strip() if value else value

    def create(self, validated_data):
        """
        Create a new notification instance.
        
        Handles notification creation with proper validation.
        """
        try:
            notification = super().create(validated_data)
            logger.info(f"Notification created for user: {notification.user.email}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise serializers.ValidationError(f"Error creating notification: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update an existing notification instance.
        
        Handles notification updates with proper validation.
        """
        try:
            notification = super().update(instance, validated_data)
            logger.info(f"Notification updated for user: {notification.user.email}")
            return notification
            
        except Exception as e:
            logger.error(f"Error updating notification: {str(e)}")
            raise serializers.ValidationError(f"Error updating notification: {str(e)}")


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing notifications.
    
    Provides a simplified view of notifications for list endpoints
    with optimized field selection.
    """
    
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'created_at', 'is_read')
        read_only_fields = ('id', 'created_at')


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed notification view.
    
    Provides comprehensive notification information including
    user details and full message content.
    """
    
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = (
            'id', 'user', 'user_email', 'user_name', 'title', 'message', 
            'created_at', 'is_read'
        )
        read_only_fields = ('id', 'created_at', 'user_email', 'user_name')

    def get_user_name(self, obj):
        """
        Get user's full name.
        
        Returns the user's full name or email if name is not available.
        """
        return obj.user.get_full_name() if obj.user else None
