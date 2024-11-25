from django.db import models

from auth_app.models import User
from provider_app.models import ServiceProvider


class Service(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='service_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SubService(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="sub_services")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='subservice_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} under {self.service.name}"

class ServiceRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="service_requests")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'),
                                                     ('in_progress', 'In Progress'), ('completed', 'Completed')],
                             default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Service Request by {self.user.email} - Status: {self.status}"
