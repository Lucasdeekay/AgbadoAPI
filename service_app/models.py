from django.db import models

from auth_app.models import User
from provider_app.models import ServiceProvider


class Service(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='service_images/', null=True, blank=True)
    category = models.CharField(max_length=100)
    min_price = models.DecimalField()
    max_price = models.DecimalField()
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
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="service_requests")
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="service_requests/", null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="service_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.user.email} - {self.status}"

class ServiceRequestBid(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Withdrawn', 'Withdrawn'),
    ]

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="bids")
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid by {self.service_provider.email} - {self.service_request.title} - {self.status}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name="booking")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings_as_user")
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings_as_provider")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    user_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    provider_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    feedback = models.TextField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1 to 5 rating
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking: {self.service_request.title} - {self.user.email} & {self.service_provider.email}"

