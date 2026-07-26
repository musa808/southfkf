from django import forms

from .models import Player


class PlayerForm(forms.ModelForm):
    """
    Deliberately has no `club` field. The club is always assigned by the
    view (from the URL's club_pk), never chosen here — this is what makes
    it impossible for a Club Admin to register a player under a club that
    isn't theirs, regardless of what they submit.
    """

    class Meta:
        model = Player
        fields = ["first_name", "last_name", "date_of_birth", "position", "jersey_number", "status", "photo"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }