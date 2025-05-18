from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GetUserNotificationsView, UpdateAllNotificationsReadStatusView
from .viewsets import NotificationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet)


urlpatterns = [
    path('', GetUserNotificationsView.as_view(), name='get_user_notifications'),
    path('mark-read/', UpdateAllNotificationsReadStatusView.as_view(), name='update_notification_read_status'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
