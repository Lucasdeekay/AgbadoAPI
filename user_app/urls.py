from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import DailyTaskViewSet, TaskCompletionViewSet, UserRewardViewSet, UserActivityViewSet, LeisureAccessViewSet

router = DefaultRouter()
router.register(r'tasks', DailyTaskViewSet)
router.register(r'task-completions', TaskCompletionViewSet)
router.register(r'rewards', UserRewardViewSet)
router.register(r'user-activities', UserActivityViewSet)
router.register(r'leisure', LeisureAccessViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
