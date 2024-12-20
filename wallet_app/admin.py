from django.contrib import admin
from .models import Wallet, Transaction, Withdrawal


# Registering the Wallet model with custom admin interface
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__email',)
    list_filter = ('user__is_service_provider',)
    ordering = ('-updated_at',)


# Registering the Transaction model with custom admin interface
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'transaction_id', 'status', 'created_at')
    search_fields = ('user__email', 'transaction_type')
    list_filter = ('transaction_type', 'status')
    ordering = ('-created_at',)


class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['user', 'bank_name', 'account_number', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'bank_name', 'account_number']
    ordering = ['-created_at']


admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Withdrawal, WithdrawalAdmin)