"""
ViewSets for service app models.

This module contains ViewSets for handling CRUD operations on service-related models
including services, subservices, service requests, bids, and bookings with proper filtering and pagination.
"""

from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Service, SubService, ServiceRequest, ServiceRequestBid, Booking
from .serializers import ServiceSerializer, SubServiceSerializer, ServiceRequestSerializer, ServiceRequestBidSerializer, BookingSerializer

import logging

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for consistent page sizing across the API.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Service model.
    
    Provides CRUD operations for services with filtering by name and active status.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['name', 'is_active', 'category', 'provider']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['created_at', 'name', 'min_price', 'max_price']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Log service creation."""
        service = serializer.save()
        logger.info(f"Service created: {service.name}")

    def perform_update(self, serializer):
        """Log service updates."""
        service = serializer.save()
        logger.info(f"Service updated: {service.name}")

    def perform_destroy(self, instance):
        """Log service deletion."""
        service_name = instance.name
        instance.delete()
        logger.info(f"Service deleted: {service_name}")


class SubServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SubService model.
    
    Provides CRUD operations for subservices with filtering by service, name, and price.
    """
    queryset = SubService.objects.all()
    serializer_class = SubServiceSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['service', 'name', 'price', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'price']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Log subservice creation."""
        subservice = serializer.save()
        logger.info(f"Subservice created: {subservice.name}")

    def perform_update(self, serializer):
        """Log subservice updates."""
        subservice = serializer.save()
        logger.info(f"Subservice updated: {subservice.name}")

    def perform_destroy(self, instance):
        """Log subservice deletion."""
        subservice_name = instance.name
        instance.delete()
        logger.info(f"Subservice deleted: {subservice_name}")


class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ServiceRequest model.
    
    Provides CRUD operations for service requests with user-specific filtering.
    """
    serializer_class = ServiceRequestSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['category', 'status', 'user']
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'title', 'price']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return service requests for the authenticated user only."""
        return ServiceRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Log service request creation."""
        service_request = serializer.save()
        logger.info(f"Service request created: {service_request.title}")

    def perform_update(self, serializer):
        """Log service request updates."""
        service_request = serializer.save()
        logger.info(f"Service request updated: {service_request.title}")

    def perform_destroy(self, instance):
        """Log service request deletion."""
        request_title = instance.title
        instance.delete()
        logger.info(f"Service request deleted: {request_title}")


class ServiceRequestBidViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ServiceRequestBid model.
    
    Provides CRUD operations for service request bids with user-specific filtering.
    """
    serializer_class = ServiceRequestBidSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['service_request', 'service_provider', 'status']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return bids for the authenticated user only."""
        return ServiceRequestBid.objects.filter(service_provider=self.request.user)

    def perform_create(self, serializer):
        """Log bid creation."""
        bid = serializer.save()
        logger.info(f"Bid created for service request: {bid.service_request.title}")

    def perform_update(self, serializer):
        """Log bid updates."""
        bid = serializer.save()
        logger.info(f"Bid updated for service request: {bid.service_request.title}")

    def perform_destroy(self, instance):
        """Log bid deletion."""
        request_title = instance.service_request.title
        instance.delete()
        logger.info(f"Bid deleted for service request: {request_title}")

    @action(detail=False, methods=['get'])
    def nearest(self, request):
        """
        Return bids ordered by nearest distance to their service request.
        """
        queryset = self.get_queryset()
        bids_with_distance = sorted(
            queryset,
            key=lambda bid: bid.calculate_distance_km() or float('inf')
        )
        page = self.paginate_queryset(bids_with_distance)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Booking model.
    
    Provides CRUD operations for bookings with user-specific filtering.
    """
    serializer_class = BookingSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['service_request', 'user', 'service_provider', 'user_status', 'provider_status']
    ordering_fields = ['created_at', 'user_status', 'provider_status']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return bookings for the authenticated user only."""
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Log booking creation."""
        booking = serializer.save()
        logger.info(f"Booking created for service request: {booking.service_request.title}")

    def perform_update(self, serializer):
        """Log booking updates."""
        booking = serializer.save()
        logger.info(f"Booking updated for service request: {booking.service_request.title}")

    def perform_destroy(self, instance):
        """Log booking deletion."""
        request_title = instance.service_request.title
        instance.delete()
        logger.info(f"Booking deleted for service request: {request_title}")
