from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from clubs.models import Club

from .forms import PlayerForm
from .models import Player


def _can_manage_club_players(user, club):
    """
    Super Admin / Sub-County Admin can register or edit players for any
    club. Club Admin can only do so for the one club they're assigned to
    (user.club) — never any other club, even via a guessed URL.
    """
    if not user.is_authenticated:
        return False
    if user.is_super_admin or user.is_subcounty_admin:
        return True
    if user.is_club_admin:
        return user.club_id == club.pk
    return False


@login_required
def player_list(request, club_pk):
    club = get_object_or_404(Club, pk=club_pk)
    players = Player.objects.filter(club=club).select_related("club")
    return render(
        request,
        "players/player_list.html",
        {
            "club": club,
            "players": players,
            "can_manage": _can_manage_club_players(request.user, club),
        },
    )


@login_required
def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    return render(
        request,
        "players/player_detail.html",
        {
            "player": player,
            "can_manage": _can_manage_club_players(request.user, player.club),
        },
    )


@login_required
def player_create(request, club_pk):
    club = get_object_or_404(Club, pk=club_pk)

    if not _can_manage_club_players(request.user, club):
        messages.error(request, "You don't have permission to register players for this club.")
        return redirect("players:list", club_pk=club.pk)

    if request.method == "POST":
        form = PlayerForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save(commit=False)
            player.club = club  # always forced from the URL, never from the form
            player.save()
            messages.success(request, f"{player.full_name} registered to {club.name}.")
            return redirect("players:list", club_pk=club.pk)
    else:
        form = PlayerForm()

    return render(
        request,
        "players/player_form.html",
        {"form": form, "club": club, "is_create": True},
    )


@login_required
def player_edit(request, pk):
    player = get_object_or_404(Player, pk=pk)

    if not _can_manage_club_players(request.user, player.club):
        messages.error(request, "You don't have permission to edit players for this club.")
        return redirect("players:detail", pk=player.pk)

    if request.method == "POST":
        form = PlayerForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f"{player.full_name} updated.")
            return redirect("players:detail", pk=player.pk)
    else:
        form = PlayerForm(instance=player)

    return render(
        request,
        "players/player_form.html",
        {"form": form, "club": player.club, "is_create": False, "player": player},
    )