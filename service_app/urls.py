from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ServiceViewSet, SubServiceViewSet, ServiceRequestViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet)
router.register(r'subservices', SubServiceViewSet)
router.register(r'requests', ServiceRequestViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
