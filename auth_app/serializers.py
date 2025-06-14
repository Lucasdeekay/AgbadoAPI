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
        request = self.context.get('request')
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return request.build_absolute_uri(obj.profile_picture.url)
        return obj.profile_picture  # fallback if it's already a URL string

    def create(self, validated_data):
        image_file = self.context['request'].FILES.get('profile_picture')
        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['profile_picture'] = image_url
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        image_file = self.context['request'].FILES.get('profile_picture')
        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['profile_picture'] = image_url
        return super().update(instance, validated_data)


class KYCSerializer(serializers.ModelSerializer):
    national_id = serializers.SerializerMethodField()
    driver_license = serializers.SerializerMethodField()
    proof_of_address = serializers.SerializerMethodField()

    class Meta:
        model = KYC
        fields = "__all__"

    def _upload_file(self, field_name):
        file = self.context['request'].FILES.get(field_name)
        return upload_to_cloudinary(file) if file else None

    def create(self, validated_data):
        for field in ['national_id', 'driver_license', 'proof_of_address']:
            url = self._upload_file(field)
            if url:
                validated_data[field] = url
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for field in ['national_id', 'driver_license', 'proof_of_address']:
            url = self._upload_file(field)
            if url:
                validated_data[field] = url
        return super().update(instance, validated_data)

    def get_national_id(self, obj):
        return obj.national_id

    def get_driver_license(self, obj):
        return obj.driver_license

    def get_proof_of_address(self, obj):
        return obj.proof_of_address


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
            "profile_picture": request.build_absolute_uri(obj.user.profile_picture.url) if obj.user.profile_picture and obj.user.profile_picture.url else None,
        }
        return user_data

    def get_referer(self, obj):
        request = self.context.get('request')
        referer_data = {
            "id": obj.referer.id,
            "email": obj.referer.email,
            "first_name": obj.referer.first_name,
            "last_name": obj.referer.last_name,
            "profile_picture": request.build_absolute_uri(obj.referer.profile_picture.url) if obj.referer.profile_picture and obj.referer.profile_picture.url else None,
        }
        return referer_data