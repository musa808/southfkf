from django import forms
from django.forms import inlineformset_factory

from .models import GoalEvent, MatchResult


class MatchResultForm(forms.ModelForm):

    class Meta:
        model = MatchResult
        fields = [
            "home_score", "away_score",
            "went_to_extra_time",
            "home_score_et", "away_score_et",
            "went_to_penalties",
            "home_penalties", "away_penalties",
            "played_at", "notes",
        ]
        widgets = {
            "played_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class GoalEventForm(forms.ModelForm):

    class Meta:
        model = GoalEvent
        fields = [
            "scorer", "scorer_name_fallback",
            "minute", "period",
            "is_own_goal", "is_penalty",
        ]

    def __init__(self, *args, fixture=None, **kwargs):
        super().__init__(*args, **kwargs)
        if fixture:
            from players.models import Player
            # Limit scorer choices to players from both clubs in this fixture.
            club_ids = [
                fixture.home_team.club_id,
                fixture.away_team.club_id,
            ]
            self.fields["scorer"].queryset = (
                Player.objects.filter(club_id__in=club_ids)
                .select_related("club")
                .order_by("club__name", "last_name")
            )
            self.fields["scorer"].required = False


# Inline formset for goal events — up to 22 goals per match (generous upper bound).
GoalEventFormSet = inlineformset_factory(
    MatchResult,
    GoalEvent,
    form=GoalEventForm,
    extra=3,
    can_delete=True,
    max_num=22,
)