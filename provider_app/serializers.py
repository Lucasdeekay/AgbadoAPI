from rest_framework import serializers
from .models import ServiceProvider


# Serializer for ServiceProvider model
class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = (
            'user', 'company_name', 'company_address', 'company_description', 'company_phone_no',
            'company_email', 'business_category', 'company_logo', 'opening_hour', 'closing_hour',
            'avg_rating', 'rating_population', 'is_approved', 'created_at'
        )
