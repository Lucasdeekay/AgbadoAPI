from rest_framework import serializers
from .models import ServiceProvider


# Serializer for ServiceProvider model
class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = (
        'user', 'company_name', 'company_address', 'contact_info', 'business_category', 'company_logo', 'is_approved', 'created_at')
