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
    national_id = serializers.SerializerMethodField()
    driver_license = serializers.SerializerMethodField()
    proof_of_address = serializers.SerializerMethodField()

    class Meta:
        model = KYC
        fields = (
            'user', 'national_id', 'bvn', 'driver_license', 'proof_of_address',
            'status', 'updated_at', 'verified_at'
        )

    def _upload_file(self, field_name):
        # Check if the request context and FILES exist before trying to get the file
        if 'request' in self.context and self.context['request'].FILES:
            file = self.context['request'].FILES.get(field_name)
            return upload_to_cloudinary(file) if file else None
        return None

    def create(self, validated_data):
        for field in ['national_id', 'driver_license', 'proof_of_address']:
            url = self._upload_file(field)
            if url:
                validated_data[field] = url
            # If no file was uploaded for a field, ensure it's not trying to set None
            # which might overwrite existing values if that's not the intent.
            # However, since KYC documents are typically set once, setting None might be okay.
            # If the intent is *not* to clear a field if no new file is provided,
            # then remove the `else:` block and only set `validated_data[field]` if `url` is not None.
            # The current logic will set it to None if `_upload_file` returns None,
            # which is what `get()` does if the file wasn't present.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for field in ['national_id', 'driver_license', 'proof_of_address']:
            url = self._upload_file(field)
            if url:
                validated_data[field] = url
            # If no file was uploaded for a field, it means the client didn't send it.
            # We should generally *not* update the field if no new file was provided,
            # to prevent accidentally clearing existing values.
            # So, only update if `url` is not None, meaning a new file was uploaded.
            elif field in validated_data and validated_data[field] is None:
                # This 'elif' case handles if the client explicitly sent 'null' for a field.
                # If you want to allow clearing a field by explicitly sending null, keep this.
                # Otherwise, remove it. For file fields, typically you only update if a new file is sent.
                pass 
            else:
                # Remove from validated_data to prevent super().update from setting it to None
                # if the client didn't send a new file for this field.
                validated_data.pop(field, None)
        return super().update(instance, validated_data)

    def get_national_id(self, obj):
       return obj.national_id or None  # Return None if the field is empty

    def get_driver_license(self, obj):
        return obj.driver_license or None  # Return None if the field is empty

    def get_proof_of_address(self, obj):
        return obj.proof_of_address or None  # Return None if the field is empty


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