from django.contrib import admin

from .models import Season


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    ordering = ("-start_date",)