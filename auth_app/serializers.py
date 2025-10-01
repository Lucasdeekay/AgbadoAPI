"""
Serializers for auth app models.

This module contains serializers for handling data validation and transformation
for authentication-related models including users, KYC, OTP, and referrals.
"""

from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone

from rest_framework import serializers

from auth_app.utils import upload_to_cloudinary, generate_unique_referral_code
from wallet_app.services import update_bvn_on_reserved_account
from .models import User, KYC, OTP, Referral

import logging

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Handles user data serialization and deserialization including
    profile picture uploads and referral code generation.
    """
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'phone_number': {'required': True}
        }

    def get_profile_picture(self, obj):
        """
        Get profile picture URL or None.
        
        Returns the profile picture URL if it exists, otherwise None.
        """
        return obj.profile_picture or None

    def validate_email(self, value):
        """
        Validate email uniqueness.
        
        Ensures the email is unique across all users.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone_number(self, value):
        """
        Validate phone number uniqueness.
        
        Ensures the phone number is unique across all users.
        """
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        """
        Create a new user instance.
        
        Handles profile picture upload and referral code generation.
        """
        try:
            # Check if 'profile_picture' was sent in the FILES dictionary
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('profile_picture')

            if image_file:
                image_url = upload_to_cloudinary(image_file)
                validated_data['profile_picture'] = image_url
            
            # Generate unique referral code if not provided
            if not validated_data.get('referral_code'):
                validated_data['referral_code'] = generate_unique_referral_code()
            
            # Remove password from validated_data and create user
            password = validated_data.pop('password', None)
            user = User.objects.create(**validated_data)
            if password:
                user.set_password(password)
                user.save()
            
            logger.info(f"User created successfully: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise serializers.ValidationError(f"Error creating user: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update an existing user instance.
        
        Handles profile picture upload and password updates.
        """
        try:
            # Check if 'profile_picture' was sent in the FILES dictionary
            image_file = None
            if 'request' in self.context and self.context['request'].FILES:
                image_file = self.context['request'].FILES.get('profile_picture')

            if image_file:
                image_url = upload_to_cloudinary(image_file)
                validated_data['profile_picture'] = image_url
            
            # Handle password update separately
            password = validated_data.pop('password', None)
            if password:
                instance.set_password(password)

            # Update other fields
            updated_instance = super().update(instance, validated_data)
            updated_instance.save()
            
            logger.info(f"User updated successfully: {updated_instance.email}")
            return updated_instance
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise serializers.ValidationError(f"Error updating user: {str(e)}")


class KYCSerializer(serializers.ModelSerializer):
    """
    Serializer for KYC model.
    
    Handles KYC document uploads and validation including
    national ID, driver license, and proof of address.
    """
    national_id = serializers.SerializerMethodField()
    driver_license = serializers.SerializerMethodField()
    proof_of_address = serializers.SerializerMethodField()

    class Meta:
        model = KYC
        fields = (
            'user', 'national_id', 'bvn', 'driver_license', 'proof_of_address',
            'status', 'updated_at', 'verified_at'
        )
        read_only_fields = ('updated_at', 'verified_at')

    def validate_bvn(self, value):
        """
        Validate BVN format.
        
        Ensures BVN is exactly 11 digits.
        """
        if value and len(str(value)) != 11:
            raise serializers.ValidationError("BVN must be exactly 11 digits.")
        return value

    def create(self, validated_data):
        """
        Create a new KYC instance.
        
        Handles document uploads to Cloudinary.
        """
        try:
            request = self.context.get('request')

            # Handle national_id upload
            national_id_file = None
            if request and request.FILES:
                national_id_file = request.FILES.get('national_id')
            if national_id_file:
                national_id_url = upload_to_cloudinary(national_id_file)
                validated_data['national_id'] = national_id_url
            else:
                validated_data.pop('national_id', None)

            # Handle driver_license upload
            driver_license_file = None
            if request and request.FILES:
                driver_license_file = request.FILES.get('driver_license')
            if driver_license_file:
                driver_license_url = upload_to_cloudinary(driver_license_file)
                validated_data['driver_license'] = driver_license_url
            else:
                validated_data.pop('driver_license', None)

            # Handle proof_of_address upload
            proof_of_address_file = None
            if request and request.FILES:
                proof_of_address_file = request.FILES.get('proof_of_address')
            if proof_of_address_file:
                proof_of_address_url = upload_to_cloudinary(proof_of_address_file)
                validated_data['proof_of_address'] = proof_of_address_url
            else:
                validated_data.pop('proof_of_address', None)

            kyc = super().create(validated_data)
            bvn = validated_data.get("bvn")

            if bvn:
                try:
                    update_bvn_on_reserved_account(kyc.user, bvn)
                except ValueError as e:
                    # surface the error but do NOT roll back KYC
                    raise serializers.ValidationError({"bvn": str(e)})
            logger.info(f"KYC created successfully for user: {kyc.user.email}")
            return kyc
            
        except Exception as e:
            logger.error(f"Error creating KYC: {str(e)}")
            raise serializers.ValidationError(f"Error creating KYC: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update an existing KYC instance.
        
        Handles document uploads to Cloudinary.
        """
        try:
            request = self.context.get('request')

            # Handle national_id upload
            national_id_file = None
            if request and request.FILES:
                national_id_file = request.FILES.get('national_id')
            if national_id_file:
                national_id_url = upload_to_cloudinary(national_id_file)
                validated_data['national_id'] = national_id_url
            elif 'national_id' in validated_data and validated_data['national_id'] is None:
                pass
            else:
                validated_data.pop('national_id', None)

            # Handle driver_license upload
            driver_license_file = None
            if request and request.FILES:
                driver_license_file = request.FILES.get('driver_license')
            if driver_license_file:
                driver_license_url = upload_to_cloudinary(driver_license_file)
                validated_data['driver_license'] = driver_license_url
            elif 'driver_license' in validated_data and validated_data['driver_license'] is None:
                pass
            else:
                validated_data.pop('driver_license', None)

            # Handle proof_of_address upload
            proof_of_address_file = None
            if request and request.FILES:
                proof_of_address_file = request.FILES.get('proof_of_address')
            if proof_of_address_file:
                proof_of_address_url = upload_to_cloudinary(proof_of_address_file)
                validated_data['proof_of_address'] = proof_of_address_url
            elif 'proof_of_address' in validated_data and validated_data['proof_of_address'] is None:
                pass
            else:
                validated_data.pop('proof_of_address', None)

            kyc = super().update(instance, validated_data)
            old_bvn = instance.bvn
            instance = super().update(instance, validated_data)
            new_bvn = instance.bvn

            if new_bvn and new_bvn != old_bvn:
                try:
                    update_bvn_on_reserved_account(instance.user, new_bvn)
                except ValueError as e:
                    raise serializers.ValidationError({"bvn": str(e)})
            logger.info(f"KYC updated successfully for user: {kyc.user.email}")
            return kyc
            
        except Exception as e:
            logger.error(f"Error updating KYC: {str(e)}")
            raise serializers.ValidationError(f"Error updating KYC: {str(e)}")

    def get_national_id(self, obj):
        """
        Get national ID URL.
        
        Returns the national ID URL if it exists, otherwise None.
        """
        return obj.national_id if obj.national_id else None

    def get_driver_license(self, obj):
        """
        Get driver license URL.
        
        Returns the driver license URL if it exists, otherwise None.
        """
        return obj.driver_license if obj.driver_license else None

    def get_proof_of_address(self, obj):
        """
        Get proof of address URL.
        
        Returns the proof of address URL if it exists, otherwise None.
        """
        return obj.proof_of_address if obj.proof_of_address else None


class OTPSerializer(serializers.ModelSerializer):
    """
    Serializer for OTP model.
    
    Handles OTP data serialization and validation.
    """
    class Meta:
        model = OTP
        fields = "__all__"
        read_only_fields = ('created_at', 'expires_at')

    def validate_otp(self, value):
        """
        Validate OTP format.
        
        Ensures OTP is exactly 6 digits.
        """
        if len(str(value)) != 6:
            raise serializers.ValidationError("OTP must be exactly 6 digits.")
        return value


class ReferralSerializer(serializers.ModelSerializer):
    """
    Serializer for Referral model.
    
    Includes nested user and referer information for complete referral tracking.
    """
    user = serializers.SerializerMethodField()
    referer = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = "__all__"
        read_only_fields = ('created_at',)

    def get_user(self, obj):
        """
        Get user information.
        
        Returns user data including ID, email, name, and profile picture.
        """
        user_data = {
            "id": obj.user.id,
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "profile_picture": obj.user.profile_picture,
        }
        return user_data

    def get_referer(self, obj):
        """
        Get referer information.
        
        Returns referer data including ID, email, name, and profile picture.
        """
        referer_data = {
            "id": obj.referer.id,
            "email": obj.referer.email,
            "first_name": obj.referer.first_name,
            "last_name": obj.referer.last_name,
            "profile_picture": obj.referer.profile_picture,
        }
        return referer_data