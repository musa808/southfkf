from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SeasonForm
from .models import Season


def _can_manage(user):
    """Only Super Admin / Sub-County Admin manage seasons."""
    return user.is_authenticated and (user.is_super_admin or user.is_subcounty_admin)


@login_required
def season_list(request):
    seasons = Season.objects.all()
    return render(request, "seasons/season_list.html", {"seasons": seasons})


@login_required
def season_detail(request, pk):
    season = get_object_or_404(Season, pk=pk)
    competitions = season.competitions.all()
    return render(request, "seasons/season_detail.html", {"season": season, "competitions": competitions})


@login_required
@user_passes_test(_can_manage)
def season_create(request):
    if request.method == "POST":
        form = SeasonForm(request.POST)
        if form.is_valid():
            season = form.save()
            messages.success(request, f"{season.name} created.")
            return redirect("seasons:detail", pk=season.pk)
    else:
        form = SeasonForm()
    return render(request, "seasons/season_form.html", {"form": form, "is_create": True})


@login_required
@user_passes_test(_can_manage)
def season_edit(request, pk):
    season = get_object_or_404(Season, pk=pk)
    if request.method == "POST":
        form = SeasonForm(request.POST, instance=season)
        if form.is_valid():
            form.save()
            messages.success(request, f"{season.name} updated.")
            return redirect("seasons:detail", pk=season.pk)
    else:
        form = SeasonForm(instance=season)
    return render(request, "seasons/season_form.html", {"form": form, "is_create": False, "season": season})