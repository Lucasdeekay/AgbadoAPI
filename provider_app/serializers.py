from rest_framework import serializers

from auth_app.utils import upload_to_cloudinary
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
        if obj.company_logo and hasattr(obj.company_logo, 'url'):
            return request.build_absolute_uri(obj.company_logo.url)
        return obj.company_logo  # fallback if already a URL string

    def create(self, validated_data):
        image_file = self.context['request'].FILES.get('company_logo')
        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['company_logo'] = image_url
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = self.context['request'].FILES.get('company_logo')
        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['company_logo'] = image_url
        return super().update(instance, validated_data)