from django import forms
from django.utils import timezone

from clubs.models import Club
from players.models import Player

from .models import Transfer, TransferWindow


class TransferInitiateForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ["player", "to_club", "transfer_type", "fee", "loan_end_date"]
        widgets = {
            "loan_end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, initiating_club=None, window=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.initiating_club = initiating_club
        self.window = window

        # A club admin can only send players currently on their own roster.
        if initiating_club is not None:
            self.fields["player"].queryset = Player.objects.filter(
                club=initiating_club, status=Player.Status.ACTIVE
            )
            self.fields["to_club"].queryset = Club.objects.exclude(
                pk=initiating_club.pk
            ).filter(status=Club.Status.ACTIVE)

    def clean(self):
        cleaned = super().clean()
        transfer_type = cleaned.get("transfer_type")
        loan_end_date = cleaned.get("loan_end_date")

        if transfer_type == Transfer.TransferType.LOAN and not loan_end_date:
            self.add_error("loan_end_date", "A loan transfer needs a loan end date.")
        if transfer_type != Transfer.TransferType.LOAN and loan_end_date:
            self.add_error("loan_end_date", "Only loan transfers should have a loan end date.")

        if self.window is not None and not self.window.is_open:
            raise forms.ValidationError(
                "The current transfer window is not open. You cannot initiate a transfer right now."
            )
        return cleaned


class RejectionForm(forms.Form):
    reason = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Reason for rejecting this transfer"}),
        required=True,
    )


class TransferWindowForm(forms.ModelForm):
    class Meta:
        model = TransferWindow
        fields = ["season", "name", "window_type", "start_date", "end_date", "is_active"]
        widgets = {
            "season": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": 'e.g. "2026 Opening Window"'}),
            "window_type": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date cannot be before the start date.")
        return cleaned