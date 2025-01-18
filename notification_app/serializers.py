from rest_framework import serializers
from .models import Notification


# Serializer for Notification model
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('user', 'message', 'created_at', 'is_read')
