from django.contrib import admin
from .models import Service, SubService, ServiceRequest, ServiceRequestBid, Booking


# Registering the Service model with custom admin interface
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('provider', 'name', 'description', 'category', 'min_price', 'max_price', 'is_active', 'created_at')
    search_fields = ('name', 'category', 'is_active')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)  # Add this to allow display but not editing


# Registering the SubService model with custom admin interface
@admin.register(SubService)
class SubServiceAdmin(admin.ModelAdmin):
    list_display = ('service', 'name', 'description', 'price', 'created_at')
    search_fields = ('service__name', 'name')
    list_filter = ('name',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)  # Add this to allow display but not editing


# Registering the ServiceRequest model with custom admin interface
@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'price', 'status', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('status', 'category', 'created_at')
    readonly_fields = ('created_at',)  # Add this to allow display but not editing


# Registering the ServiceRequestBid model with custom admin interface
@admin.register(ServiceRequestBid)
class ServiceRequestBidAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'service_provider', 'price', 'status', 'created_at')
    search_fields = ('service_request__title', 'service_provider__email')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at',)  # Add this to allow display but not editing


# Registering the Booking model with custom admin interface
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'user', 'service_provider', 'price', 'user_status', 'provider_status', 'created_at')
    search_fields = ('service_request__title', 'user__email', 'service_provider__email')
    list_filter = ('user_status', 'provider_status', 'created_at')
    readonly_fields = ('created_at',)  # Add this to allow display but not editing

