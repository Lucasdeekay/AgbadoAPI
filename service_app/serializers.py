from rest_framework import serializers
from .models import Service, SubService, ServiceRequest, ServiceRequestBid, Booking
from django.conf import settings  # Import settings for MEDIA_URL


# Serializer for Service model
class ServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and obj.image.url:
            return request.build_absolute_uri(obj.image.url)
        return None


# Serializer for SubService model
class SubServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SubService
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and obj.image.url:
            return request.build_absolute_uri(obj.image.url)
        return None


# Serializer for ServiceRequest model
class ServiceRequestSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and obj.image.url:
            return request.build_absolute_uri(obj.image.url)
        return None


# Serializer for ServiceRequestBid model
class ServiceRequestBidSerializer(serializers.ModelSerializer):
    service_provider = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequestBid
        fields = '__all__'

    def get_service_provider(self, obj):
        request = self.context.get('request')
        user_data = {
            "id": obj.service_provider.id,
            "email": obj.service_provider.email,
            "first_name": obj.service_provider.first_name,
            "last_name": obj.service_provider.last_name,
            "profile_picture": request.build_absolute_uri(obj.service_provider.profile_picture.url) if obj.service_provider.profile_picture and obj.service_provider.profile_picture.url else None,
        }
        return user_data

# Serializer for Booking model
class BookingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    service_provider = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    def get_user(self, obj):
        request = self.context.get('request')
        user_data = {
            "id": obj.user.id,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "profile_picture": request.build_absolute_uri(obj.user.profile_picture.url) if obj.user.profile_picture and obj.user.profile_picture.url else None,
        }
        return user_data

    def get_service_provider(self, obj):
        request = self.context.get('request')
        provider_data = {
            "id": obj.service_provider.id,
            "email": obj.service_provider.email,
            "first_name": obj.service_provider.first_name,
            "last_name": obj.service_provider.last_name,
            "profile_picture": request.build_absolute_uri(obj.service_provider.profile_picture.url) if obj.service_provider.profile_picture and obj.service_provider.profile_picture.url else None,
        }
        return provider_data