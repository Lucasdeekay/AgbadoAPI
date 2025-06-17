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
        return obj.image # Returns the string URL or None if not set/not a file

    def create(self, validated_data):
        image_file = None
        # Safely check if 'request' and 'FILES' exist in context
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('image')
        
        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = None
        # Safely check if 'request' and 'FILES' exist in context
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('image')

        if image_file:
            # Only update the image if a new file is provided
            validated_data['image'] = upload_to_cloudinary(image_file)
        # Important: If image_file is None, we intentionally *do not* add 'image' to validated_data
        # unless it was explicitly sent as None in the main request body. This prevents
        # unintentionally clearing the image if the client simply didn't send a new one.
        
        return super().update(instance, validated_data)


class SubServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SubService
        fields = '__all__'

    def get_image(self, obj):
        return obj.image

    def create(self, validated_data):
        image_file = None
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('image')

        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = None
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('image')

        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        
        return super().update(instance, validated_data)


class ServiceRequestSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField() # This will now return full user data

    class Meta:
        model = ServiceRequest
        fields = '__all__'

    def get_image(self, obj):
        return obj.image

    def get_user(self, obj):
        request = self.context.get('request')
        # Ensure profile_picture URL is built correctly, handling None
        profile_pic_url = None
        if obj.user.profile_picture and hasattr(obj.user.profile_picture, 'url'):
            if request:
                profile_pic_url = request.build_absolute_uri(obj.user.profile_picture.url)
            else:
                profile_pic_url = obj.user.profile_picture.url # Fallback to relative URL
        elif isinstance(obj.user.profile_picture, str): # If it's already a string URL
            profile_pic_url = obj.user.profile_picture

        return {
            "id": obj.user.id,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "profile_picture": profile_pic_url, # Now includes the full URL
        }

    def create(self, validated_data):
        image_file = None
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('image')

        if image_file:
            validated_data['image'] = upload_to_cloudinary(image_file)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = None
        if 'request' in self.context and self.context['request'].FILES:
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
            "image": obj.service_request.image,
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
            "profile_picture": obj.user.profile_picture,
        }
        return user_data

    def get_service_provider(self, obj):
        request = self.context.get('request')
        provider_data = {
            "id": obj.service_provider.id,
            "email": obj.service_provider.email,
            "first_name": obj.service_provider.first_name,
            "last_name": obj.service_provider.last_name,
            "profile_picture": obj.service_provider.profile_picture,
        }
        return provider_data