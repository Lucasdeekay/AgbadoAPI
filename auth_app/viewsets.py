"""
ViewSets for auth app models.

This module contains ViewSets for handling CRUD operations on authentication-related models
including users, KYC, OTP, and referrals with proper filtering and pagination.
"""

from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, KYC, OTP, Referral
from .serializers import UserSerializer, KYCSerializer, OTPSerializer, ReferralSerializer

import logging

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for consistent page sizing across the API.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    
    Provides CRUD operations for users with filtering by email, phone number, and status.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['email', 'phone_number', 'is_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['first_name', 'last_name', 'email', 'date_joined', 'last_login']
    ordering = ['-date_joined']
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Log user creation."""
        user = serializer.save()
        logger.info(f"User created: {user.email}")

    def perform_update(self, serializer):
        """Log user updates."""
        user = serializer.save()
        logger.info(f"User updated: {user.email}")

    def perform_destroy(self, instance):
        """Log user deletion."""
        email = instance.email
        instance.delete()
        logger.info(f"User deleted: {email}")


class KYCViewSet(viewsets.ModelViewSet):
    """
    ViewSet for KYC model.
    
    Provides CRUD operations for KYC documents with user-specific filtering.
    """
    serializer_class = KYCSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['status',]
    ordering_fields = ['created_at', 'updated_at', 'verified_at']
    ordering = ['-updated_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return KYC records for the authenticated user only."""
        return KYC.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Log KYC creation."""
        kyc = serializer.save()
        logger.info(f"KYC created for user: {kyc.user.email}")

    def perform_update(self, serializer):
        """Log KYC updates."""
        kyc = serializer.save()
        logger.info(f"KYC updated for user: {kyc.user.email}")


class OTPViewSet(viewsets.ModelViewSet):
    """
    ViewSet for OTP model.
    
    Provides CRUD operations for OTP records with user-specific filtering.
    """
    serializer_class = OTPSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['is_used',]
    ordering_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return OTP records for the authenticated user only."""
        return OTP.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Log OTP creation."""
        otp = serializer.save()
        logger.info(f"OTP created for user: {otp.user.email}")

    def perform_update(self, serializer):
        """Log OTP updates."""
        otp = serializer.save()
        logger.info(f"OTP updated for user: {otp.user.email}")


class ReferralViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Referral model.
    
    Provides CRUD operations for referral records with user-specific filtering.
    """
    serializer_class = ReferralSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return referrals for the authenticated user only."""
        return Referral.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Log referral creation."""
        referral = serializer.save()
        logger.info(f"Referral created: {referral.user.email} referred by {referral.referer.email}")

    def perform_update(self, serializer):
        """Log referral updates."""
        referral = serializer.save()
        logger.info(f"Referral updated: {referral.user.email}")
