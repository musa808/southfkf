from django.contrib import admin
from .models import Coach


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ("full_name", "club", "role", "license_level", "is_active", "phone_number")
    list_filter = ("role", "license_level", "is_active", "club")
    search_fields = ("first_name", "last_name", "email", "phone_number")
    autocomplete_fields = ("club",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Personal Info", {
            "fields": ("user", "first_name", "last_name", "date_of_birth", "nationality", "photo")
        }),
        ("Club & Role", {
            "fields": ("club", "role", "license_level", "date_joined_club", "is_active")
        }),
        ("Contact", {
            "fields": ("email", "phone_number")
        }),
        ("Other", {
            "fields": ("bio", "created_at", "updated_at")
        }),
    )