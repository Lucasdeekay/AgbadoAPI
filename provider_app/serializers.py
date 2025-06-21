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
        return obj.company_logo or None  # fallback if already a URL string or None

    def create(self, validated_data):
        image_file = None
        # Check if 'request' and 'FILES' exist in context before accessing
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('company_logo')

        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['company_logo'] = image_url
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = None
        # Check if 'request' and 'FILES' exist in context before accessing
        if 'request' in self.context and self.context['request'].FILES:
            image_file = self.context['request'].FILES.get('company_logo')

        if image_file:
            image_url = upload_to_cloudinary(image_file)
            validated_data['company_logo'] = image_url
        # If image_file is None (meaning no new file was provided),
        # we don't want to accidentally set company_logo to None in validated_data
        # if it wasn't explicitly sent. So, we'll let super().update handle it
        # which will only update if the field is present in validated_data.
        # If you specifically want to allow clients to *clear* the logo by sending
        # a null or empty string for 'company_logo' in the *regular* data,
        # you'd handle that separately, but for file uploads, this is standard.

        return super().update(instance, validated_data)