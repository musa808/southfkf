from django.contrib import admin

from .models import Club


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "ward", "registration_number", "status", "created_at")
    list_filter = ("status", "ward")
    search_fields = ("name", "registration_number", "ward")
    ordering = ("name",)