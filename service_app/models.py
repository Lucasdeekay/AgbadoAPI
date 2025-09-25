"""
Service app models for service management.

This module contains models for managing services, subservices, service requests,
bids, and bookings with comprehensive business logic and helper methods.
"""

from datetime import datetime
import math
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from auth_app.models import User

class Category(models.Model):
    """
    Model representing service categories.

    Prefilled with common categories such as Electrical, Automobile, Carpentry, etc.
    Allows dynamic management instead of hardcoded choices.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the category (e.g., Electrical, Plumbing)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is currently active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the category was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the category was last updated"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    @classmethod
    def prefill_defaults(cls):
        """
        Prefill the database with default categories.
        Call this in a migration, signal, or Django shell.
        """
        default_categories = [
            "Electrical", "Automobile", "Carpentry", "Cleaning", "Plumbing",
            "Fumigation", "Legal", "Healthcare", "Fashion", "Shopping",
            "Construction", "Fitness", "Engineering", "Education", "Others",
        ]
        for cat in default_categories:
            cls.objects.get_or_create(name=cat)

class Service(models.Model):
    """
    Model representing a service offered by a provider.
    
    Manages service information including pricing, categories,
    availability status, and provider details.
    """
    provider = models.ForeignKey(
        "provider_app.ServiceProvider", 
        on_delete=models.CASCADE, 
        related_name="services",
        help_text="Service provider offering this service"
    )
    name = models.CharField(
        max_length=255, 
        help_text="Name of the service"
    )
    description = models.TextField(
        help_text="Detailed description of the service"
    )
    image = models.URLField(
        null=True, 
        blank=True, 
        help_text="URL to an image representing the service"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="services",
        help_text="Category of the service"
    )
    min_price = models.DecimalField(
        max_digits=16, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Minimum price for the service"
    )
    max_price = models.DecimalField(
        max_digits=16, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Maximum price for the service"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether the service is currently active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the service was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="When the service was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service"
        verbose_name_plural = "Services"
        indexes = [
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['min_price', 'max_price']),
        ]

    def __str__(self) -> str:
        """String representation of the Service."""
        return f"{self.name} by {self.provider.company_name}"

    def get_price_range_display(self):
        """
        Get formatted price range display.
        
        Returns:
            str: Formatted price range with currency symbol
        """
        return f"₦{self.min_price:,.2f} - ₦{self.max_price:,.2f}"

    def get_average_price(self):
        """
        Get average price of the service.
        
        Returns:
            Decimal: Average of min and max price
        """
        return (self.min_price + self.max_price) / 2

    def is_available(self):
        """
        Check if service is available.
        
        Returns:
            bool: True if service is active, False otherwise
        """
        return self.is_active

    def get_subservices_count(self):
        """
        Get count of active subservices.
        
        Returns:
            int: Number of active subservices
        """
        return self.sub_services.filter(is_active=True).count()

    def get_total_bookings(self):
        """
        Get total number of bookings for this service.
        
        Returns:
            int: Total number of bookings
        """
        return self.bookings.count()

    @classmethod
    def get_services_by_category(cls, category):
        """
        Get services by category.
        
        Args:
            category: Service category
            
        Returns:
            QuerySet: Services in the specified category
        """
        return cls.objects.filter(category=category, is_active=True)

    @classmethod
    def get_services_by_provider(cls, provider):
        """
        Get services by provider.
        
        Args:
            provider: ServiceProvider instance
            
        Returns:
            QuerySet: Services offered by the provider
        """
        return cls.objects.filter(provider=provider, is_active=True)


class SubService(models.Model):
    """
    Model representing a sub-service under a main service.
    
    Manages sub-service information including pricing,
    availability status, and parent service details.
    """
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE, 
        related_name="sub_services",
        help_text="Main service this sub-service belongs to"
    )
    name = models.CharField(
        max_length=255, 
        help_text="Name of the sub-service"
    )
    description = models.TextField(
        help_text="Detailed description of the sub-service"
    )
    price = models.DecimalField(
        max_digits=16, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Price for the sub-service"
    )
    image = models.URLField(
        null=True, 
        blank=True, 
        help_text="URL to an image representing the sub-service"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether the sub-service is currently active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the sub-service was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="When the sub-service was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sub Service"
        verbose_name_plural = "Sub Services"
        indexes = [
            models.Index(fields=['service', '-created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['price']),
        ]

    def __str__(self) -> str:
        """String representation of the SubService."""
        return f"{self.name} - ₦{self.price:,.2f}"

    def get_price_display(self):
        """
        Get formatted price display.
        
        Returns:
            str: Formatted price with currency symbol
        """
        return f"₦{self.price:,.2f}"

    def is_available(self):
        """
        Check if subservice is available.
        
        Returns:
            bool: True if subservice is active, False otherwise
        """
        return self.is_active and self.service.is_active

    def get_service_name(self):
        """
        Get parent service name.
        
        Returns:
            str: Name of the parent service
        """
        return self.service.name

    @classmethod
    def get_subservices_by_service(cls, service):
        """
        Get subservices by parent service.
        
        Args:
            service: Service instance
            
        Returns:
            QuerySet: Subservices belonging to the service
        """
        return cls.objects.filter(service=service, is_active=True)


class ServiceRequest(models.Model):
    """
    Model representing a user's request for a service.
    
    Manages service request information including user details,
    pricing, categories, and status tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('awarded', 'Awarded'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="service_requests",
        help_text="User who made the service request"
    )
    title = models.CharField(
        max_length=255, 
        help_text="Title of the service request"
    )
    description = models.TextField(
        help_text="Detailed description of the service request"
    )
    image = models.URLField(
        null=True, 
        blank=True, 
        help_text="URL to an image for the request (optional)"
    )
    price = models.DecimalField(
        max_digits=16, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Budget for the service request"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="service_requests",
        help_text="Category of the requested service"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending', 
        help_text="Current status of the request"
    )
    # Location fields
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Latitude of the service request location"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Longitude of the service request location"
    )
    address = models.CharField(
        max_length=500, null=True, blank=True,
        help_text="Address of the service request location"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the service request was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="When the service request was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['price']),
        ]

    def __str__(self) -> str:
        """String representation of the ServiceRequest."""
        return f"{self.title} by {self.user.email} - {self.status}"

    def get_price_display(self):
        """
        Get formatted price display.
        
        Returns:
            str: Formatted price with currency symbol
        """
        return f"₦{self.price:,.2f}"

    def is_open_for_bids(self):
        """
        Check if request is open for bids.
        
        Returns:
            bool: True if request is open for bids, False otherwise
        """
        return self.status in ['pending', 'in_progress']

    def get_bids_count(self):
        """
        Get count of bids for this request.
        
        Returns:
            int: Number of bids
        """
        return self.bids.count()

    def get_accepted_bid(self):
        """
        Get the accepted bid for this request.
        
        Returns:
            ServiceRequestBid: Accepted bid or None
        """
        return self.bids.filter(status='accepted').first()

    def can_be_cancelled(self):
        """
        Check if request can be cancelled.
        
        Returns:
            bool: True if request can be cancelled, False otherwise
        """
        return self.status in ['pending', 'in_progress']

    def get_bids_ordered_by_distance(self):
        """
        Get all bids for this service request ordered by nearest distance.
        
        Returns:
            list: List of tuples (bid, distance_in_km), sorted by distance.
        """
        bids_with_distance = []
        for bid in self.bids.all():
            distance = bid.calculate_distance_km()
            if distance is not None:
                bids_with_distance.append((bid, distance))

        # Sort by distance
        bids_with_distance.sort(key=lambda x: x[1])
        return bids_with_distance

    @classmethod
    def get_requests_by_user(cls, user):
        """
        Get requests by user.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet: Requests made by the user
        """
        return cls.objects.filter(user=user)

    @classmethod
    def get_requests_by_category(cls, category):
        """
        Get requests by category.
        
        Args:
            category: Request category
            
        Returns:
            QuerySet: Requests in the specified category
        """
        return cls.objects.filter(category=category, status='pending')


class ServiceRequestBid(models.Model):
    """
    Model representing a bid on a service request by a provider.
    
    Manages bid information including pricing, status tracking,
    and provider details.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    service_request = models.ForeignKey(
        ServiceRequest, 
        on_delete=models.CASCADE, 
        related_name="bids",
        help_text="Service request being bid on"
    )
    provider = models.ForeignKey(
        "provider_app.ServiceProvider", 
        on_delete=models.CASCADE, 
        related_name="bids",
        help_text="Provider making the bid"
    )
    amount = models.DecimalField(
        max_digits=16, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Bid amount offered by the provider"
    )
    proposal = models.TextField(
        help_text="Proposal message from the provider"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending', 
        help_text="Current status of the bid"
    )
    # Location fields
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Latitude of the bid location"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Longitude of the bid location"
    )
    address = models.CharField(
        max_length=500, null=True, blank=True,
        help_text="Address of the bid location"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the bid was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="When the bid was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Request Bid"
        verbose_name_plural = "Service Request Bids"
        indexes = [
            models.Index(fields=['service_request', '-created_at']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['amount']),
        ]

    def __str__(self) -> str:
        """String representation of the ServiceRequestBid."""
        return f"Bid by {self.provider.company_name} for {self.service_request.title} - {self.status}"

    def get_amount_display(self):
        """
        Get formatted amount display.
        
        Returns:
            str: Formatted amount with currency symbol
        """
        return f"₦{self.amount:,.2f}"

    def is_accepted(self):
        """
        Check if bid is accepted.
        
        Returns:
            bool: True if bid is accepted, False otherwise
        """
        return self.status == 'accepted'

    def can_be_accepted(self):
        """
        Check if bid can be accepted.
        
        Returns:
            bool: True if bid can be accepted, False otherwise
        """
        return self.status == 'pending'

    def can_be_rejected(self):
        """
        Check if bid can be rejected.
        
        Returns:
            bool: True if bid can be rejected, False otherwise
        """
        return self.status == 'pending'

    def calculate_distance_km(self):
        """
        Calculate distance in kilometers between 
        the service request and the bid location using the Haversine formula.
        
        Returns:
            float: Distance in kilometers, or None if location data is missing
        """
        if not (self.latitude and self.longitude and 
                self.service_request.latitude and self.service_request.longitude):
            return None

        # Convert to floats
        lat1 = float(self.latitude)
        lon1 = float(self.longitude)
        lat2 = float(self.service_request.latitude)
        lon2 = float(self.service_request.longitude)

        # Radius of Earth in km
        R = 6371  

        # Convert degrees to radians
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return round(distance, 2)

    @classmethod
    def get_bids_by_request(cls, service_request):
        """
        Get bids by service request.
        
        Args:
            service_request: ServiceRequest instance
            
        Returns:
            QuerySet: Bids for the service request
        """
        return cls.objects.filter(service_request=service_request)

    @classmethod
    def get_bids_by_provider(cls, provider):
        """
        Get bids by provider.
        
        Args:
            provider: ServiceProvider instance
            
        Returns:
            QuerySet: Bids made by the provider
        """
        return cls.objects.filter(provider=provider)


class Booking(models.Model):
    """
    Model representing a booking for a service request bid.
    
    Tied directly to a specific bid, which already links the 
    service request and provider details.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings_as_user",
        help_text="User who made the booking"
    )
    bid = models.OneToOneField(  # 👈 ensures a bid can only lead to one booking
        ServiceRequestBid,
        on_delete=models.CASCADE,
        related_name="booking",
        help_text="The accepted bid for this booking"
    )
    provider = models.ForeignKey(
        "provider_app.ServiceProvider",
        on_delete=models.CASCADE,
        related_name="bookings",
        help_text="Service provider handling the booking"
    )
    amount = models.DecimalField(  # 👈 optional if you want to store snapshot at booking time
        max_digits=16,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Agreed amount for the booking"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the booking"
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Additional notes for the booking"
    )
    feedback = models.TextField(
        null=True,
        blank=True,
        help_text="Feedback from the user or provider"
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating given by the user (1-5)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the booking was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the booking was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        """String representation of the Booking."""
        return f"Booking for {self.bid.service_request.title} by {self.user.email}"

    def get_amount_display(self):
        return f"₦{self.amount:,.2f}"

    def is_confirmed(self):
        return self.status == 'confirmed'

    def is_completed(self):
        return self.status == 'completed'

    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']

    def get_rating_display(self):
        if self.rating:
            return f"{self.rating}/5 stars"
        return "No rating"

    @classmethod
    def get_bookings_by_user(cls, user):
        return cls.objects.filter(user=user)

    @classmethod
    def get_bookings_by_provider(cls, provider):
        return cls.objects.filter(provider=provider)



