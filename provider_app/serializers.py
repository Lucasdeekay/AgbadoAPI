"""
Serializers for provider app models.

This module contains serializers for handling data validation and transformation
for service provider-related models including company information and business details.
"""

from rest_framework import serializers

from auth_app.utils import upload_to_cloudinary
from service_app.models import Category
from service_app.serializers import CategorySerializer
from .models import ServiceProvider

import logging

logger = logging.getLogger(__name__)


class ServiceProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for ServiceProvider model.
    
    Handles service provider data serialization and deserialization including
    company information, business details, and logo uploads.
    """
    company_logo = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="category",
        write_only=True
    )

    class Meta:
        model = ServiceProvider
        fields = (
            'id', 'user', 'company_name', 'company_address', 'company_description', 
            'company_phone_no', 'company_email', 'business_category', 'company_logo', 
            'opening_hour', 'closing_hour', 'avg_rating', 'rating_population', 
            'is_approved', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'avg_rating', 'rating_population')
        extra_kwargs = {
            'user': {'required': True},
            'company_name': {'required': True},
            'company_address': {'required': True},
            'company_phone_no': {'required': True},
            'company_email': {'required': True},
            'business_category': {'required': True}
        }

    def get_company_logo(self, obj):
        """
        Get company logo URL or None.
        
        Returns the company logo URL if it exists, otherwise None.
        """
        return obj.company_logo or None

    def validate_company_name(self, value):
        """
        Validate company name.
        
        Ensures company name is not empty and has reasonable length.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Company name cannot be empty.")
        
        if len(value) > 200:
            raise serializers.ValidationError("Company name is too long. Maximum 200 characters.")
        
        return value.strip()

    def validate_company_email(self, value):
        """
        Validate company email format.
        
        Ensures email is properly formatted.
        """
        if value and '@' not in value:
            raise serializers.ValidationError("Please enter a valid email address.")
        return value

    def validate_company_phone_no(self, value):
        """
        Validate company phone number.
        
        Ensures phone number has reasonable length.
        """
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number is too short.")
        
        if value and len(value) > 15:
            raise serializers.ValidationError("Phone number is too long.")
        
        return value

    def validate_opening_hour(self, value):
        """
        Validate opening hour format.
        
        Ensures opening hour is in HH:MM format.
        """
        if value:
            try:
                hour, minute = value.split(':')
                hour = int(hour)
                minute = int(minute)
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    raise ValueError
            except (ValueError, AttributeError):
                raise serializers.ValidationError("Opening hour must be in HH:MM format.")
        return value

    def validate_closing_hour(self, value):
        """
        Validate closing hour format.
        
        Ensures closing hour is in HH:MM format.
        """
        if value:
            try:
                hour, minute = value.split(':')
                hour = int(hour)
                minute = int(minute)
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    raise ValueError
            except (ValueError, AttributeError):
                raise serializers.ValidationError("Closing hour must be in HH:MM format.")
        return value

    def validate(self, data):
        """
        Validate business hours consistency.
        
        Ensures closing hour is after opening hour.
        """
        opening_hour = data.get('opening_hour')
        closing_hour = data.get('closing_hour')
        
        if opening_hour and closing_hour:
            try:
                opening_time = int(opening_hour.replace(':', ''))
                closing_time = int(closing_hour.replace(':', ''))
                if closing_time <= opening_time:
                    raise serializers.ValidationError(
                        "Closing hour must be after opening hour."
                    )
            except (ValueError, AttributeError):
                pass  # Let individual field validators handle format errors
        
        return data

    def create(self, validated_data):
        """
        Create a new service provider instance.
        
        Handles company logo upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('company_logo')

            if image_file:
                image_url = upload_to_cloudinary(image_file)
                validated_data['company_logo'] = image_url
                
            service_provider = super().create(validated_data)
            logger.info(f"Service provider created: {service_provider.company_name}")
            return service_provider
            
        except Exception as e:
            logger.error(f"Error creating service provider: {str(e)}")
            raise serializers.ValidationError(f"Error creating service provider: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update an existing service provider instance.
        
        Handles company logo upload to Cloudinary.
        """
        try:
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('company_logo')

            if image_file:
                image_url = upload_to_cloudinary(image_file)
                validated_data['company_logo'] = image_url

            service_provider = super().update(instance, validated_data)
            logger.info(f"Service provider updated: {service_provider.company_name}")
            return service_provider
            
        except Exception as e:
            logger.error(f"Error updating service provider: {str(e)}")
            raise serializers.ValidationError(f"Error updating service provider: {str(e)}")


class ServiceProviderListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing service providers.
    
    Provides a simplified view of service providers for list endpoints
    with optimized field selection.
    """
    
    class Meta:
        model = ServiceProvider
        fields = (
            'id', 'company_name', 'business_category', 'company_logo', 
            'avg_rating', 'rating_population', 'is_approved', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'avg_rating', 'rating_population')


class ServiceProviderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed service provider view.
    
    Provides comprehensive service provider information including
    user details and full business information.
    """
    
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceProvider
        fields = (
            'id', 'user', 'user_email', 'user_name', 'company_name', 
            'company_address', 'company_description', 'company_phone_no',
            'company_email', 'business_category', 'company_logo', 
            'opening_hour', 'closing_hour', 'avg_rating', 'rating_population',
            'is_approved', 'created_at'
        )
        read_only_fields = (
            'id', 'created_at', 'avg_rating', 'rating_population', 
            'user_email', 'user_name'
        )

    def get_user_name(self, obj):
        """
        Get user's full name.
        
        Returns the user's full name or email if name is not available.
        """
        return obj.user.get_full_name() if obj.user else None

    def get_company_logo(self, obj):
        """
        Get company logo URL or None.
        
        Returns the company logo URL if it exists, otherwise None.
        """
        return obj.company_logo or None