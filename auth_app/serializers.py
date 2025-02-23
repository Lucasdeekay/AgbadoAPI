from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone

from rest_framework import serializers
from .models import User, KYC, OTP, Referral


# Serializer for User model
class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def get_profile_picture(self, obj):
        request = self.context.get('request')
        if obj.profile_picture and obj.profile_picture.url:
            return request.build_absolute_uri(obj.profile_picture.url)
        return None


# Serializer for KYC model
class KYCSerializer(serializers.ModelSerializer):
    national_id = serializers.SerializerMethodField()
    driver_license = serializers.SerializerMethodField()
    proof_of_address = serializers.SerializerMethodField()

    class Meta:
        model = KYC
        fields = "__all__"

    def get_national_id(self, obj):
        request = self.context.get('request')
        if obj.national_id and obj.national_id.url:
            return request.build_absolute_uri(obj.national_id.url)
        return None

    def get_driver_license(self, obj):
        request = self.context.get('request')
        if obj.driver_license and obj.driver_license.url:
            return request.build_absolute_uri(obj.driver_license.url)
        return None

    def get_proof_of_address(self, obj):
        request = self.context.get('request')
        if obj.proof_of_address and obj.proof_of_address.url:
            return request.build_absolute_uri(obj.proof_of_address.url)
        return None


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