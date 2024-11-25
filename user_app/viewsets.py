from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import DailyTask, TaskCompletion, UserReward, UserActivity, LeisureAccess
from .serializers import DailyTaskSerializer, TaskCompletionSerializer, UserRewardSerializer, UserActivitySerializer, \
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
