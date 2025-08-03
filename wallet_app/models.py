from datetime import datetime
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from auth_app.models import User




class Wallet(models.Model):
    """
    Model representing a user's wallet for managing balances and virtual accounts.
    """
    user: 'User' = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="wallet",
        help_text="User account associated with this wallet"
    )
    balance: float = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, help_text="Current wallet balance"
    )
    paystack_customer_code: str = models.CharField(
        max_length=50, unique=True, null=True, blank=True, help_text="Paystack customer code for this user"
    )
    dva_account_number: str = models.CharField(
        max_length=20, unique=True, null=True, blank=True, help_text="Dedicated Virtual Account number"
    )
    dva_account_name: str = models.CharField(
        max_length=200, null=True, blank=True, help_text="Name on the DVA account"
    )
    dva_bank_name: str = models.CharField(
        max_length=100, null=True, blank=True, help_text="Bank name for the DVA"
    )
    dva_assigned_at: datetime = models.DateTimeField(
        null=True, blank=True, help_text="When the DVA was assigned"
    )
    updated_at: datetime = models.DateTimeField(
        auto_now=True, help_text="When the wallet was last updated"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the wallet was created"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"

    def __str__(self) -> str:
        """String representation of the Wallet."""
        return f"Wallet of {self.user.email}"

    # You might want to automatically create a Wallet for a new User
    # This is handled by a signal below.




class Transaction(models.Model):
    """
    Model representing a transaction (deposit, withdrawal, payment) in the wallet.
    """
    TRANSACTION_TYPES = [
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Payment', 'Payment'),
    ]
    TRANSACTION_STATUSES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Reversed', 'Reversed'),
    ]
    user: 'User' = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions",
        help_text="User who performed the transaction"
    )
    transaction_type: str = models.CharField(
        max_length=20, choices=TRANSACTION_TYPES, help_text="Type of transaction"
    )
    reference: str = models.CharField(
        max_length=50, unique=True, null=True, blank=True, help_text="External reference (e.g., Paystack)"
    )
    amount: float = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Transaction amount"
    )
    status: str = models.CharField(
        max_length=10, choices=TRANSACTION_STATUSES, default='Pending', help_text="Transaction status"
    )
    paystack_transaction_id: int = models.IntegerField(
        null=True, blank=True, help_text="Paystack transaction ID (internal)"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the transaction was created"
    )
    updated_at: datetime = models.DateTimeField(
        auto_now=True, help_text="When the transaction was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self) -> str:
        """String representation of the Transaction."""
        return f"{self.transaction_type} - {self.amount} by {self.user.email} ({self.status})"




class Withdrawal(models.Model):
    """
    Model representing a withdrawal request from a user's wallet.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Reversed', 'Reversed'),
    ]
    user: 'User' = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="withdrawals",
        help_text="User requesting the withdrawal"
    )
    bank_name: str = models.CharField(
        max_length=100, help_text="Bank name for the withdrawal"
    )
    account_number: str = models.CharField(
        max_length=20, help_text="Bank account number for the withdrawal"
    )
    account_name: str = models.CharField(
        max_length=200, null=True, blank=True, help_text="Account name (verified by Paystack)"
    )
    amount: float = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Withdrawal amount"
    )
    paystack_recipient_code: str = models.CharField(
        max_length=50, null=True, blank=True, help_text="Paystack Transfer Recipient Code"
    )
    paystack_transfer_reference: str = models.CharField(
        max_length=50, unique=True, null=True, blank=True, help_text="Unique reference for Paystack transfer"
    )
    paystack_transfer_id: int = models.IntegerField(
        null=True, blank=True, help_text="Paystack internal Transfer ID"
    )
    status: str = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='Pending', help_text="Withdrawal status"
    )
    failure_reason: str = models.TextField(
        null=True, blank=True, help_text="Reason for failure (if any)"
    )
    created_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the withdrawal was created"
    )
    updated_at: datetime = models.DateTimeField(
        auto_now=True, help_text="When the withdrawal was last updated"
    )

    def __str__(self) -> str:
        """String representation of the Withdrawal."""
        return f"Withdrawal by {self.user.email} - {self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']




class Bank(models.Model):
    """
    Model representing a bank supported for wallet withdrawals.
    """
    name: str = models.CharField(
        max_length=100, unique=True, help_text="Bank name"
    )
    code: str = models.CharField(
        max_length=10, unique=True, help_text="Bank code (e.g., NUBAN code)"
    )
    slug: str = models.CharField(
        max_length=100, unique=True, null=True, blank=True, help_text="Paystack slug for the bank"
    )
    is_active: bool = models.BooleanField(
        default=True, help_text="Whether the bank is currently active/available"
    )
    added_at: datetime = models.DateTimeField(
        auto_now_add=True, help_text="When the bank was added"
    )
    updated_at: datetime = models.DateTimeField(
        auto_now=True, help_text="When the bank was last updated"
    )

    def __str__(self) -> str:
        """String representation of the Bank."""
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


# Signal to create a Wallet for every new User
@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

# Signal to save the Wallet when the User is saved (though OneToOneField might handle this implicitly)
@receiver(post_save, sender=User)
def save_user_wallet(sender, instance, **kwargs):
    try:
        instance.wallet.save()
    except Wallet.DoesNotExist:
        # This might happen if a user is created without the signal above firing,
        # or if the wallet was manually deleted.
        # Consider creating it here as a fallback or logging an error.
        Wallet.objects.create(user=instance)

