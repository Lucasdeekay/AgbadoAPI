from django.db import models

from auth_app.models import User

CATEGORIES = [
    ('Electrical', 'Electrical'),
    ('Automobile', 'Automobile'),
    ('Carpentry', 'Carpentry'),
    ('Cleaning', 'Cleaning'),
    ('Plumbing', 'Plumbing'),
    ('Fumigation', 'Fumigation'),
    ('Legal', 'Legal'),
    ('Healthcare', 'Healthcare'),
    ('Fashion', 'Fashion'),
    ('Shopping', 'Shopping'),
    ('Construction', 'Construction'),
    ('Fitness', 'Fitness'),
    ('Engineering', 'Engineering'),
    ('Education', 'Education'),
]

class ServiceProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="provider_profile")
    company_name = models.CharField(max_length=255)
    company_address = models.TextField()
    company_description = models.TextField()
    company_phone_no = models.CharField(max_length=20)
    company_email = models.EmailField()
    business_category = models.CharField(max_length=100, choices=CATEGORIES)  # Updated to use choices
    company_logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    opening_hour = models.CharField(max_length=10)
    closing_hour = models.CharField(max_length=10)
    avg_rating = models.PositiveIntegerField(default=0, null=True, blank=True)
    rating_population = models.PositiveIntegerField(default=0, null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # Indicates admin approval for service providers
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name