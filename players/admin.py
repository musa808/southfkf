from django.contrib import admin

from .models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "club", "position", "jersey_number", "status")
    list_filter = ("club", "position", "status")
    search_fields = ("first_name", "last_name", "club__name")
    autocomplete_fields = ["club"]