from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DashboardView, GetKYCDetailsView, GetReferralCode, UpdateUserProfileView, UpdateKYCView, ChangePasswordView
from .viewsets import DailyTaskViewSet, GiftViewSet, TaskCompletionViewSet, UserGiftViewSet, UserRewardViewSet, UserActivityViewSet, LeisureAccessViewSet

router = DefaultRouter()
router.register(r'tasks', DailyTaskViewSet, basename='task')
router.register(r'task-completions', TaskCompletionViewSet, basename='task-completion')
router.register(r'rewards', UserRewardViewSet, basename='reward')
router.register(r'user-activities', UserActivityViewSet, basename='user-activity')
router.register(r'leisure', LeisureAccessViewSet, basename='leisure')
router.register(r'gifts', GiftViewSet, basename='gift')
router.register(r'user-gifts', UserGiftViewSet, basename='user-gift')


urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/update/', UpdateUserProfileView.as_view(), name='update_user_profile'),
    path('kyc/', GetKYCDetailsView.as_view(), name='get_user_kyc'),
    path('kyc/update/', UpdateKYCView.as_view(), name='update_user_kyc'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('referral-code/', GetReferralCode.as_view(), name='get_referral_code'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
