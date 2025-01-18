from rest_framework import serializers
from .models import User, KYC, OTP, Referral


# Serializer for User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Handle user creation, password hashing and return the user instance
        user = User.objects.create_user(**validated_data)
        return user


# Serializer for KYC model
class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = (
            'user', 'status', 'national_id', 'bvn', 'driver_license', 'proof_of_address', 'updated_at', 'verified_at')


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('user', 'otp', 'created_at', 'is_used')

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = ('user', 'referer', 'created_at',)
