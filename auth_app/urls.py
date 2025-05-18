from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RegisterServiceProviderView, LoginView, LogoutView, ForgotPasswordView, RegisterUserView, ResetPasswordView, SendOTPView, UpdateIsBusyView, VerifyOTPView, \
    GoogleAppleAuthView
from .viewsets import UserViewSet, KYCViewSet, OTPViewSet, ReferralViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'kyc', KYCViewSet)
router.register(r'otp', OTPViewSet)
router.register(r'referral', ReferralViewSet)

urlpatterns = [
    path('register/service-provider/', RegisterServiceProviderView.as_view(), name='register-service-provider'),
    path('register/user/', RegisterUserView.as_view(), name='register-user'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('update-status/', UpdateIsBusyView.as_view(), name='update-status'),
    path('login/google-or-apple/', GoogleAppleAuthView.as_view(), name='google-or-apple-auth'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
