from django import forms

from .models import Season


class SeasonForm(forms.ModelForm):
    class Meta:
        model = Season
        fields = ["name", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }