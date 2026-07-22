from django import forms

from .models import Fixture


class GenerateLeagueFixturesForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    days_between_rounds = forms.IntegerField(
        initial=7, min_value=1, help_text="Number of days between each round of matches."
    )
    venue = forms.CharField(
        required=False, max_length=150, help_text="Default venue for all generated fixtures (you can edit individually after)."
    )


class GenerateGroupFixturesForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    days_between_rounds = forms.IntegerField(initial=7, min_value=1)
    venue = forms.CharField(required=False, max_length=150)


class KnockoutSlotTeamsForm(forms.Form):
    """
    Lets the admin manually assign which two entered teams occupy a
    knockout bracket slot (KnockoutFixture), since auto-seeding isn't
    reliable without real-world ranking data.
    """

    team_a = forms.ModelChoiceField(queryset=None, required=False, label="Team A")
    team_b = forms.ModelChoiceField(queryset=None, required=False, label="Team B")

    def __init__(self, *args, competition=None, **kwargs):
        super().__init__(*args, **kwargs)
        from competitions.models import CompetitionTeam
        qs = CompetitionTeam.objects.filter(competition=competition).select_related("club")
        self.fields["team_a"].queryset = qs
        self.fields["team_b"].queryset = qs


class KnockoutFixtureScheduleForm(forms.ModelForm):
    """
    Used to assign a date/venue to a Fixture that already exists for a
    knockout slot (the slot's teams are set separately via the
    competitions app's bracket-slot editor).
    """

    class Meta:
        model = Fixture
        fields = ["match_date", "kickoff_time", "venue", "status"]
        widgets = {
            "match_date": forms.DateInput(attrs={"type": "date"}),
            "kickoff_time": forms.TimeInput(attrs={"type": "time"}),
        }


class FixtureEditForm(forms.ModelForm):
    """General-purpose edit form for any fixture (league, group, or knockout)."""

    class Meta:
        model = Fixture
        fields = ["match_date", "kickoff_time", "venue", "status"]
        widgets = {
            "match_date": forms.DateInput(attrs={"type": "date"}),
            "kickoff_time": forms.TimeInput(attrs={"type": "time"}),
        }