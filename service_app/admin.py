"""
Service app admin configuration.

This module configures Django admin interface for service management models
including services, subservices, service requests, bids, and bookings.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Service, SubService, ServiceRequest, ServiceRequestBid, Booking


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Admin configuration for Service model.
    
    Provides comprehensive management interface for services including
    filtering, searching, and bulk actions.
    """
    list_display = (
        'get_provider_name', 'name', 'get_category_display', 
        'get_price_range', 'is_active_display', 'get_subservices_count',
        'created_at'
    )
    list_filter = (
        'category', 'is_active', 'created_at', 'provider__business_category'
    )
    search_fields = (
        'name', 'description', 'provider__company_name', 
        'provider__company_email'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'name', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('min_price', 'max_price')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_services', 'deactivate_services', 'reset_prices']

    def get_provider_name(self, obj):
        """Get provider company name."""
        return obj.provider.company_name if obj.provider else 'N/A'
    get_provider_name.short_description = 'Provider'
    get_provider_name.admin_order_field = 'provider__company_name'

    def get_category_display(self, obj):
        """Get formatted category display."""
        return format_html(
            '<span style="color: #007bff; font-weight: bold;">{}</span>',
            obj.get_category_display()
        )
    get_category_display.short_description = 'Category'

    def get_price_range(self, obj):
        """Get formatted price range."""
        return format_html(
            '<span style="color: #28a745;">₦{:,} - ₦{:,}</span>',
            obj.min_price, obj.max_price
        )
    get_price_range.short_description = 'Price Range'

    def is_active_display(self, obj):
        """Get formatted active status."""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">✗ Inactive</span>'
        )
    is_active_display.short_description = 'Status'

    def get_subservices_count(self, obj):
        """Get count of subservices."""
        count = obj.sub_services.filter(is_active=True).count()
        return format_html(
            '<span style="color: #6c757d;">{}</span>',
            count
        )
    get_subservices_count.short_description = 'Sub Services'

    def activate_services(self, request, queryset):
        """Activate selected services."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'Successfully activated {updated} service(s).'
        )
    activate_services.short_description = "Activate selected services"

    def deactivate_services(self, request, queryset):
        """Deactivate selected services."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'Successfully deactivated {updated} service(s).'
        )
    deactivate_services.short_description = "Deactivate selected services"

    def reset_prices(self, request, queryset):
        """Reset prices to default values."""
        updated = queryset.update(min_price=0, max_price=0)
        self.message_user(
            request, 
            f'Successfully reset prices for {updated} service(s).'
        )
    reset_prices.short_description = "Reset prices for selected services"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('provider')


@admin.register(SubService)
class SubServiceAdmin(admin.ModelAdmin):
    """
    Admin configuration for SubService model.
    
    Provides comprehensive management interface for subservices including
    filtering, searching, and bulk actions.
    """
    list_display = (
        'get_service_name', 'name', 'get_price_display', 
        'is_active_display', 'created_at'
    )
    list_filter = (
        'is_active', 'created_at', 'service__category', 'service__provider'
    )
    search_fields = (
        'name', 'description', 'service__name', 
        'service__provider__company_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    fieldsets = (
        ('Basic Information', {
            'fields': ('service', 'name', 'description')
        }),
        ('Pricing', {
            'fields': ('price',)
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_subservices', 'deactivate_subservices']

    def get_service_name(self, obj):
        """Get parent service name."""
        return obj.service.name if obj.service else 'N/A'
    get_service_name.short_description = 'Service'
    get_service_name.admin_order_field = 'service__name'

    def get_price_display(self, obj):
        """Get formatted price display."""
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">₦{:,}</span>',
            obj.price
        )
    get_price_display.short_description = 'Price'

    def is_active_display(self, obj):
        """Get formatted active status."""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">✗ Inactive</span>'
        )
    is_active_display.short_description = 'Status'

    def activate_subservices(self, request, queryset):
        """Activate selected subservices."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'Successfully activated {updated} subservice(s).'
        )
    activate_subservices.short_description = "Activate selected subservices"

    def deactivate_subservices(self, request, queryset):
        """Deactivate selected subservices."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'Successfully deactivated {updated} subservice(s).'
        )
    deactivate_subservices.short_description = "Deactivate selected subservices"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('service', 'service__provider')


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    """
    Admin configuration for ServiceRequest model.
    
    Provides comprehensive management interface for service requests including
    filtering, searching, and bulk actions.
    """
    list_display = (
        'get_title_display', 'get_user_email', 'get_category_display',
        'get_price_display', 'get_status_display', 'get_bids_count',
        'latitude', 'longitude', 'created_at'
    )
    list_filter = (
        'status', 'category', 'created_at', 'user__state'
    )
    search_fields = (
        'title', 'description', 'user__email', 'user__phone_number'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude'),
        }),
        ('Pricing', {
            'fields': ('price',)
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['approve_requests', 'reject_requests', 'mark_as_completed']

    def get_title_display(self, obj):
        """Get formatted title display."""
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{}</span>',
            obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
        )
    get_title_display.short_description = 'Title'

    def get_user_email(self, obj):
        """Get user email."""
        return obj.user.email if obj.user else 'N/A'
    get_user_email.short_description = 'User'
    get_user_email.admin_order_field = 'user__email'

    def get_category_display(self, obj):
        """Get formatted category display."""
        return format_html(
            '<span style="color: #6c757d; font-weight: bold;">{}</span>',
            obj.get_category_display()
        )
    get_category_display.short_description = 'Category'

    def get_price_display(self, obj):
        """Get formatted price display."""
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">₦{:,}</span>',
            obj.price
        )
    get_price_display.short_description = 'Budget'

    def get_status_display(self, obj):
        """Get formatted status display."""
        status_colors = {
            'pending': '#ffc107',
            'in_progress': '#17a2b8',
            'completed': '#28a745',
            'cancelled': '#dc3545',
            'awarded': '#6f42c1',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Status'

    def get_bids_count(self, obj):
        """Get count of bids."""
        count = obj.bids.count()
        return format_html(
            '<span style="color: #6c757d;">{}</span>',
            count
        )
    get_bids_count.short_description = 'Bids'

    def approve_requests(self, request, queryset):
        """Approve selected requests."""
        updated = queryset.update(status='in_progress')
        self.message_user(
            request, 
            f'Successfully approved {updated} request(s).'
        )
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        """Reject selected requests."""
        updated = queryset.update(status='cancelled')
        self.message_user(
            request, 
            f'Successfully rejected {updated} request(s).'
        )
    reject_requests.short_description = "Reject selected requests"

    def mark_as_completed(self, request, queryset):
        """Mark selected requests as completed."""
        updated = queryset.update(status='completed')
        self.message_user(
            request, 
            f'Successfully marked {updated} request(s) as completed.'
        )
    mark_as_completed.short_description = "Mark selected requests as completed"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(ServiceRequestBid)
class ServiceRequestBidAdmin(admin.ModelAdmin):
    """
    Admin configuration for ServiceRequestBid model.
    
    Provides comprehensive management interface for service request bids including
    filtering, searching, and bulk actions.
    """
    list_display = (
        'get_request_title', 'get_provider_name', 'get_amount_display',
        'get_status_display', 'get_distance_display', 'created_at'
    )
    list_filter = (
        'status', 'created_at', 'provider__business_category'
    )
    search_fields = (
        'service_request__title', 'provider__company_name', 
        'provider__company_email', 'proposal'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    fieldsets = (
        ('Basic Information', {
            'fields': ('service_request', 'provider', 'amount', 'proposal')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude'),
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['accept_bids', 'reject_bids', 'withdraw_bids']

    def get_distance_display(self, obj):
        """Show distance between bid and request."""
        distance = obj.calculate_distance_km()
        if distance is not None:
            return format_html(
                '<span style="color: #007bff; font-weight: bold;">{} km</span>',
                distance
            )
        return format_html(
            '<span style="color: #6c757d;">N/A</span>'
        )
    get_distance_display.short_description = "Distance"


    def get_request_title(self, obj):
        """Get service request title."""
        return obj.service_request.title if obj.service_request else 'N/A'
    get_request_title.short_description = 'Request'
    get_request_title.admin_order_field = 'service_request__title'

    def get_provider_name(self, obj):
        """Get provider company name."""
        return obj.provider.company_name if obj.provider else 'N/A'
    get_provider_name.short_description = 'Provider'
    get_provider_name.admin_order_field = 'provider__company_name'

    def get_amount_display(self, obj):
        """Get formatted amount display."""
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">₦{:,}</span>',
            obj.amount
        )
    get_amount_display.short_description = 'Amount'

    def get_status_display(self, obj):
        """Get formatted status display."""
        status_colors = {
            'pending': '#ffc107',
            'accepted': '#28a745',
            'rejected': '#dc3545',
            'withdrawn': '#6c757d',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Status'

    def accept_bids(self, request, queryset):
        """Accept selected bids."""
        updated = queryset.update(status='accepted')
        self.message_user(
            request, 
            f'Successfully accepted {updated} bid(s).'
        )
    accept_bids.short_description = "Accept selected bids"

    def reject_bids(self, request, queryset):
        """Reject selected bids."""
        updated = queryset.update(status='rejected')
        self.message_user(
            request, 
            f'Successfully rejected {updated} bid(s).'
        )
    reject_bids.short_description = "Reject selected bids"

    def withdraw_bids(self, request, queryset):
        """Withdraw selected bids."""
        updated = queryset.update(status='withdrawn')
        self.message_user(
            request, 
            f'Successfully withdrew {updated} bid(s).'
        )
    withdraw_bids.short_description = "Withdraw selected bids"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'service_request', 'provider'
        )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin configuration for Booking model.
    
    Provides comprehensive management interface for bookings including
    filtering, searching, and bulk actions.
    """
    list_display = (
        'get_service_name', 'get_user_email', 'get_provider_name',
        'get_amount_display', 'get_status_display', 'get_rating_display',
        'booking_date', 'created_at'
    )
    list_filter = (
        'status', 'booking_date', 'created_at', 'user__state',
        'provider__business_category'
    )
    search_fields = (
        'service__name', 'user__email', 'provider__company_name',
        'notes', 'feedback'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'service', 'provider', 'booking_date')
        }),
        ('Pricing', {
            'fields': ('amount',)
        }),
        ('Status & Feedback', {
            'fields': ('status', 'notes', 'feedback', 'rating')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['confirm_bookings', 'mark_as_completed', 'cancel_bookings']

    def get_service_name(self, obj):
        """Get service name."""
        return obj.service.name if obj.service else 'N/A'
    get_service_name.short_description = 'Service'
    get_service_name.admin_order_field = 'service__name'

    def get_user_email(self, obj):
        """Get user email."""
        return obj.user.email if obj.user else 'N/A'
    get_user_email.short_description = 'User'
    get_user_email.admin_order_field = 'user__email'

    def get_provider_name(self, obj):
        """Get provider company name."""
        return obj.provider.company_name if obj.provider else 'N/A'
    get_provider_name.short_description = 'Provider'
    get_provider_name.admin_order_field = 'provider__company_name'

    def get_amount_display(self, obj):
        """Get formatted amount display."""
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">₦{:,}</span>',
            obj.amount
        )
    get_amount_display.short_description = 'Amount'

    def get_status_display(self, obj):
        """Get formatted status display."""
        status_colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'cancelled': '#dc3545',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_display.short_description = 'Status'

    def get_rating_display(self, obj):
        """Get formatted rating display."""
        if obj.rating:
            stars = '★' * obj.rating + '☆' * (5 - obj.rating)
            return format_html(
                '<span style="color: #ffc107;">{}</span>',
                stars
            )
        return format_html(
            '<span style="color: #6c757d;">No rating</span>'
        )
    get_rating_display.short_description = 'Rating'

    def confirm_bookings(self, request, queryset):
        """Confirm selected bookings."""
        updated = queryset.update(status='confirmed')
        self.message_user(
            request, 
            f'Successfully confirmed {updated} booking(s).'
        )
    confirm_bookings.short_description = "Confirm selected bookings"

    def mark_as_completed(self, request, queryset):
        """Mark selected bookings as completed."""
        updated = queryset.update(status='completed')
        self.message_user(
            request, 
            f'Successfully marked {updated} booking(s) as completed.'
        )
    mark_as_completed.short_description = "Mark selected bookings as completed"

    def cancel_bookings(self, request, queryset):
        """Cancel selected bookings."""
        updated = queryset.update(status='cancelled')
        self.message_user(
            request, 
            f'Successfully cancelled {updated} booking(s).'
        )
    cancel_bookings.short_description = "Cancel selected bookings"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'user', 'service', 'provider'
        )

    def has_add_permission(self, request):
        """Disable manual booking creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable booking deletion."""
        return False

