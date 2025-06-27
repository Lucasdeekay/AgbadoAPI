from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone

from rest_framework import serializers

from auth_app.utils import upload_to_cloudinary
from .models import User, KYC, OTP, Referral


# Serializer for User model
class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True}}

    def get_profile_picture(self, obj):
        return obj.profile_picture or None  # fallback if it's already a URL string or None

    def create(self, validated_data):
        # Check if 'profile_picture' was sent in the FILES dictionary before attempting to get it
        image_file = None
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('profile_picture')

        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['profile_picture'] = image_url
        
        # Remove password from validated_data if it's there and create user with create_user
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        # Check if 'profile_picture' was sent in the FILES dictionary before attempting to get it
        image_file = None
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('profile_picture')

        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['profile_picture'] = image_url
        
        # Handle password update separately if it's in validated_data
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # Update other fields using super().update
        updated_instance = super().update(instance, validated_data)
        updated_instance.save() # Save the instance after password set
        return updated_instance


class KYCSerializer(serializers.ModelSerializer):
    # These fields are defined as SerializerMethodField for output purposes.
    # File upload logic for these will be handled manually in create/update methods,
    # just like the profile_picture in UserSerializer.
    national_id = serializers.SerializerMethodField()
    driver_license = serializers.SerializerMethodField()
    proof_of_address = serializers.SerializerMethodField()

    class Meta:
        model = KYC
        fields = (
            'user', 'national_id', 'bvn', 'driver_license', 'proof_of_address',
            'status', 'updated_at', 'verified_at'
        )
        # extra_kwargs are NOT needed for SerializerMethodField as they are read-only by default.
        # Removing the extra_kwargs for national_id, driver_license, proof_of_address.
        # This was part of the earlier attempt to make them writeable as regular fields,
        # but with SerializerMethodField, they are read-only for input.

    def create(self, validated_data):
        request = self.context.get('request')

        # Handle national_id upload
        national_id_file = None
        if request and request.FILES:
            national_id_file = request.FILES.get('national_id')
        if national_id_file:
            national_id_url = upload_to_cloudinary(national_id_file)
            validated_data['national_id'] = national_id_url
        else:
            validated_data.pop('national_id', None) # Remove if not provided

        # Handle driver_license upload
        driver_license_file = None
        if request and request.FILES:
            driver_license_file = request.FILES.get('driver_license')
        if driver_license_file:
            driver_license_url = upload_to_cloudinary(driver_license_file)
            validated_data['driver_license'] = driver_license_url
        else:
            validated_data.pop('driver_license', None) # Remove if not provided

        # Handle proof_of_address upload
        proof_of_address_file = None
        if request and request.FILES:
            proof_of_address_file = request.FILES.get('proof_of_address')
        if proof_of_address_file:
            proof_of_address_url = upload_to_cloudinary(proof_of_address_file)
            validated_data['proof_of_address'] = proof_of_address_url
        else:
            validated_data.pop('proof_of_address', None) # Remove if not provided

        # The 'bvn' field and other non-file fields will be automatically handled
        # by ModelSerializer's default create method from validated_data.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Handle national_id upload
        national_id_file = None
        if request and request.FILES:
            national_id_file = request.FILES.get('national_id')
        if national_id_file:
            national_id_url = upload_to_cloudinary(national_id_file)
            validated_data['national_id'] = national_id_url
        elif 'national_id' in validated_data and validated_data['national_id'] is None:
            # If client explicitly sent 'national_id': null to clear it
            pass
        else:
            # If no new file was uploaded AND the field wasn't explicitly set to null,
            # remove it from validated_data to prevent accidentally clearing existing value.
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

        # The 'bvn' field and other non-file fields will be automatically handled
        # by ModelSerializer's default update method.
        return super().update(instance, validated_data)

    def get_national_id(self, obj):
        # This method is for serializing (outputting) the national_id URL.
        return obj.national_id if obj.national_id else None

    def get_driver_license(self, obj):
        # This method is for serializing (outputting) the driver_license URL.
        return obj.driver_license if obj.driver_license else None

    def get_proof_of_address(self, obj):
        # This method is for serializing (outputting) the proof_of_address URL.
        return obj.proof_of_address if obj.proof_of_address else None
    
class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = "__all__"


class ReferralSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    referer = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = "__all__"

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

    def get_referer(self, obj):
        request = self.context.get('request')
        referer_data = {
            "id": obj.referer.id,
            "email": obj.referer.email,
            "first_name": obj.referer.first_name,
            "last_name": obj.referer.last_name,
            "profile_picture": obj.referer.profile_picture,
        }
        return referer_data