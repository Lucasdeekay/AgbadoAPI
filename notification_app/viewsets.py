"""
ViewSets for notification app models.

This module contains ViewSets for handling CRUD operations on notification models
with proper filtering and pagination.
"""

from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Notification
from .serializers import NotificationSerializer

import logging

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for consistent page sizing across the API.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification model.
    
    Provides CRUD operations for notifications with user-specific filtering.
    """
    serializer_class = NotificationSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['is_read', 'created_at']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return notifications for the authenticated user only."""
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Log notification creation."""
        notification = serializer.save()
        logger.info(f"Notification created for user: {notification.user.email}")

    def perform_update(self, serializer):
        """Log notification updates."""
        notification = serializer.save()
        logger.info(f"Notification updated for user: {notification.user.email}")

    def perform_destroy(self, instance):
        """Log notification deletion."""
        user_email = instance.user.email
        instance.delete()
        logger.info(f"Notification deleted for user: {user_email}")
