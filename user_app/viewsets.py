from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import DailyTask, Gift, TaskCompletion, UserGift, UserReward, UserActivity, LeisureAccess
from .serializers import DailyTaskSerializer, GiftSerializer, TaskCompletionSerializer, UserGiftSerializer, UserRewardSerializer, UserActivitySerializer, \
    LeisureAccessSerializer


class CustomPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page


class DailyTaskViewSet(viewsets.ModelViewSet):
    queryset = DailyTask.objects.all()
    serializer_class = DailyTaskSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['user', 'task_type', 'status']  # Fields you want to filter by


class TaskCompletionViewSet(viewsets.ModelViewSet):
    queryset = TaskCompletion.objects.all()
    serializer_class = TaskCompletionSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['user', 'task', 'status']  # Fields you want to filter by


class UserRewardViewSet(viewsets.ModelViewSet):
    queryset = UserReward.objects.all()
    serializer_class = UserRewardSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['user', 'reward_type']  # Fields you want to filter by


class UserActivityViewSet(viewsets.ModelViewSet):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['user', 'activity_type', 'status']  # Fields you want to filter by


class LeisureAccessViewSet(viewsets.ModelViewSet):
    queryset = LeisureAccess.objects.all()
    serializer_class = LeisureAccessSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['user', 'platform', 'status']  # Fields you want to filter by


class GiftViewSet(viewsets.ModelViewSet):
    queryset = Gift.objects.all()
    serializer_class = GiftSerializer
    permission_classes = [AllowAny] # Admin might manage this, but public can view available gifts

class UserGiftViewSet(viewsets.ModelViewSet):
    queryset = UserGift.objects.all()
    serializer_class = UserGiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        gift_id = request.data.get('gift')
        user = request.user

        try:
            gift = get_object_or_404(Gift, pk=gift_id)
        except:
            return Response({"detail": "Gift not found."}, status=status.HTTP_404_NOT_FOUND)

        user_reward = get_object_or_404(UserReward, user=user)

        if user_reward.points < gift.coin_amount:
            return Response({"detail": "Not enough points to claim this gift."}, status=status.HTTP_400_BAD_REQUEST)

        # Deduct points
        user_reward.points -= gift.coin_amount
        user_reward.save()

        # Create UserGift entry
        serializer = self.get_serializer(data={'user': user.id, 'gift': gift.id})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
