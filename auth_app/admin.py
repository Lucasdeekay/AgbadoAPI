from django.contrib import admin
from .models import User, KYC, OTP, Referral


# Registering the User model with custom admin interface
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_service_provider', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_service_provider')
    ordering = ('-date_joined',)


# Registering the KYC model with custom admin interface
class KYCAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'updated_at', 'verified_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)
    ordering = ('-updated_at',)


class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'is_used')
    search_fields = ('user__email', 'is_used')
    list_filter = ('is_used',)
    ordering = ('-created_at',)

class ReferralAdmin(admin.ModelAdmin):
    list_display = ('user', 'referer', 'created_at',)
    search_fields = ('user__email',)
    ordering = ('-created_at',)


admin.site.register(User, UserAdmin)
admin.site.register(KYC, KYCAdmin)
admin.site.register(OTP, OTPAdmin)
admin.site.register(Referral, ReferralAdmin)
