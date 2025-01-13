from django.contrib import admin
from .models import ServiceProvider


# Registering the ServiceProvider model with custom admin interface
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'company_name', 'company_address', 'company_phone_no', 'company_email',
        'business_category', 'avg_rating', 'rating_population', 'is_approved', 'created_at'
    )
    search_fields = ('user__email', 'company_name', 'company_email')
    list_filter = ('is_approved', 'business_category')
    ordering = ('-created_at',)

    # Customizing the form display for more comprehensive fields
    fieldsets = (
        (None, {
            'fields': ('user', 'company_name', 'company_address', 'company_description',
                       'company_phone_no', 'company_email', 'business_category', 'company_logo')
        }),
        ('Business Hours', {
            'fields': ('opening_hour', 'closing_hour')
        }),
        ('Ratings', {
            'fields': ('avg_rating', 'rating_population')
        }),
        ('Approval Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    # You can add actions or filters for additional customization, if needed
    actions = ['approve_service_provider']

    def approve_service_provider(self, request, queryset):
        queryset.update(is_approved=True)
    approve_service_provider.short_description = 'Approve selected service providers'


admin.site.register(ServiceProvider, ServiceProviderAdmin)
