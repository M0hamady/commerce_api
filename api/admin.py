from django.contrib import admin
from django.utils.html import format_html
from .models import User, BlacklistedToken

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'mobile_number', 'location', 'position_title', 'is_client', 'image_tag')
    list_filter = ('is_client', 'job_position_title')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('image_tag',)  # Make image_tag readonly

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.get_image_url)
        return "-"
    image_tag.short_description = 'Profile Image'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only run this if creating a new user
            # Perform additional actions for new users if needed
            pass
        super().save_model(request, obj, form, change)

class BlacklistedTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'revoked_at')
    search_fields = ('token',)

admin.site.register(User, UserAdmin)
admin.site.register(BlacklistedToken, BlacklistedTokenAdmin)
