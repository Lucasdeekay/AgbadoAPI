from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from auth_app.models import User


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Paystack Customer ID for this user
    # This is crucial for creating DVAs and managing customer-related operations
    paystack_customer_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Dedicated Virtual Account details for deposits
    dva_account_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    dva_account_name = models.CharField(max_length=200, null=True, blank=True)
    dva_bank_name = models.CharField(max_length=100, null=True, blank=True)
    dva_assigned_at = models.DateTimeField(null=True, blank=True) # When the DVA was assigned

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True) # Add created_at for better tracking

    def __str__(self):
        return f"Wallet of {self.user.email}"

    # You might want to automatically create a Wallet for a new User
    # This is handled by a signal below.


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Payment', 'Payment'), # E.g., payment for a service on your platform
    ]
    
    TRANSACTION_STATUSES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Reversed', 'Reversed'), # For funds returned after a failed withdrawal
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Use a more descriptive name for transaction_id if it's external (e.g., Paystack reference)
    # This will store the Paystack `reference` for deposits (charge.success) or transfers
    reference = models.CharField(max_length=50, unique=True, null=True, blank=True) 
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUSES, default='Pending')
    
    # Optional: Store Paystack's transaction ID (distinct from reference) if needed
    paystack_transaction_id = models.IntegerField(null=True, blank=True, help_text="Paystack transaction ID (internal)")

    # You can add a field to link to the Withdrawal model if transaction_type is 'Withdrawal'
    # For now, `reference` will be enough to link back to Paystack's transfer.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} by {self.user.email} ({self.status})"


class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'), # Initiated by user, waiting for processing
        ('Processing', 'Processing'), # Sent to Paystack, waiting for their response
        ('Completed', 'Completed'), # Successfully transferred by Paystack
        ('Failed', 'Failed'),       # Failed by Paystack
        ('Reversed', 'Reversed'),   # Funds returned to wallet after Paystack failure
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawals")
    
    # Bank details provided by the user for this specific withdrawal
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200, null=True, blank=True) # Will be verified by Paystack

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Paystack transfer recipient code
    # This identifies the beneficiary on Paystack's side. You might create one per account number.
    paystack_recipient_code = models.CharField(max_length=50, null=True, blank=True, 
                                               help_text="Paystack Transfer Recipient Code")
    
    # Paystack transfer reference for this withdrawal request
    paystack_transfer_reference = models.CharField(max_length=50, unique=True, null=True, blank=True, 
                                                    help_text="Unique reference for Paystack transfer")
    
    # Optional: Paystack's internal ID for the transfer
    paystack_transfer_id = models.IntegerField(null=True, blank=True, help_text="Paystack internal Transfer ID")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    
    # Reason for failure (if any)
    failure_reason = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Track when the status changes

    def __str__(self):
        return f"Withdrawal by {self.user.email} - {self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at'] # Order by most recent withdrawals first


class Bank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    slug = models.CharField(max_length=100, unique=True, null=True, blank=True) # Paystack slug
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
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

