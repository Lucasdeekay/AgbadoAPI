from rest_framework import serializers
from .models import Wallet, Transaction


# Serializer for Wallet model
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('user', 'balance', 'updated_at')


# Serializer for Transaction model
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('user', 'amount', 'transaction_type', 'status', 'created_at')
