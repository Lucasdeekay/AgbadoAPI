"""
Admin interface for auth app models.

This module contains admin configurations for user management,
KYC verification, OTP handling, and referral tracking.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import User, KYC, OTP, Referral, WebAuthnCredential


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Admin interface for User model.
    
    Provides comprehensive user management with filtering,
    searching, and bulk actions.
    """
    list_display = (
        'email', 'get_full_name', 'phone_number', 'state', 
        'is_active', 'is_service_provider', 'is_verified', 
        'is_busy', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_service_provider', 'is_verified', 
        'is_busy', 'state', 'date_joined'
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'referral_code')
    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'state')
        }),
        ('Profile', {
            'fields': ('profile_picture', 'referral_code', 'pin')
        }),
        ('Status', {
            'fields': ('is_active', 'is_service_provider', 'is_verified', 'is_busy')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login')
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related()


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    """
    Admin interface for KYC model.
    
    Provides KYC verification management with document tracking
    and status management.
    """
    list_display = (
        'user', 'status', 'get_document_count', 'updated_at', 
        'verified_at', 'get_user_email'
    )
    list_filter = ('status', 'updated_at', 'verified_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('-updated_at',)
    readonly_fields = ('updated_at', 'verified_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Documents', {
            'fields': ('national_id', 'driver_license', 'proof_of_address', 'bvn')
        }),
        ('Status', {
            'fields': ('status', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('updated_at',)
        }),
    )

    def get_user_email(self, obj):
        """Get user email for display."""
        return obj.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'

    def get_document_count(self, obj):
        """Get count of uploaded documents."""
        count = sum([
            1 if obj.national_id else 0,
            1 if obj.driver_license else 0,
            1 if obj.proof_of_address else 0,
            1 if obj.bvn else 0
        ])
        return f"{count}/4"
    get_document_count.short_description = 'Documents'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """
    Admin interface for OTP model.
    
    Provides OTP management with expiration tracking
    and usage status.
    """
    list_display = (
        'user', 'otp', 'created_at', 'expires_at', 
        'is_used', 'is_expired_display'
    )
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'otp')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'expires_at')
    fieldsets = (
        ('OTP Information', {
            'fields': ('user', 'otp')
        }),
        ('Status', {
            'fields': ('is_used',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        }),
    )

    def is_expired_display(self, obj):
        """Display if OTP is expired."""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_display.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    """
    Admin interface for Referral model.
    
    Provides referral tracking with user relationship
    management.
    """
    list_display = (
        'user', 'referer', 'created_at', 'get_user_email', 
        'get_referer_email'
    )
    list_filter = ('created_at',)
    search_fields = ('user__email', 'referer__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Referral Information', {
            'fields': ('user', 'referer')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def get_user_email(self, obj):
        """Get referred user email."""
        return obj.user.email
    get_user_email.short_description = 'Referred User'
    get_user_email.admin_order_field = 'user__email'

    def get_referer_email(self, obj):
        """Get referer email."""
        return obj.referer.email
    get_referer_email.short_description = 'Referer'
    get_referer_email.admin_order_field = 'referer__email'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'referer')


@admin.register(WebAuthnCredential)
class WebAuthnCredentialAdmin(admin.ModelAdmin):
    """
    Admin interface for WebAuthnCredential model.
    
    Provides WebAuthn credential management for
    passwordless authentication.
    """
    list_display = (
        'user', 'credential_id_short', 'transports', 
        'registered_at', 'last_used', 'sign_count'
    )
    list_filter = ('transports', 'registered_at', 'last_used')
    search_fields = ('user__email', 'credential_id')
    ordering = ('-registered_at',)
    readonly_fields = ('registered_at', 'last_used', 'sign_count')
    fieldsets = (
        ('Credential Information', {
            'fields': ('user', 'credential_id', 'public_key', 'transports')
        }),
        ('Security', {
            'fields': ('sign_count',)
        }),
        ('Timestamps', {
            'fields': ('registered_at', 'last_used')
        }),
    )

    def credential_id_short(self, obj):
        """Display shortened credential ID."""
        return f"{obj.credential_id[:20]}..." if len(obj.credential_id) > 20 else obj.credential_id
    credential_id_short.short_description = 'Credential ID'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
