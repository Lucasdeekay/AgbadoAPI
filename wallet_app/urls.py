from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import WalletViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'wallet', WalletViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
