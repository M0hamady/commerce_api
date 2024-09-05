# admin.py
from django.contrib import admin
from .models import Visit

class VisitAdmin(admin.ModelAdmin):
    list_display = ('slug', 'page_url', 'created_at')
    search_fields = ('slug', 'page_url')
    list_filter = ('created_at',)
    readonly_fields = ('slug', 'created_at')
    
    # Optional: Customize the form if needed
    fieldsets = (
        (None, {
            'fields': ('slug', 'page_url')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

admin.site.register(Visit, VisitAdmin)
