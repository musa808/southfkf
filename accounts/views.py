from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from .forms import ClubAdminCreationForm


def _is_admin_role(user):
    """Only Super Admin / Sub-County Admin may create Club Admin accounts."""
    return user.is_authenticated and (user.is_super_admin or user.is_subcounty_admin)


@login_required
@user_passes_test(_is_admin_role)
def create_club_admin(request):
    if request.method == "POST":
        form = ClubAdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Club Admin account created for {user.username}.")
            return redirect("clubs:list")
    else:
        form = ClubAdminCreationForm()

    return render(request, "accounts/create_club_admin.html", {"form": form})