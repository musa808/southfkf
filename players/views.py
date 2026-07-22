from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from clubs.models import Club

from .models import Player


@login_required
def player_list(request, club_pk):
    club = get_object_or_404(Club, pk=club_pk)
    players = Player.objects.filter(club=club).select_related("club")
    return render(request, "players/player_list.html", {"club": club, "players": players})


@login_required
def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    return render(request, "players/player_detail.html", {"player": player})