from django.contrib import admin

from .models import (
    Competition,
    CompetitionTeam,
    Group,
    GroupTeam,
    KnockoutFixture,
    KnockoutRound,
)


class CompetitionTeamInline(admin.TabularInline):
    model = CompetitionTeam
    extra = 1
    autocomplete_fields = ["club"]


class GroupInline(admin.TabularInline):
    model = Group
    extra = 0


class KnockoutRoundInline(admin.TabularInline):
    model = KnockoutRound
    extra = 0


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "season",
        "competition_type",
        "status",
        "created_at",
    )

    list_filter = (
        "competition_type",
        "status",
        "season",
    )

    search_fields = ("name",)

    inlines = [
        CompetitionTeamInline,
        GroupInline,
        KnockoutRoundInline,
    ]


class GroupTeamInline(admin.TabularInline):
    model = GroupTeam
    extra = 1
    autocomplete_fields = ["competition_team"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "competition",
    )

    list_filter = (
        "competition",
    )

    search_fields = (
        "name",
    )

    inlines = [
        GroupTeamInline,
    ]


class KnockoutFixtureInline(admin.TabularInline):
    model = KnockoutFixture
    extra = 0
    autocomplete_fields = [
        "team_a",
        "team_b",
        "winner",
        "feeds_into",
    ]


@admin.register(KnockoutRound)
class KnockoutRoundAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "competition",
        "order",
    )

    list_filter = (
        "competition",
    )

    ordering = (
        "competition",
        "order",
    )

    inlines = [
        KnockoutFixtureInline,
    ]


@admin.register(KnockoutFixture)
class KnockoutFixtureAdmin(admin.ModelAdmin):
    list_display = (
        "round",
        "slot_number",
        "team_a",
        "team_b",
        "winner",
    )

    list_filter = (
        "round__competition",
    )

    search_fields = (
        "team_a__club__name",
        "team_b__club__name",
    )

    autocomplete_fields = [
        "team_a",
        "team_b",
        "winner",
        "feeds_into",
    ]


@admin.register(CompetitionTeam)
class CompetitionTeamAdmin(admin.ModelAdmin):
    list_display = (
        "club",
        "competition",
        "status",
        "entered_at",
    )

    list_filter = (
        "competition",
        "status",
    )

    search_fields = (
        "club__name",
    )

    autocomplete_fields = [
        "club",
    ]