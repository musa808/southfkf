from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClubForm
from .models import Club


def _can_manage_clubs(user):
    """Super Admin and Sub-County Admin can create/edit any club."""
    return user.is_authenticated and (user.is_super_admin or user.is_subcounty_admin)


@login_required
def club_list(request):
    """
    Super Admin / Sub-County Admin see every club.
    Club Admin sees only their own club.
    Referee sees the full list (read-only) for context on fixtures.
    """
    user = request.user
    if user.is_super_admin or user.is_subcounty_admin or user.is_referee_role:
        clubs = Club.objects.all()
    elif user.is_club_admin and user.club_id:
        clubs = Club.objects.filter(pk=user.club_id)
    else:
        clubs = Club.objects.none()

    return render(request, "clubs/club_list.html", {"clubs": clubs})


@login_required
def club_detail(request, pk):
    club = get_object_or_404(Club, pk=pk)
    user = request.user

    # Club Admins may only view their own club's detail page.
    if user.is_club_admin:
        if user.club_id is None:
            messages.error(
                request,
                "Your account has no club assigned. "
                "Contact the Sub-County Admin to link your account to a club.",
            )
            return redirect("clubs:list")
        if user.club_id != club.id:
            messages.error(request, "You can only view your own club.")
            return redirect("clubs:list")

    return render(request, "clubs/club_detail.html", {"club": club})


@login_required
@user_passes_test(_can_manage_clubs)
def club_create(request):
    if request.method == "POST":
        form = ClubForm(request.POST, request.FILES)
        if form.is_valid():
            club = form.save()
            messages.success(request, f"{club.name} was registered successfully.")
            return redirect("clubs:detail", pk=club.pk)
    else:
        form = ClubForm()

    return render(request, "clubs/club_form.html", {"form": form, "is_create": True})


@login_required
def club_edit(request, pk):
    club = get_object_or_404(Club, pk=pk)
    user = request.user

    # Sub-County Admin can edit any club; Club Admin can edit only their own.
    allowed = user.is_super_admin or user.is_subcounty_admin or (
        user.is_club_admin and user.club_id == club.id
    )
    if not allowed:
        messages.error(request, "You don't have permission to edit this club.")
        return redirect("clubs:list")

    if request.method == "POST":
        form = ClubForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, f"{club.name} was updated.")
            return redirect("clubs:detail", pk=club.pk)
    else:
        form = ClubForm(instance=club)

    return render(request, "clubs/club_form.html", {"form": form, "is_create": False, "club": club})