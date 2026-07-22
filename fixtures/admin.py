from django.contrib import admin

from .models import Fixture


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = (
        "competition",
        "home_team",
        "away_team",
        "round_number",
        "leg",
        "match_date",
        "status",
    )

    list_filter = (
        "competition",
        "status",
        "leg",
    )

    search_fields = (
        "home_team__club__name",
        "away_team__club__name",
    )

    autocomplete_fields = [
        "home_team",
        "away_team",
        "group",
        "knockout_fixture",
    ]

    date_hierarchy = "match_date"