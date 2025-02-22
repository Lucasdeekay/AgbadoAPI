from rest_framework import serializers
from .models import Service, SubService, ServiceRequest, ServiceRequestBid, Booking


# Serializer for Service model
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'category', 'min_price', 'max_price', 'is_active')


# Serializer for SubService model
class SubServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubService
        fields = ('id', 'service', 'name', 'description', 'price', 'is_active', 'created_at')


# Serializer for ServiceRequest model
class ServiceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = '__all__'


# Serializer for ServiceRequestBid model
class ServiceRequestBidSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequestBid
        fields = '__all__'


# Serializer for Booking model
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'