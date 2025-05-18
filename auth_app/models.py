from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # Remove the username field
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    state = models.CharField(max_length=50)
    is_service_provider = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # To check if the user has completed KYC
    date_joined = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_picture/', null=True, blank=True)
    referral_code = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_busy = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    def __str__(self):
        return self.email


class KYC(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="kyc")
    national_id = models.ImageField(upload_to='national_id/', null=True, blank=True)
    bvn = models.CharField(max_length=11, null=True, blank=True)
    driver_license = models.ImageField(upload_to='driver_license/', null=True, blank=True)
    proof_of_address = models.ImageField(upload_to='proof_of_address/', null=True, blank=True)
    status = models.CharField(max_length=10,
                              choices=[('Pending', 'Pending'), ('Verified', 'Verified'), ('Rejected', 'Rejected')],
                              default='Pending')
    updated_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"KYC for {self.user.email}"


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """
        Check if OTP is expired (1 hour after creation).
        """
        expiration_time = self.created_at + timedelta(hours=1)
        return timezone.now() > expiration_time

    def __str__(self):
        return f"OTP for {self.user.email} - {'Used' if self.is_used else 'Not Used'}"

class Referral(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referral_user")
    referer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referral_referer")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} referral - {self.referer.email}"