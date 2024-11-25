from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import NotificationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
