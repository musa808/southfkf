from django.contrib import admin

from .models import GoalEvent, MatchResult


class GoalEventInline(admin.TabularInline):
    model = GoalEvent
    extra = 1
    autocomplete_fields = ["scorer"]
    fields = ["scorer", "scorer_name_fallback", "minute", "period", "is_own_goal", "is_penalty"]


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = (
        "fixture", "home_score", "away_score",
        "went_to_extra_time", "went_to_penalties", "created_at",
    )
    list_filter = ("fixture__competition",)
    search_fields = (
        "fixture__home_team__club__name",
        "fixture__away_team__club__name",
    )
    autocomplete_fields = ["fixture"]
    inlines = [GoalEventInline]

    def save_model(self, request, obj, form, change):
        """Mark the fixture as PLAYED when a result is recorded via admin."""
        super().save_model(request, obj, form, change)
        obj.fixture.status = obj.fixture.Status.PLAYED
        obj.fixture.save(update_fields=["status"])


@admin.register(GoalEvent)
class GoalEventAdmin(admin.ModelAdmin):
    list_display = ("result", "scorer_display", "minute", "period", "is_own_goal", "is_penalty")
    list_filter = ("result__fixture__competition",)
    autocomplete_fields = ["scorer"]

    def scorer_display(self, obj):
        return obj.scorer_display
    scorer_display.short_description = "Scorer"