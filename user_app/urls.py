from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DashboardView, UpdateUserProfileView, UpdateKYCView, ChangePasswordView
from .viewsets import DailyTaskViewSet, TaskCompletionViewSet, UserRewardViewSet, UserActivityViewSet, LeisureAccessViewSet

router = DefaultRouter()
router.register(r'tasks', DailyTaskViewSet)
router.register(r'task-completions', TaskCompletionViewSet)
router.register(r'rewards', UserRewardViewSet)
router.register(r'user-activities', UserActivityViewSet)
router.register(r'leisure', LeisureAccessViewSet)


urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/update/', UpdateUserProfileView.as_view(), name='update_user_profile'),
    path('kyc/update/', UpdateKYCView.as_view(), name='update_user_kyc'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
