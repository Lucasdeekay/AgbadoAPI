from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RegisterView, LoginView, LogoutView, ForgotPasswordView, RetrievePasswordView, VerifyOTPView, \
    GoogleAuthView, AppleAuthView, ResetPasswordView
from .viewsets import UserViewSet, KYCViewSet, OTPViewSet, ReferralViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'kyc', KYCViewSet)
router.register(r'otp', OTPViewSet)
router.register(r'referral', ReferralViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('retrieve-password/', RetrievePasswordView.as_view(), name='retrieve-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('login/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('login/apple/', AppleAuthView.as_view(), name='apple-auth'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
