"""
ViewSets for provider app models.

This module contains ViewSets for handling CRUD operations on service provider models
with proper filtering and pagination.
"""

from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ServiceProvider
from .serializers import ServiceProviderSerializer

import logging

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for consistent page sizing across the API.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ServiceProvider model.
    
    Provides CRUD operations for service providers with filtering by company name,
    business category, and approval status.
    """
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['company_name', 'business_category', 'is_approved']
    search_fields = ['company_name', 'company_description', 'company_email']
    ordering_fields = ['created_at', 'company_name', 'is_approved']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Log service provider creation."""
        service_provider = serializer.save()
        logger.info(f"Service provider created: {service_provider.company_name}")

    def perform_update(self, serializer):
        """Log service provider updates."""
        service_provider = serializer.save()
        logger.info(f"Service provider updated: {service_provider.company_name}")

    def perform_destroy(self, instance):
        """Log service provider deletion."""
        company_name = instance.company_name
        instance.delete()
        logger.info(f"Service provider deleted: {company_name}")
