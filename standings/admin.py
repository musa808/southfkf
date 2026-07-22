from django.contrib import admin
from .models import StandingsRow


@admin.register(StandingsRow)
class StandingsRowAdmin(admin.ModelAdmin):
    list_display = (
        "team", "competition", "group", "played",
        "won", "drawn", "lost", "goals_for", "goals_against", "points",
    )
    list_filter = ("competition", "group")
    ordering = ("competition", "-points", "-goals_for")