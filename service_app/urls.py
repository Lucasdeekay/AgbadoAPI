from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ServiceProviderDetailsView, ServiceDetailsView, AddServiceView, AddSubServiceView, EditServiceView, \
    EditSubServiceView
from .viewsets import ServiceViewSet, SubServiceViewSet, ServiceRequestViewSet, ServiceRequestBidViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet)
router.register(r'sub-services', SubServiceViewSet)
router.register(r'service-requests', ServiceRequestViewSet, basename='service-request')
router.register(r'service-request-bids', ServiceRequestBidViewSet, basename='service-request-bid')
router.register(r'bookings', BookingViewSet, basename='booking')



urlpatterns = [
    path('service-provider/', ServiceProviderDetailsView.as_view(), name='service_provider_details'),
    path('service/<int:service_id>/', ServiceDetailsView.as_view(), name='service_details'),
    path('service/add/', AddServiceView.as_view(), name='add_service'),
    path('sub-service/add/', AddSubServiceView.as_view(), name='add_subservice'),
    path('service/edit/<int:service_id>/', EditServiceView.as_view(), name='edit_service'),
    path('sub-service/edit/<int:subservice_id>/', EditSubServiceView.as_view(), name='edit_subservice'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
