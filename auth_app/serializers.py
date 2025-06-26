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
    # These should NOT be SerializerMethodField if you want to write to them.
    # They should correspond to the model fields directly.
    # We will handle the file upload logic in create/update.

    class Meta:
        model = KYC
        fields = (
            'user', 'national_id', 'bvn', 'driver_license', 'proof_of_address',
            'status', 'updated_at', 'verified_at'
        )
        # Add extra_kwargs if you want to make these fields explicitly write_only
        # which is common for file uploads where the client sends a file,
        # but the API returns a URL.
        extra_kwargs = {
            'national_id': {'write_only': True, 'required': False},
            'driver_license': {'write_only': True, 'required': False},
            'proof_of_address': {'write_only': True, 'required': False},
        }

    # Helper method to get the file and upload
    def _handle_file_upload(self, field_name, validated_data):
        request = self.context.get('request')
        if request and request.FILES:
            file = request.FILES.get(field_name)
            if file:
                # If a file is provided, upload it and update validated_data
                url = upload_to_cloudinary(file)
                if url:
                    validated_data[field_name] = url
                # If upload fails, you might want to raise a validation error
                # else:
                #    raise serializers.ValidationError({field_name: "File upload failed."})
            elif field_name in request.data:
                # This handles cases where the client sends field_name=null to explicitly clear it
                # Only if you want to allow clearing files this way
                if request.data.get(field_name) is None:
                    validated_data[field_name] = None
                # If field_name is present in request.data but not in request.FILES, and not null,
                # it means the client might have sent a URL directly. This is generally not
                # recommended for upload fields, but if allowed, add logic here.
        # If no file is provided, and the field is not in request.data (i.e., not explicitly cleared),
        # we do nothing, letting the existing value persist for updates.

    def create(self, validated_data):
        # Handle file uploads *before* calling super().create
        self._handle_file_upload('national_id', validated_data)
        self._handle_file_upload('driver_license', validated_data)
        self._handle_file_upload('proof_of_address', validated_data)

        # The 'bvn' field should be present in validated_data if sent by the client.
        # Since it's a regular ModelSerializer field, DRF handles its validation and inclusion automatically.

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle file uploads *before* calling super().update
        # Note: If a file is NOT provided in the update request, we do *not*
        # want to overwrite the existing instance's URL with None.
        # So, we remove it from validated_data if no new file was uploaded.

        for field in ['national_id', 'driver_license', 'proof_of_address']:
            request = self.context.get('request')
            if request and request.FILES and request.FILES.get(field):
                # Only process if a new file is actually provided
                file = request.FILES.get(field)
                url = upload_to_cloudinary(file)
                if url:
                    validated_data[field] = url
                else:
                    # If upload failed for a new file, remove it from validated_data
                    validated_data.pop(field, None)
                    # Optionally, raise an error here if upload is mandatory
            elif field in validated_data and validated_data[field] is None:
                # This handles explicit clearing by sending field: null in the JSON body
                # If you don't want to allow clearing via JSON null, remove this block.
                pass # validated_data[field] is already None, no action needed for update to clear it.
            else:
                # If the field was not provided in FILES and not explicitly sent as null in JSON,
                # we don't want to update it. Remove it from validated_data to prevent clearing.
                validated_data.pop(field, None)

        # The 'bvn' field should be handled automatically by ModelSerializer
        # unless it's explicitly popped or manipulated.

        return super().update(instance, validated_data)

    # These get_ methods are for outputting the URLs when serializing (reading).
    # If your model fields already store the URLs, you don't strictly need these
    # unless you want to format them differently or handle cases where they might be empty.
    # If the model fields store files directly (e.g., ImageField), then these are needed
    # to convert the file path to a full URL. Assuming they store URLs directly here.
    def get_national_id(self, obj):
        # Assuming obj.national_id is already the URL or None
        return obj.national_id if obj.national_id else None

    def get_driver_license(self, obj):
        return obj.driver_license if obj.driver_license else None

    def get_proof_of_address(self, obj):
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