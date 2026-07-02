from django.contrib import admin

from .models import Click, ShortURL


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'original_url', 'owner', 'clicks', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('short_code', 'original_url', 'owner__username')
    readonly_fields = ('short_code', 'clicks', 'created_at')


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ('short_url', 'created_at', 'browser', 'device', 'referrer')
    list_filter = ('browser', 'device', 'created_at')
    search_fields = ('short_url__short_code', 'referrer')
    readonly_fields = ('short_url', 'created_at', 'referrer', 'ip_address', 'browser', 'device')
