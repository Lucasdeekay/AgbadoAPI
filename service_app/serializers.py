from rest_framework import serializers

from auth_app.utils import upload_to_cloudinary
from .models import Service, SubService, ServiceRequest, ServiceRequestBid, Booking
from django.conf import settings  # Import settings for MEDIA_URL


# Serializer for Service model
class ServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = '__all__'

    def get_image(self, obj):
        return obj.image if isinstance(obj.image, str) else None

    def create(self, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().update(instance, validated_data)


class SubServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SubService
        fields = '__all__'

    def get_image(self, obj):
        return obj.image if isinstance(obj.image, str) else None

    def create(self, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().update(instance, validated_data)


class ServiceRequestSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = '__all__'

    def get_image(self, obj):
        return obj.image if isinstance(obj.image, str) else None

    def get_user(self, obj):
        request = self.context.get('request')
        return {
            "id": obj.user.id,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "profile_picture": obj.user.profile_picture,
        }

    def create(self, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().update(instance, validated_data)


# Serializer for ServiceRequestBid model
class ServiceRequestBidSerializer(serializers.ModelSerializer):
    service_provider = serializers.SerializerMethodField()
    service_request = serializers.SerializerMethodField() # Added service_request field

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

    def get_service_request(self, obj): # method to get service request details.
        request = self.context.get('request')
        service_request_data = {
            "id": obj.service_request.id,
            "user": obj.service_request.user.id, # or serialize the user details similarly
            "title": obj.service_request.title,
            "description": obj.service_request.description,
            "image": request.build_absolute_uri(obj.service_request.image.url) if obj.service_request.image and obj.service_request.image.url else None,
            "price": str(obj.service_request.price), # Decimal to String
            "category": obj.service_request.category,
            "status": obj.service_request.status,
            "created_at": obj.service_request.created_at,
            "updated_at": obj.service_request.updated_at,
        }
        return service_request_data

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