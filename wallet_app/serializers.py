from rest_framework import serializers
from .models import Wallet, Transaction, Withdrawal


# Serializer for Wallet model
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('user', 'balance', 'updated_at')


# Serializer for Transaction model
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('user', 'amount', 'transaction_type', 'transaction_id', 'status', 'created_at')


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['id', 'user', 'bank_name', 'account_number', 'amount', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'status']