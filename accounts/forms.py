from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser


class FCMSLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )


class ClubAdminCreationForm(UserCreationForm):
    """
    Used by Super Admin / Sub-County Admin to create a Club Admin
    account and tie it to a club in one step.
    """

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "phone_number", "club")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.CLUB_ADMIN
        if commit:
            user.save()
        return user