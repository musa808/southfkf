from django.contrib import admin
from .models import Referee, RefereeAssignment


class RefereeAssignmentInline(admin.TabularInline):
    model = RefereeAssignment
    extra = 1
    autocomplete_fields = ("fixture",)


@admin.register(Referee)
class RefereeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "grade", "home_region", "is_active", "phone_number")
    list_filter = ("grade", "is_active", "home_region")
    search_fields = ("first_name", "last_name", "email", "license_number", "phone_number")
    readonly_fields = ("created_at", "updated_at")
    inlines = [RefereeAssignmentInline]


@admin.register(RefereeAssignment)
class RefereeAssignmentAdmin(admin.ModelAdmin):
    list_display = ("referee", "fixture", "role", "confirmed", "fee")
    list_filter = ("role", "confirmed")
    search_fields = ("referee__first_name", "referee__last_name")
    autocomplete_fields = ("referee", "fixture")