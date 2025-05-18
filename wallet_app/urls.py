from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WalletDetailsView, AllTransactionsView, TransactionDetailView, DepositView, WithdrawalRequestView
from .viewsets import WalletViewSet, TransactionViewSet, WithdrawalViewSet

router = DefaultRouter()
router.register(r'wallet', WalletViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'withdrawals', WithdrawalViewSet)

urlpatterns = [
    path('', WalletDetailsView.as_view(), name='wallet-details'),
    path('transactions/', AllTransactionsView.as_view(), name='all-transactions'),
    path('transactions/<int:transaction_id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('deposit/', DepositView.as_view(), name='deposit'),
    path('withdraw/', WithdrawalRequestView.as_view(), name='withdraw'),
    path('api/', include(router.urls)),  # All routes are prefixed with 'api/'
]
