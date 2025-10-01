"""
Serializers for service app models.

This module contains serializers for handling data validation and transformation
for service-related models including services, sub-services, requests, bids, and bookings.
"""

from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator

from auth_app.utils import upload_to_cloudinary
from .models import Category, Service, SubService, ServiceRequest, ServiceRequestBid, Booking

import logging

logger = logging.getLogger(__name__)



class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.

    Handles serialization and deserialization of service categories.
    """
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'name': {'required': True},
            'is_active': {'required': False},
        }

    def validate_name(self, value):
        """
        Validate category name.
        Ensures it's not empty and has reasonable length.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Category name cannot be empty.")

        if len(value) > 100:
            raise serializers.ValidationError("Category name is too long. Maximum 100 characters.")

        return value.strip()
    
class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Service model.
    
    Handles service data serialization and deserialization including
    service information, pricing, and image uploads.
    """
    image = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="category",
        write_only=True
    )

    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': True},
            'category': {'required': True},
            'min_price': {'required': True},
            'max_price': {'required': True}
        }

    def get_image(self, obj):
        """
        Get service image URL or None.
        
        Returns the service image URL if it exists, otherwise None.
        """
        return obj.image or None

    def validate_title(self, value):
        """
        Validate service title.
        
        Ensures title is not empty and has reasonable length.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Service title cannot be empty.")
        
        if len(value) > 200:
            raise serializers.ValidationError("Service title is too long. Maximum 200 characters.")
        
        return value.strip()

    def validate_min_price(self, value):
        """
        Validate minimum price.
        
        Ensures minimum price is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Minimum price must be greater than zero.")
        return value

    def validate_max_price(self, value):
        """
        Validate maximum price.
        
        Ensures maximum price is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Maximum price must be greater than zero.")
        return value

    def validate(self, data):
        """
        Validate price range consistency.
        
        Ensures maximum price is greater than or equal to minimum price.
        """
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        
        if min_price and max_price and max_price < min_price:
            raise serializers.ValidationError(
                "Maximum price must be greater than or equal to minimum price."
            )
        
        return data

    def create(self, validated_data):
        """
        Create a new service instance.
        
        Handles service image upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('image')
            
            if image_file:
                validated_data['image'] = upload_to_cloudinary(image_file)
            
            service = super().create(validated_data)
            logger.info(f"Service created: {service.title}")
            return service
            
        except Exception as e:
            logger.error(f"Error creating service: {str(e)}")
            raise serializers.ValidationError(f"Error creating service: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update an existing service instance.
        
        Handles service image upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('image')

            if image_file:
                validated_data['image'] = upload_to_cloudinary(image_file)
            
            service = super().update(instance, validated_data)
            logger.info(f"Service updated: {service.title}")
            return service
            
        except Exception as e:
            logger.error(f"Error updating service: {str(e)}")
            raise serializers.ValidationError(f"Error updating service: {str(e)}")


class SubServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for SubService model.
    
    Handles sub-service data serialization and deserialization including
    sub-service information and image uploads.
    """
    image = serializers.SerializerMethodField()

    class Meta:
        model = SubService
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': True},
            'service': {'required': True}
        }

    def get_image(self, obj):
        """
        Get sub-service image URL or None.
        
        Returns the sub-service image URL if it exists, otherwise None.
        """
        return obj.image or None

    def validate_title(self, value):
        """
        Validate sub-service title.
        
        Ensures title is not empty and has reasonable length.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Sub-service title cannot be empty.")
        
        if len(value) > 200:
            raise serializers.ValidationError("Sub-service title is too long. Maximum 200 characters.")
        
        return value.strip()

    def create(self, validated_data):
        """
        Create a new sub-service instance.
        
        Handles sub-service image upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('image')

            if image_file:
                validated_data['image'] = upload_to_cloudinary(image_file)
            
            sub_service = super().create(validated_data)
            logger.info(f"Sub-service created: {sub_service.title}")
            return sub_service
            
        except Exception as e:
            logger.error(f"Error creating sub-service: {str(e)}")
            raise serializers.ValidationError(f"Error creating sub-service: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update an existing sub-service instance.
        
        Handles sub-service image upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('image')

            if image_file:
                validated_data['image'] = upload_to_cloudinary(image_file)
            
            sub_service = super().update(instance, validated_data)
            logger.info(f"Sub-service updated: {sub_service.title}")
            return sub_service
            
        except Exception as e:
            logger.error(f"Error updating sub-service: {str(e)}")
            raise serializers.ValidationError(f"Error updating sub-service: {str(e)}")


class ServiceRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for ServiceRequest model.
    
    Handles service request data serialization and deserialization including
    request information, user details, and image uploads.
    """
    image = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="category",
        write_only=True
    )

    class Meta:
        model = ServiceRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'status')
        extra_kwargs = {
            'user': {'required': True},
            'title': {'required': True},
            'description': {'required': True},
            'category': {'required': True},
            'price': {'required': True},
            'latitude': {'required': True},
            'longitude': {'required': True},
            'address': {'required': True}
        }

    def get_image(self, obj):
        """
        Get service request image URL or None.
        
        Returns the service request image URL if it exists, otherwise None.
        """
        return obj.image or None

    def get_user(self, obj):
        """
        Get user information for service request.
        
        Returns user data including ID, email, name, and profile picture.
        """
        request = self.context.get('request')
        profile_pic_url = None
        
        if obj.user.profile_picture and hasattr(obj.user.profile_picture, 'url'):
            if request:
                profile_pic_url = request.build_absolute_uri(obj.user.profile_picture.url)
            else:
                profile_pic_url = obj.user.profile_picture.url
        elif isinstance(obj.user.profile_picture, str):
            profile_pic_url = obj.user.profile_picture

        return {
            "id": obj.user.id,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "profile_picture": profile_pic_url,
        }

    def validate_title(self, value):
        """
        Validate service request title.
        
        Ensures title is not empty and has reasonable length.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Service request title cannot be empty.")
        
        if len(value) > 200:
            raise serializers.ValidationError("Service request title is too long. Maximum 200 characters.")
        
        return value.strip()

    def validate_price(self, value):
        """
        Validate service request price.
        
        Ensures price is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def create(self, validated_data):
        """
        Create a new service request instance.
        
        Handles service request image upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('image')

            if image_file:
                validated_data['image'] = upload_to_cloudinary(image_file)
            
            service_request = super().create(validated_data)
            logger.info(f"Service request created: {service_request.title}")
            return service_request
            
        except Exception as e:
            logger.error(f"Error creating service request: {str(e)}")
            raise serializers.ValidationError(f"Error creating service request: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update an existing service request instance.
        
        Handles service request image upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('image')

            if image_file:
                validated_data['image'] = upload_to_cloudinary(image_file)
            
            service_request = super().update(instance, validated_data)
            logger.info(f"Service request updated: {service_request.title}")
            return service_request
            
        except Exception as e:
            logger.error(f"Error updating service request: {str(e)}")
            raise serializers.ValidationError(f"Error updating service request: {str(e)}")


class ServiceRequestBidSerializer(serializers.ModelSerializer):
    """
    Serializer for ServiceRequestBid model.
    
    Handles service request bid data serialization and deserialization including
    bid information, service provider details, and service request details.
    """
    service_provider = serializers.SerializerMethodField()
    service_request = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequestBid
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'service_provider': {'required': True},
            'service_request': {'required': True},
            'bid_amount': {'required': True},
            'proposal': {'required': True},
            'latitude': {'required': True},
            'longitude': {'required': True},
            'address': {'required': True}
        }

    def get_distance_km(self, obj):
        """
        Return distance in kilometers between bid and request.
        """
        distance = obj.calculate_distance_km()
        return distance if distance is not None else None

    def get_service_provider(self, obj):
        """
        Get service provider information for bid.
        
        Returns service provider data including ID, email, name, and profile picture.
        """
        if not obj.service_provider:
            return None

        return {
            "id": obj.service_provider.id,
            "email": obj.service_provider.user.email,
            "first_name": obj.service_provider.user.first_name,
            "last_name": obj.service_provider.user.last_name,
            "company_logo": getattr(obj.service_provider, "company_logo", None),
        }

    def get_service_request(self, obj):
        """
        Get service request information for bid.
        
        Returns service request data including ID, user, title, description, and price.
        """
        return {
            "id": obj.service_request.id,
            "user": obj.service_request.user.id,
            "title": obj.service_request.title,
            "description": obj.service_request.description,
            "image": obj.service_request.image,
            "price": str(obj.service_request.price),
            "category": obj.service_request.category.name,
            "status": obj.service_request.status,
            "created_at": obj.service_request.created_at,
            "updated_at": obj.service_request.updated_at,
        }

    def validate_bid_amount(self, value):
        """
        Validate bid amount.
        
        Ensures bid amount is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Bid amount must be greater than zero.")
        return value

    def validate_proposal(self, value):
        """
        Validate proposal content.
        
        Ensures proposal is not empty and has reasonable length.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Proposal cannot be empty.")
        
        if len(value) > 2000:
            raise serializers.ValidationError("Proposal is too long. Maximum 2000 characters.")
        
        return value.strip()


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for Booking model.

    Handles booking data serialization and deserialization including
    booking information, user details, provider details, and bid details.
    """
    user = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    bid = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'user': {'required': True},
            'provider': {'required': True},
            'bid': {'required': True},
            'amount': {'required': True},
        }

    def get_user(self, obj):
        """Get user information for booking."""
        if not obj.user:
            return None
        return {
            "id": obj.user.id,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "profile_picture": getattr(obj.user, "profile_picture", None),
        }

    def get_provider(self, obj):
        """Get provider information for booking."""
        if not obj.provider:
            return None
        return {
            "id": obj.provider.id,
            "email": obj.provider.user.email,
            "first_name": obj.provider.user.first_name,
            "last_name": obj.provider.user.last_name,
            "company_logo": getattr(obj.provider, "company_logo", None),
            "company_name": getattr(obj.provider, "company_name", None),
        }

    def get_bid(self, obj):
        """Get bid details (amount, proposal, service request)."""
        if not obj.bid:
            return None
        bid = obj.bid
        return {
            "id": bid.id,
            "amount": bid.amount,
            "proposal": bid.proposal,
            "status": bid.status,
            "created_at": bid.created_at,
            "service_request": {
                "id": bid.service_request.id,
                "title": bid.service_request.title,
                "description": bid.service_request.description,
                "category": bid.service_request.category.name,
                "price": bid.service_request.price,
                "status": bid.service_request.status,
            } if bid.service_request else None
        }
