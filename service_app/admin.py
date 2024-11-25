from django.contrib import admin
from .models import Service, SubService, ServiceRequest

# Registering the Service model with custom admin interface
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('provider', 'name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)


# Registering the SubService model with custom admin interface
class SubServiceAdmin(admin.ModelAdmin):
    list_display = ('service', 'name', 'description', 'price', 'created_at')
    search_fields = ('service__name', 'name')
    list_filter = ('name',)
    ordering = ('-created_at',)


# Registering the ServiceRequest model with custom admin interface
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'sub_service', 'status', 'requested_at', 'completed_at')
    search_fields = ('user__email', 'service__name', 'status')
    list_filter = ('status', 'service', 'sub_service')
    ordering = ('-requested_at',)


admin.site.register(Service, ServiceAdmin)
admin.site.register(SubService, SubServiceAdmin)
admin.site.register(ServiceRequest, ServiceRequestAdmin)
