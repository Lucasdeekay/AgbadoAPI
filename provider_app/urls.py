from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ServiceProviderViewSet

router = DefaultRouter()
router.register(r'providers', ServiceProviderViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
