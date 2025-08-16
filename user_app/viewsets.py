"""
ViewSets for user app models.

This module contains ViewSets for handling CRUD operations on user-related models
including tasks, rewards, activities, and gifts with proper filtering and pagination.
"""

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DailyTask, Gift, TaskCompletion, UserGift, UserReward, UserActivity, LeisureAccess
from .serializers import (
    DailyTaskSerializer, GiftSerializer, TaskCompletionSerializer, 
    UserGiftSerializer, UserRewardSerializer, UserActivitySerializer, 
    LeisureAccessSerializer
)


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for consistent page sizing across the API.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class DailyTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DailyTask model.
    
    Provides CRUD operations for daily tasks with filtering by task type and status.
    """
    queryset = DailyTask.objects.filter(is_active=True)
    serializer_class = DailyTaskSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['task_type', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'points']
    ordering = ['-created_at']


class TaskCompletionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaskCompletion model.
    
    Provides CRUD operations for task completions with user-specific filtering.
    """
    serializer_class = TaskCompletionSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['task', 'otp_verified']
    ordering_fields = ['completed_at']
    ordering = ['-completed_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return task completions for the authenticated user only."""
        return TaskCompletion.objects.filter(user=self.request.user)


class UserRewardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserReward model.
    
    Provides CRUD operations for user rewards with user-specific filtering.
    """
    serializer_class = UserRewardSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['redeemed']
    ordering_fields = ['redeemed_at']
    ordering = ['-redeemed_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return rewards for the authenticated user only."""
        return UserReward.objects.filter(user=self.request.user)


class UserActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserActivity model.
    
    Provides CRUD operations for user activities with user-specific filtering.
    """
    serializer_class = UserActivitySerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['activity_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return activities for the authenticated user only."""
        return UserActivity.objects.filter(user=self.request.user)


class LeisureAccessViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LeisureAccess model.
    
    Provides CRUD operations for leisure access with user-specific filtering.
    """
    serializer_class = LeisureAccessSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['is_verified']
    ordering_fields = ['verified_at']
    ordering = ['-verified_at']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return leisure access for the authenticated user only."""
        return LeisureAccess.objects.filter(user=self.request.user)


class GiftViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Gift model.
    
    Provides CRUD operations for gifts. Public read access, admin write access.
    """
    queryset = Gift.objects.all()
    serializer_class = GiftSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name']
    ordering_fields = ['coin_amount', 'created_at']
    ordering = ['coin_amount']
    permission_classes = [AllowAny]  # Public can view gifts

class UserGiftViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserGift model.
    
    Provides CRUD operations for user gifts with point deduction logic.
    """
    serializer_class = UserGiftSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ['delivery_status']
    ordering_fields = ['date_won', 'delivery_date']
    ordering = ['-date_won']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return gifts for the authenticated user only."""
        return UserGift.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create a new user gift with point deduction validation.
        
        Validates that the user has enough points before creating the gift.
        """
        gift_id = request.data.get('gift')
        user = request.user

        try:
            gift = get_object_or_404(Gift, pk=gift_id)
        except Gift.DoesNotExist:
            return Response(
                {"detail": "Gift not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            user_reward = get_object_or_404(UserReward, user=user)
        except UserReward.DoesNotExist:
            return Response(
                {"detail": "User reward account not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if user_reward.points < gift.coin_amount:
            return Response(
                {"detail": "Not enough points to claim this gift."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deduct points
        user_reward.points -= gift.coin_amount
        user_reward.save()

        # Create UserGift entry
        serializer = self.get_serializer(data={'user': user.id, 'gift': gift.id})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
