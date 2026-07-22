from django import forms
from .models import Coach


class CoachForm(forms.ModelForm):
    class Meta:
        model = Coach
        fields = [
            "user", "club", "first_name", "last_name", "date_of_birth",
            "nationality", "role", "license_level", "phone_number", "email",
            "photo", "date_joined_club", "is_active", "bio",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_joined_club": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "bio": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name in ("is_active",):
                field.widget.attrs.update({"class": "form-check-input"})
            elif field_name not in self.Meta.widgets:
                field.widget.attrs.update({"class": "form-control"})