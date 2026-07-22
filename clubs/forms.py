from django import forms

from .models import Club


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = [
            "name",
            "logo",
            "ward",
            "registration_number",
            "home_ground",
            "contact_name",
            "contact_phone",
            "contact_email",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Garbatulla United FC"}),
            "ward": forms.TextInput(attrs={"placeholder": "e.g. Garbatulla Ward"}),
            "registration_number": forms.TextInput(attrs={"placeholder": "e.g. GBT-FC-001"}),
        }