from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "role", "club", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")

    fieldsets = UserAdmin.fieldsets + (
        ("FCMS Role", {"fields": ("role", "club", "phone_number")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("FCMS Role", {"fields": ("role", "club", "phone_number")}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name() or "—"
    get_full_name.short_description = "Full Name"