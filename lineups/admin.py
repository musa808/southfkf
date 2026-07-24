from django.contrib import admin

from .models import Lineup, LineupPlayer


class LineupPlayerInline(admin.TabularInline):
    model = LineupPlayer
    extra = 0
    fields = ["player", "role", "is_captain", "shirt_number", "position_label", "order"]
    autocomplete_fields = ["player"]


@admin.register(Lineup)
class LineupAdmin(admin.ModelAdmin):
    list_display = ("team", "fixture", "formation", "starter_count", "sub_count", "submitted_at")
    list_filter  = ("fixture__competition", "formation")
    search_fields = ("team__club__name",)
    inlines = [LineupPlayerInline]
    readonly_fields = ("submitted_at", "updated_at")

    def starter_count(self, obj):
        return obj.starter_count
    starter_count.short_description = "Starters"

    def sub_count(self, obj):
        return obj.sub_count
    sub_count.short_description = "Subs"