from django import forms

from clubs.models import Club

from .models import Competition, CompetitionTeam


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = [
            "season",
            "name",
            "competition_type",
            "status",
            "double_round_robin",
            "points_win",
            "points_draw",
            "points_loss",
            "two_legged_ties",
            "extra_time_enabled",
            "penalties_enabled",
            "has_third_place_playoff",
            "teams_qualifying_per_group",
        ]
        widgets = {
            "competition_type": forms.Select(attrs={"id": "id_competition_type"}),
        }


class TeamEntryForm(forms.Form):
    """Bulk-add clubs to a competition from a single multi-select."""

    clubs = forms.ModelMultipleChoiceField(
        queryset=Club.objects.filter(status=Club.Status.ACTIVE),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select clubs to enter into this competition",
    )

    def save(self, competition):
        created = []
        for club in self.cleaned_data["clubs"]:
            entry, was_created = CompetitionTeam.objects.get_or_create(competition=competition, club=club)
            if was_created:
                created.append(entry)
        return created