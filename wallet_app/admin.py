from django.contrib import admin
from .models import Wallet, Transaction, Withdrawal


# Registering the Wallet model with custom admin interface
class WalletAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = (
        'user',
        'balance',
        'paystack_customer_code',
        'dva_account_number',
        'dva_bank_name', # Display bank name directly
        'updated_at',
        'created_at', # Added created_at
    )
    
    # Enable searching by user email and Paystack customer code
    search_fields = ('user__email', 'paystack_customer_code', 'dva_account_number')
    
    # Filter by user service provider status (if applicable) and DVA assignment status
    list_filter = ('user__is_service_provider', 'dva_account_number', 'dva_bank_name')
    
    ordering = ('-created_at',) # Order by creation date descending

    # Fields that should not be editable in the admin form
    readonly_fields = (
        'created_at',
        'updated_at',
        'paystack_customer_code', # These are typically set by your system, not manually edited
        'dva_account_number',
        'dva_account_name',
        'dva_bank_name',
        'dva_assigned_at',
    )

    # Organize fields in the add/change form for better readability
    fieldsets = (
        (None, {
            'fields': ('user', 'balance')
        }),
        ('Paystack Customer Details', {
            'fields': ('paystack_customer_code',),
            'description': 'This is the unique Paystack identifier for the user.'
        }),
        ('Dedicated Virtual Account (DVA) Details', {
            'fields': ('dva_account_number', 'dva_account_name', 'dva_bank_name', 'dva_assigned_at'),
            'description': 'Details of the Paystack Dedicated Virtual Account for deposits.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',), # Makes this section collapsible
        }),
    )


# Registering the Transaction model with custom admin interface
class TransactionAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = (
        'user',
        'amount',
        'transaction_type',
        'status',
        'reference', # Use 'reference' instead of 'transaction_id'
        'paystack_transaction_id', # Show Paystack's internal ID
        'created_at',
        'updated_at',
    )
    
    # Enable searching by user email and Paystack reference
    search_fields = ('user__email', 'reference', 'paystack_transaction_id__exact') # __exact for exact match on int
    
    # Filter by transaction type and status
    list_filter = ('transaction_type', 'status', 'created_at')
    
    ordering = ('-created_at',)
    
    # Fields that should not be editable in the admin form
    readonly_fields = (
        'created_at',
        'updated_at',
        'reference',
        'paystack_transaction_id',
    )

    # Organize fields in the add/change form
    fieldsets = (
        (None, {
            'fields': ('user', 'amount', 'transaction_type', 'status')
        }),
        ('Paystack Details', {
            'fields': ('reference', 'paystack_transaction_id'),
            'description': 'External reference and ID from Paystack for this transaction.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


class WithdrawalAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = [
        'user',
        'amount',
        'bank_name',
        'account_number',
        'account_name', # Display verified account name
        'status',
        'paystack_transfer_reference', # Show Paystack's transfer reference
        'created_at',
        'updated_at',
    ]
    
    # Filter by status and creation date
    list_filter = ['status', 'created_at', 'bank_name']
    
    # Enable searching by user email, bank details, and Paystack reference
    search_fields = [
        'user__email',
        'bank_name',
        'account_number',
        'account_name',
        'paystack_transfer_reference',
    ]
    
    ordering = ['-created_at']
    
    # Fields that should not be editable in the admin form
    readonly_fields = (
        'created_at',
        'updated_at',
        'paystack_recipient_code',
        'paystack_transfer_reference',
        'paystack_transfer_id',
        # account_name might be read-only if it's set after Paystack verification
        # bank_name and account_number might be editable if you allow manual corrections
    )

    # Organize fields in the add/change form
    fieldsets = (
        (None, {
            'fields': ('user', 'amount', 'bank_name', 'account_number', 'account_name', 'status', 'failure_reason')
        }),
        ('Paystack Transfer Details', {
            'fields': ('paystack_recipient_code', 'paystack_transfer_reference', 'paystack_transfer_id'),
            'description': 'Details related to the Paystack transfer for this withdrawal.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Withdrawal, WithdrawalAdmin)