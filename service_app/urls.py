from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CancelBookingView, CompleteBookingView, ServiceProviderBidsView, ServiceProviderBookingsView, GetAllServicesDetailsView, ServiceDetailsView, AddServiceView, AddSubServiceView, EditServiceView, \
    EditSubServiceView, SubmitBidView
from .viewsets import ServiceViewSet, SubServiceViewSet, ServiceRequestViewSet, ServiceRequestBidViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'services', ServiceViewSet)
router.register(r'sub-services', SubServiceViewSet)
router.register(r'service-requests', ServiceRequestViewSet, basename='service-request')
router.register(r'service-request-bids', ServiceRequestBidViewSet, basename='service-request-bid')
router.register(r'bookings', BookingViewSet, basename='booking')



urlpatterns = [
    path('bookings/', ServiceProviderBookingsView.as_view(), name='bookings'),
    path('requests/', ServiceProviderBidsView.as_view(), name='requests'),
    path('bids/submit/<int:service_request_id>/', SubmitBidView.as_view(), name='submit-bid'),
    path('bookings/cancel/<int:booking_id>/', CancelBookingView.as_view(), name='cancel-booking'),
    path('bookings/complete/<int:booking_id>/', CompleteBookingView.as_view(), name='complete-booking'),
    path('all/', GetAllServicesDetailsView.as_view(), name='get_all_services'),
    path('<int:service_id>/', ServiceDetailsView.as_view(), name='service_details'),
    path('add/', AddServiceView.as_view(), name='add_service'),
    path('sub-service/add/', AddSubServiceView.as_view(), name='add_subservice'),
    path('edit/<int:service_id>/', EditServiceView.as_view(), name='edit_service'),
    path('sub-service/edit/<int:subservice_id>/', EditSubServiceView.as_view(), name='edit_subservice'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
