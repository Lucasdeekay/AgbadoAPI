from django.db import models

from auth_app.models import User


class ServiceProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="provider_profile")
    company_name = models.CharField(max_length=255)
    company_address = models.TextField()
    contact_info = models.CharField(max_length=50)
    business_category = models.CharField(max_length=100)
    company_logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # Indicates admin approval for service providers
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name