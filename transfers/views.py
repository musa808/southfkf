from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from clubs.models import Club
from players.models import Player

from .forms import RejectionForm, TransferInitiateForm, TransferWindowForm
from .models import Transfer, TransferWindow
from .permissions import club_admin_required, subcounty_admin_required


@login_required
def dashboard(request):
    """
    Role-aware transfer dashboard:
      - Club Admin: transfers in/out of their club, with pending actions surfaced first.
      - Sub-County / Super Admin: everything, with items awaiting their approval surfaced first.
    """
    user = request.user
    pending_your_action = Transfer.objects.none()

    if user.is_club_admin and user.club_id:
        transfers = Transfer.objects.filter(
            Q(from_club=user.club) | Q(to_club=user.club)
        ).select_related("player", "from_club", "to_club", "window")
        pending_your_action = transfers.filter(
            to_club=user.club, status=Transfer.Status.PENDING_CLUB
        )
    elif user.is_subcounty_admin or user.is_super_admin:
        transfers = Transfer.objects.all().select_related(
            "player", "from_club", "to_club", "window"
        )
        pending_your_action = transfers.filter(status=Transfer.Status.PENDING_SUBCOUNTY)
    else:
        transfers = Transfer.objects.none()

    active_windows = TransferWindow.objects.filter(is_active=True)

    return render(
        request,
        "transfers/dashboard.html",
        {
            "transfers": transfers[:50],
            "pending_your_action": pending_your_action,
            "active_windows": [w for w in active_windows if w.is_open],
        },
    )


@club_admin_required
def initiate_transfer(request):
    user = request.user
    open_window = next(
        (w for w in TransferWindow.objects.filter(is_active=True) if w.is_open), None
    )

    if request.method == "POST":
        form = TransferInitiateForm(
            request.POST, initiating_club=user.club, window=open_window
        )
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.from_club = user.club
            transfer.window = open_window
            transfer.initiated_by = user
            transfer.status = Transfer.Status.PENDING_CLUB
            try:
                transfer.full_clean()
            except ValidationError as exc:
                for err in exc.messages:
                    messages.error(request, err)
            else:
                transfer.save()
                messages.success(
                    request,
                    f"Transfer request for {transfer.player.full_name} sent to {transfer.to_club.name}.",
                )
                return redirect("transfers:detail", pk=transfer.pk)
    else:
        form = TransferInitiateForm(initiating_club=user.club, window=open_window)

    return render(
        request,
        "transfers/transfer_initiate.html",
        {"form": form, "open_window": open_window},
    )


@login_required
def transfer_detail(request, pk):
    transfer = get_object_or_404(
        Transfer.objects.select_related("player", "from_club", "to_club", "window", "initiated_by"),
        pk=pk,
    )
    user = request.user

    can_respond_as_receiving_club = (
        user.is_club_admin
        and user.club_id == transfer.to_club_id
        and transfer.status == Transfer.Status.PENDING_CLUB
    )
    can_cancel = (
        user.is_club_admin
        and user.club_id == transfer.from_club_id
        and transfer.status == Transfer.Status.PENDING_CLUB
    )
    can_approve_as_subcounty = (
        user.is_subcounty_admin or user.is_super_admin
    ) and transfer.status == Transfer.Status.PENDING_SUBCOUNTY

    return render(
        request,
        "transfers/transfer_detail.html",
        {
            "transfer": transfer,
            "timeline": transfer.timeline(),
            "can_respond_as_receiving_club": can_respond_as_receiving_club,
            "can_cancel": can_cancel,
            "can_approve_as_subcounty": can_approve_as_subcounty,
        },
    )


@club_admin_required
def respond_accept(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk, to_club=request.user.club)
    if request.method == "POST":
        try:
            transfer.accept_by_club(request.user)
            messages.success(request, "Transfer accepted and sent to the Sub-County Admin for approval.")
        except ValidationError as exc:
            messages.error(request, str(exc.message if hasattr(exc, "message") else exc))
    return redirect("transfers:detail", pk=transfer.pk)


@club_admin_required
def respond_reject(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk, to_club=request.user.club)
    if request.method == "POST":
        form = RejectionForm(request.POST)
        if form.is_valid():
            try:
                transfer.reject_by_club(request.user, reason=form.cleaned_data["reason"])
                messages.success(request, "Transfer rejected.")
                return redirect("transfers:detail", pk=transfer.pk)
            except ValidationError as exc:
                messages.error(request, str(exc))
    else:
        form = RejectionForm()
    return render(request, "transfers/reject_form.html", {"transfer": transfer, "form": form, "stage": "club"})


@club_admin_required
def cancel_transfer(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk, from_club=request.user.club)
    if request.method == "POST":
        try:
            transfer.cancel(request.user)
            messages.success(request, "Transfer request cancelled.")
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect("transfers:detail", pk=transfer.pk)


@subcounty_admin_required
def subcounty_approve(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    if request.method == "POST":
        try:
            transfer.approve_by_subcounty(request.user)
            messages.success(
                request,
                f"Transfer approved — {transfer.player.full_name} now plays for {transfer.to_club.name}.",
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect("transfers:detail", pk=transfer.pk)


@subcounty_admin_required
def subcounty_reject(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    if request.method == "POST":
        form = RejectionForm(request.POST)
        if form.is_valid():
            try:
                transfer.reject_by_subcounty(request.user, reason=form.cleaned_data["reason"])
                messages.success(request, "Transfer rejected.")
                return redirect("transfers:detail", pk=transfer.pk)
            except ValidationError as exc:
                messages.error(request, str(exc))
    else:
        form = RejectionForm()
    return render(request, "transfers/reject_form.html", {"transfer": transfer, "form": form, "stage": "subcounty"})


@login_required
def transfer_certificate(request, pk):
    transfer = get_object_or_404(
        Transfer.objects.select_related("player", "from_club", "to_club", "window__season"),
        pk=pk,
    )
    if transfer.status != Transfer.Status.APPROVED:
        messages.error(request, "A certificate is only available once a transfer is fully approved.")
        return redirect("transfers:detail", pk=transfer.pk)

    return render(
        request,
        "transfers/transfer_certificate.html",
        {
            "transfer": transfer,
            "federation_name": "Football Kenya Federation",
            "subcounty_name": "Sub-County Football Association",
            "chairman_name": "Abdihamid Adan",
            "chairman_title": "Sub-County Chairman, FKF",
        },
    )


@login_required
def player_history(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    transfers = Transfer.objects.filter(player=player).select_related("from_club", "to_club", "window")
    return render(request, "transfers/player_history.html", {"player": player, "transfers": transfers})


@login_required
def club_history(request, club_id):
    club = get_object_or_404(Club, pk=club_id)
    transfers = Transfer.objects.filter(Q(from_club=club) | Q(to_club=club)).select_related(
        "player", "from_club", "to_club", "window"
    )
    return render(request, "transfers/club_history.html", {"club": club, "transfers": transfers})


@subcounty_admin_required
def window_list(request):
    windows = TransferWindow.objects.select_related("season")
    return render(request, "transfers/window_list.html", {"windows": windows})


@subcounty_admin_required
def window_create(request):
    if request.method == "POST":
        form = TransferWindowForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Transfer window created.")
            return redirect("transfers:window_list")
    else:
        form = TransferWindowForm()
    return render(request, "transfers/window_form.html", {"form": form, "editing": False})


@subcounty_admin_required
def window_edit(request, pk):
    window = get_object_or_404(TransferWindow, pk=pk)
    if request.method == "POST":
        form = TransferWindowForm(request.POST, instance=window)
        if form.is_valid():
            form.save()
            messages.success(request, "Transfer window updated.")
            return redirect("transfers:window_list")
    else:
        form = TransferWindowForm(instance=window)
    return render(request, "transfers/window_form.html", {"form": form, "editing": True, "window": window})