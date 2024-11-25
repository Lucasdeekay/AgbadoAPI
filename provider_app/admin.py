from django.contrib import admin
from .models import ServiceProvider


# Registering the ServiceProvider model with custom admin interface
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'contact_info', 'is_approved', 'created_at')
    search_fields = ('user__email', 'company_name')
    list_filter = ('is_approved',)
    ordering = ('-created_at',)


admin.site.register(ServiceProvider, ServiceProviderAdmin)
