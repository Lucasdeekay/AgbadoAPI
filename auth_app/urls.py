from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RegisterView, LoginView, LogoutView, ForgotPasswordView, RetrievePasswordView, VerifyOTPView, \
    GoogleAuthView, AppleAuthView
from .viewsets import UserViewSet, KYCViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'kyc', KYCViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('retrieve-password/', RetrievePasswordView.as_view(), name='retrieve-password'),
    path('login/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('login/apple/', AppleAuthView.as_view(), name='apple-auth'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
