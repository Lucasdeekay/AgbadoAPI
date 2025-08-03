"""
Authentication app models for user management, KYC, OTP, and referrals.

This module contains models for custom user, KYC, OTP, WebAuthn credentials, and referral tracking.
"""

from datetime import datetime, timedelta

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom user manager for creating users and superusers.
    
    Provides methods for creating regular users and superusers with proper
    field validation and default values.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user.
        
        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional user fields
            
        Returns:
            User: The created user instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser.
        
        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional user fields
            
        Returns:
            User: The created superuser instance
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model for authentication and profile management.
    
    Extends Django's AbstractUser to provide custom fields for
    phone number, state, service provider status, and verification.
    """
    username = None  # Remove the username field
    email = models.EmailField(
        unique=True, 
        help_text="User's email address"
    )
    phone_number = models.CharField(
        max_length=15, 
        unique=True, 
        help_text="User's phone number"
    )
    state = models.CharField(
        max_length=50, 
        help_text="User's state of residence"
    )
    is_service_provider = models.BooleanField(
        default=False, 
        help_text="Is the user a service provider?"
    )
    is_verified = models.BooleanField(
        default=False, 
        help_text="Has the user completed KYC?"
    )
    date_joined = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date the user joined"
    )
    profile_picture = models.URLField(
        null=True, 
        blank=True, 
        help_text="Profile picture URL"
    )
    referral_code = models.CharField(
        max_length=15, 
        unique=True, 
        null=True, 
        blank=True, 
        help_text="User's referral code"
    )
    is_busy = models.BooleanField(
        default=False, 
        help_text="Is the user currently busy?"
    )
    pin = models.CharField(
        max_length=6, 
        null=True, 
        blank=True, 
        help_text="User's PIN for additional security"
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

    def __str__(self) -> str:
        """String representation of the User."""
        return self.email

    def get_full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self) -> str:
        """Get the user's short name."""
        return self.first_name or self.email


class WebAuthnCredential(models.Model):
    """
    Model for storing WebAuthn credentials for passwordless authentication.
    
    Stores FIDO2 credentials for secure biometric authentication
    including public keys and transport methods.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='webauthn_credentials',
        help_text="User associated with this credential"
    )
    credential_id = models.CharField(
        max_length=255, 
        unique=True, 
        db_index=True, 
        help_text="Identifier for the credential"
    )
    public_key = models.TextField(
        help_text="Base64URL encoded public key"
    )
    sign_count = models.BigIntegerField(
        default=0, 
        help_text="Counter to prevent replay attacks"
    )
    transports = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="e.g., 'usb,nfc,ble,internal'"
    )
    registered_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When credential was registered"
    )
    last_used = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="When credential was last used"
    )

    class Meta:
        verbose_name = "WebAuthn Credential"
        verbose_name_plural = "WebAuthn Credentials"
        ordering = ['-registered_at']

    def __str__(self) -> str:
        """String representation of the WebAuthnCredential."""
        return f"Credential for {self.user.email} - ID: {self.credential_id[:10]}..."


class KYC(models.Model):
    """
    Model for storing Know Your Customer (KYC) information for users.
    
    Manages user verification documents including national ID,
    driver license, proof of address, and BVN.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="kyc",
        help_text="User associated with this KYC record"
    )
    national_id = models.URLField(
        null=True, 
        blank=True, 
        help_text="URL to uploaded national ID document"
    )
    bvn = models.CharField(
        max_length=11, 
        null=True, 
        blank=True, 
        help_text="Bank Verification Number"
    )
    driver_license = models.URLField(
        null=True, 
        blank=True, 
        help_text="URL to uploaded driver's license"
    )
    proof_of_address = models.URLField(
        null=True, 
        blank=True, 
        help_text="URL to proof of address document"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='Pending',
        help_text="KYC verification status"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="When KYC was last updated"
    )
    verified_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="When KYC was verified"
    )

    class Meta:
        verbose_name = "KYC"
        verbose_name_plural = "KYC Records"
        ordering = ['-updated_at']

    def __str__(self) -> str:
        """String representation of the KYC record."""
        return f"KYC for {self.user.email} - {self.status}"

    def is_complete(self) -> bool:
        """
        Check if KYC has all required documents.
        
        Returns:
            bool: True if KYC has all required documents
        """
        return bool(self.national_id and self.bvn and self.proof_of_address)


class OTP(models.Model):
    """
    Model for storing one-time passwords (OTP) for user verification.
    
    Manages OTP codes for email verification, password resets,
    and other security operations.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='otps',
        help_text="User associated with this OTP"
    )
    otp = models.CharField(
        max_length=6, 
        help_text="The OTP code sent to the user"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the OTP was created"
    )
    expires_at = models.DateTimeField(
        help_text="When the OTP expires"
    )
    is_used = models.BooleanField(
        default=False, 
        help_text="Whether the OTP has been used"
    )

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Set expiration time when creating OTP."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        """
        Check if OTP is expired.
        
        Returns:
            bool: True if OTP is expired
        """
        return timezone.now() > self.expires_at

    def __str__(self) -> str:
        """String representation of the OTP."""
        return f"OTP for {self.user.email} - {'Used' if self.is_used else 'Not Used'}"


class Referral(models.Model):
    """
    Model for tracking user referrals.
    
    Manages the relationship between users who refer others
    and users who were referred, for reward tracking.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="referral_user",
        help_text="User who was referred"
    )
    referer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="referral_referer",
        help_text="User who referred"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the referral was created"
    )

    class Meta:
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        ordering = ['-created_at']
        unique_together = ['user', 'referer']

    def __str__(self) -> str:
        """String representation of the Referral."""
        return f"{self.user.email} referred by {self.referer.email}"