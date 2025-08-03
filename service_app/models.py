
from datetime import datetime
from django.db import models

from auth_app.models import User
from provider_app.models import ServiceProvider

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
    ('Others', 'Others'),
]



class Service(models.Model):
    """
    Model representing a service offered by a provider.
    """
    provider: 'ServiceProvider' = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="services",
        help_text="Service provider offering this service"
    )
    name: str = models.CharField(
        max_length=255, help_text="Name of the service"
    )
    description: str = models.TextField(
        help_text="Detailed description of the service"
    )
    image: str = models.URLField(
        null=True, blank=True, help_text="URL to an image representing the service"
    )
    category: str = models.CharField(
        max_length=100, choices=CATEGORIES, help_text="Service category/type"
    )
    min_price: float = models.DecimalField(
        max_digits=16, decimal_places=2, help_text="Minimum price for the service"
    )
    max_price: float = models.DecimalField(
        max_digits=16, decimal_places=2, help_text="Maximum price for the service"
    )
    is_active: bool = models.BooleanField(
        default=True, help_text="Whether the service is currently active"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the service was created"
    )

    def __str__(self) -> str:
        """String representation of the Service."""
        return self.name
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service"
        verbose_name_plural = "Services"



class SubService(models.Model):
    """
    Model representing a sub-service under a main service.
    """
    service: 'Service' = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="sub_services",
        help_text="Main service this sub-service belongs to"
    )
    name: str = models.CharField(
        max_length=255, help_text="Name of the sub-service"
    )
    description: str = models.TextField(
        help_text="Detailed description of the sub-service"
    )
    price: float = models.DecimalField(
        max_digits=16, decimal_places=2, help_text="Price for the sub-service"
    )
    image: str = models.URLField(
        null=True, blank=True, help_text="URL to an image representing the sub-service"
    )
    is_active: bool = models.BooleanField(
        default=True, help_text="Whether the sub-service is currently active"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the sub-service was created"
    )

    def __str__(self) -> str:
        """String representation of the SubService."""
        return f"{self.name} under {self.service.name}"
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sub Service"
        verbose_name_plural = "Sub Services"




class ServiceRequest(models.Model):
    """
    Model representing a user's request for a service.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user: 'User' = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="service_requests",
        help_text="User who made the service request"
    )
    title: str = models.CharField(
        max_length=255, help_text="Title of the service request"
    )
    description: str = models.TextField(
        help_text="Detailed description of the service request"
    )
    image: str = models.URLField(
        null=True, blank=True, help_text="URL to an image for the request (optional)"
    )
    price: float = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Proposed price for the service"
    )
    category: str = models.CharField(
        max_length=100, choices=CATEGORIES, help_text="Category of the requested service"
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending', help_text="Current status of the request"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the service request was created"
    )
    updated_at: datetime = models.DateTimeField(
        auto_now=True, help_text="When the service request was last updated"
    )

    def __str__(self) -> str:
        """String representation of the ServiceRequest."""
        return f"{self.title} by {self.user.email} - {self.status}"



class ServiceRequestBid(models.Model):
    """
    Model representing a bid on a service request by a provider.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Withdrawn', 'Withdrawn'),
    ]

    service_request: 'ServiceRequest' = models.ForeignKey(
        ServiceRequest, on_delete=models.CASCADE, related_name="bids",
        help_text="Service request being bid on"
    )
    service_provider: 'User' = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bids",
        help_text="Provider (user) making the bid"
    )
    price: float = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Bid price offered by the provider"
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending', help_text="Current status of the bid"
    )
    message: str = models.TextField(
        null=True, blank=True, help_text="Optional message from the provider"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the bid was created"
    )

    def __str__(self) -> str:
        """String representation of the ServiceRequestBid."""
        return f"Bid by {self.service_provider.email} - {self.service_request.title} - {self.status}"




class Booking(models.Model):
    """
    Model representing a booking for a service request.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    service_request: 'ServiceRequest' = models.OneToOneField(
        ServiceRequest, on_delete=models.CASCADE, related_name="booking",
        help_text="Service request being booked"
    )
    user: 'User' = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookings_as_user",
        help_text="User who made the booking"
    )
    service_provider: 'User' = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookings_as_provider",
        help_text="Service provider for the booking"
    )
    price: float = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Final agreed price for the booking"
    )
    user_status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending', help_text="User's status for the booking"
    )
    provider_status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending', help_text="Provider's status for the booking"
    )
    feedback: str = models.TextField(
        null=True, blank=True, help_text="Feedback from the user or provider"
    )
    rating: int = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Rating given by the user (1-5)"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the booking was created"
    )
    updated_at: datetime = models.DateTimeField(
        auto_now=True, help_text="When the booking was last updated"
    )

    def __str__(self) -> str:
        """String representation of the Booking."""
        return f"Booking: {self.service_request.title} - {self.user.email} & {self.service_provider.email}"

