from django import forms

from players.models import Player

from .models import Lineup, LineupPlayer


class LineupForm(forms.ModelForm):
    """Formation and notes fields for the lineup header."""

    class Meta:
        model = Lineup
        fields = ["formation", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Optional tactical notes...",
            }),
        }


class LineupPlayerForm(forms.Form):
    """
    Dynamic form for selecting players in a lineup.
    Rendered once per available player in the club's squad.
    The view builds a formset from these.
    """

    player_id  = forms.IntegerField(widget=forms.HiddenInput)
    role       = forms.ChoiceField(
        choices=[("", "Not selected")] + list(LineupPlayer.Role.choices),
        required=False,
        widget=forms.Select(attrs={
            "class": "form-select form-select-sm role-select role-field",
        }),
    )
    is_captain = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            "class": "form-check-input captain-field",
        }),
    )
    shirt_number = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "No.",
            "min": 1, "max": 99,
            "style": "width:60px;",
        }),
    )
    position_label = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "e.g. Left Wing",
            "style": "min-width:120px;",
        }),
    )


def build_lineup_player_forms(squad, existing_lineup=None):
    """
    Build a list of pre-populated LineupPlayerForm instances
    for every player in the squad. If a lineup already exists,
    pre-fill their role/captain/shirt from saved data.
    """
    existing_map = {}
    if existing_lineup:
        for lp in existing_lineup.players.select_related("player"):
            existing_map[lp.player_id] = lp

    forms_list = []
    for player in squad:
        lp = existing_map.get(player.id)
        initial = {
            "player_id": player.id,
            "role":           lp.role          if lp else "",
            "is_captain":     lp.is_captain     if lp else False,
            "shirt_number":   lp.shirt_number   if lp else player.jersey_number,
            "position_label": lp.position_label if lp else player.get_position_display(),
        }
        forms_list.append((player, LineupPlayerForm(initial=initial, prefix=f"p{player.id}")))
    return forms_list