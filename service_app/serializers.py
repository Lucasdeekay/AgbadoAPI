from rest_framework import serializers
from .models import Service, SubService, ServiceRequest


# Serializer for Service model
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'is_active', 'updated_at')


# Serializer for SubService model
class SubServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubService
        fields = ('id', 'service', 'name', 'description', 'price', 'is_active', 'created_at')


# Serializer for ServiceRequest model
class ServiceRequestSerializer(serializers.ModelSerializer):
    service = ServiceSerializer()
    sub_service = SubServiceSerializer()

    class Meta:
        model = ServiceRequest
        fields = (
        'user', 'service', 'sub_service', 'status', 'requested_at', 'completed_at', 'total_amount', 'payment_status')
