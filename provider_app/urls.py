from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CreateServiceProviderView, EditServiceProviderView, GetServiceProviderDetailsView
from .viewsets import ServiceProviderViewSet

router = DefaultRouter()
router.register(r'providers', ServiceProviderViewSet, basename='provider')

urlpatterns = [
    path("create/", CreateServiceProviderView.as_view(), name="create_service_provider"),
    path("edit/", EditServiceProviderView.as_view(), name="edit_service_provider"),
    path("details/", GetServiceProviderDetailsView.as_view(), name="get_service_provider_details"),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]


