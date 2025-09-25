"""
Provider app models for service provider management.

This module contains models for managing service provider profiles,
business information, and service categories.
"""

from datetime import datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from auth_app.models import User

class ServiceProvider(models.Model):
    """
    Model representing a service provider profile.
    
    Manages service provider business information including company details,
    contact information, business hours, ratings, and approval status.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="provider_profile",
        help_text="User account associated with this service provider"
    )
    company_name = models.CharField(
        max_length=200, 
        help_text="Name of the service provider's company"
    )
    company_address = models.TextField(
        help_text="Physical address of the company"
    )
    company_description = models.TextField(
        null=True, 
        blank=True,
        help_text="Description of the company's services"
    )
    company_phone_no = models.CharField(
        max_length=15, 
        help_text="Contact phone number for the company"
    )
    company_email = models.EmailField(
        help_text="Contact email address for the company"
    )
    business_category = models.ForeignKey(
        "service_app.Category",
        on_delete=models.SET_NULL,
        null=True,
        related_name="providers",
        help_text="Business category/type"
    )
    company_logo = models.URLField(
        null=True, 
        blank=True, 
        help_text="URL to the company's logo image"
    )
    opening_hour = models.CharField(
        max_length=5, 
        null=True, 
        blank=True,
        help_text="Opening hour (e.g., 08:00)"
    )
    closing_hour = models.CharField(
        max_length=5, 
        null=True, 
        blank=True,
        help_text="Closing hour (e.g., 18:00)"
    )
    avg_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)],
        help_text="Average customer rating (0.00-5.00)"
    )
    rating_population = models.PositiveIntegerField(
        default=0, 
        help_text="Number of ratings received"
    )
    is_approved = models.BooleanField(
        default=False, 
        help_text="Whether the provider is approved by admin"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the provider profile was created"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Provider"
        verbose_name_plural = "Service Providers"
        indexes = [
            models.Index(fields=['business_category']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['avg_rating']),
        ]

    def __str__(self) -> str:
        """String representation of the ServiceProvider."""
        return self.company_name

    def get_full_address(self):
        """
        Get complete company address.
        
        Returns:
            str: Complete company address
        """
        return self.company_address

    def get_business_hours(self):
        """
        Get formatted business hours.
        
        Returns:
            str: Formatted business hours string
        """
        if self.opening_hour and self.closing_hour:
            return f"{self.opening_hour} - {self.closing_hour}"
        elif self.opening_hour:
            return f"Opens at {self.opening_hour}"
        elif self.closing_hour:
            return f"Closes at {self.closing_hour}"
        return "Hours not specified"

    def update_rating(self, new_rating):
        """
        Update average rating with new rating.
        
        Args:
            new_rating: New rating value (1-5)
        """
        if 1 <= new_rating <= 5:
            total_rating = (self.avg_rating * self.rating_population) + new_rating
            self.rating_population += 1
            self.avg_rating = total_rating / self.rating_population
            self.save(update_fields=['avg_rating', 'rating_population'])

    def is_open_now(self):
        """
        Check if business is currently open.
        
        Returns:
            bool: True if business is open, False otherwise
        """
        if not self.opening_hour or not self.closing_hour:
            return False
        
        try:
            from datetime import datetime
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            # Simple time comparison (assumes same day)
            return self.opening_hour <= current_time <= self.closing_hour
        except:
            return False

    @classmethod
    def get_approved_providers(cls):
        """
        Get all approved service providers.
        
        Returns:
            QuerySet: Approved service providers
        """
        return cls.objects.filter(is_approved=True)

    @classmethod
    def get_providers_by_category(cls, category):
        """
        Get service providers by business category.
        
        Args:
            category: Business category
            
        Returns:
            QuerySet: Service providers in the specified category
        """
        return cls.objects.filter(business_category=category, is_approved=True)