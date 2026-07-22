from django import forms
from .models import Referee, RefereeAssignment


class RefereeForm(forms.ModelForm):
    class Meta:
        model = Referee
        fields = [
            "user", "first_name", "last_name", "date_of_birth", "nationality",
            "grade", "license_number", "phone_number", "email", "photo",
            "home_region", "is_active",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_active":
                field.widget.attrs.update({"class": "form-check-input"})
            elif field_name not in self.Meta.widgets:
                field.widget.attrs.update({"class": "form-control"})


class RefereeAssignmentForm(forms.ModelForm):
    class Meta:
        model = RefereeAssignment
        fields = ["referee", "fixture", "role", "confirmed", "fee", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "confirmed":
                field.widget.attrs.update({"class": "form-check-input"})
            elif field_name not in self.Meta.widgets:
                field.widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned_data = super().clean()
        referee = cleaned_data.get("referee")
        fixture = cleaned_data.get("fixture")
        if referee and fixture:
            conflicting = RefereeAssignment.objects.filter(
                referee=referee,
                fixture__kickoff_datetime=fixture.kickoff_datetime,
            ).exclude(pk=self.instance.pk)
            if conflicting.exists():
                raise forms.ValidationError(
                    f"{referee.full_name} is already assigned to another fixture at this kickoff time."
                )
        return cleaned_data