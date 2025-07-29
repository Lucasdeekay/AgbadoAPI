from rest_framework import serializers
from .models import Wallet, Transaction, Withdrawal
from auth_app.models import User # Assuming User model is here for nested serializer


# Serializer for User (for nested representation)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name'] # Or whatever user fields you want to expose


# Serializer for Wallet model
class WalletSerializer(serializers.ModelSerializer):
    # Use a nested serializer if you want to display user details
    # Otherwise, user will just be the user ID (PK)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Wallet
        fields = (
            'id', # Always include ID for API representation
            'user',
            'balance',
            'paystack_customer_code',
            'dva_account_number',
            'dva_account_name',
            'dva_bank_name',
            'dva_assigned_at',
            'updated_at',
            'created_at',
        )
        read_only_fields = (
            'id',
            'user', # User is set by the system, not directly via WalletSerializer
            'balance', # Balance is updated via transactions, not directly editable here
            'paystack_customer_code',
            'dva_account_number',
            'dva_account_name',
            'dva_bank_name',
            'dva_assigned_at',
            'updated_at',
            'created_at',
        )


# Serializer for Transaction model
class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Nested user details

    class Meta:
        model = Transaction
        fields = (
            'id',
            'user',
            'amount',
            'transaction_type',
            'reference', # Updated from transaction_id
            'status',
            'paystack_transaction_id', # New field
            'created_at',
            'updated_at', # New field
        )
        read_only_fields = (
            'id',
            'user',
            'status', # Status is set by webhook or internal logic
            'reference',
            'paystack_transaction_id',
            'created_at',
            'updated_at',
        )


# Serializer for creating/requesting a Withdrawal (user's input)
class WithdrawalRequestSerializer(serializers.ModelSerializer):
    # These fields are required from the user
    bank_name = serializers.CharField(max_length=100)
    account_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2) # Ensure it's not negative etc.

    class Meta:
        model = Withdrawal
        fields = [
            'bank_name',
            'account_number',
            'amount',
            # 'account_name' could be here if user provides it, but often verified later
        ]

    # You might want to add custom validation here, e.g.,
    # - Ensure amount is within min/max withdrawal limits
    # - Ensure user has sufficient balance (though this is better in the view logic)
    # - Basic validation for bank_name/account_number format
    def validate(self, data):
        # Example validation: Amount must be positive
        if data['amount'] <= 0:
            raise serializers.ValidationError("Withdrawal amount must be positive.")
        # Add more validation as needed
        return data


# Serializer for displaying Withdrawal details (admin or user's history)
class WithdrawalDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Nested user details

    class Meta:
        model = Withdrawal
        fields = [
            'id',
            'user',
            'bank_name',
            'account_number',
            'account_name', # New field, Paystack verifies this
            'amount',
            'status',
            'paystack_recipient_code',
            'paystack_transfer_reference',
            'paystack_transfer_id',
            'failure_reason', # New field
            'created_at',
            'updated_at', # New field
        ]
        read_only_fields = [
            'id',
            'user',
            'bank_name',
            'account_number',
            'account_name',
            'amount',
            'status',
            'paystack_recipient_code',
            'paystack_transfer_reference',
            'paystack_transfer_id',
            'failure_reason',
            'created_at',
            'updated_at',
        ]