from rest_framework import serializers
from .models import ServiceProvider


# Serializer for ServiceProvider model
class ServiceProviderSerializer(serializers.ModelSerializer):
    company_logo = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProvider
        fields = (
            'user', 'company_name', 'company_address', 'company_description', 'company_phone_no',
            'company_email', 'business_category', 'company_logo', 'opening_hour', 'closing_hour',
            'avg_rating', 'rating_population', 'is_approved', 'created_at'
        )

    def get_company_logo(self, obj):
        request = self.context.get('request')
        if obj.company_logo and obj.company_logo.url:
            return request.build_absolute_uri(obj.company_logo.url)
        return None