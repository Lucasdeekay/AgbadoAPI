from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CancelBookingView, CompleteBookingView, GetSubServiceDetailsView, 
    ServiceProviderBidsView, ServiceProviderBookingsView, GetAllServicesDetailsView, 
    GetServiceDetailsView, AddServiceView, AddSubServiceView, EditServiceView, 
    EditSubServiceView, SubmitBidView, UserBookingsView, AcceptBidView, DeclineBidView
)
from .viewsets import (
    ServiceViewSet, SubServiceViewSet, ServiceRequestViewSet, 
    ServiceRequestBidViewSet, BookingViewSet
)

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'sub-services', SubServiceViewSet, basename='sub-service')
router.register(r'service-requests', ServiceRequestViewSet, basename='service-request')
router.register(r'service-request-bids', ServiceRequestBidViewSet, basename='service-request-bid')
router.register(r'bookings', BookingViewSet, basename='booking')


urlpatterns = [
    # 🔹 Bookings
    path('bookings/provider/', ServiceProviderBookingsView.as_view(), name='provider-bookings'),
    path('bookings/user/', UserBookingsView.as_view(), name='user-bookings'),
    path('bookings/cancel/<int:booking_id>/', CancelBookingView.as_view(), name='cancel-booking'),
    path('bookings/complete/<int:booking_id>/', CompleteBookingView.as_view(), name='complete-booking'),

    # 🔹 Bids
    path('bids/submit/<int:service_request_id>/', SubmitBidView.as_view(), name='submit-bid'),
    path('bids/accept/<int:bid_id>/', AcceptBidView.as_view(), name='accept-bid'),
    path('bids/decline/<int:bid_id>/', DeclineBidView.as_view(), name='decline-bid'),
    path('requests/', ServiceProviderBidsView.as_view(), name='provider-requests'),

    # 🔹 Services & Subservices
    path('all/', GetAllServicesDetailsView.as_view(), name='get_all_services'),
    path('<int:service_id>/', GetServiceDetailsView.as_view(), name='service_details'),
    path('sub-service/<int:sub_service_id>/', GetSubServiceDetailsView.as_view(), name='sub_service_details'),
    path('add/', AddServiceView.as_view(), name='add_service'),
    path('sub-service/add/<int:service_id>/', AddSubServiceView.as_view(), name='add_subservice'),
    path('edit/<int:service_id>/', EditServiceView.as_view(), name='edit_service'),
    path('sub-service/edit/<int:subservice_id>/', EditSubServiceView.as_view(), name='edit_subservice'),

    # 🔹 DRF Router
    path('api/', include(router.urls)),
]
