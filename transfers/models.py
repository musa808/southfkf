from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TransferWindow(models.Model):
    """
    A period during which transfers may be initiated for a given Season.
    The Sub-County Admin opens/closes these; club admins can only initiate
    transfers while a window is open.
    """

    class WindowType(models.TextChoices):
        OPENING = "OPENING", "Opening Window"
        MID_SEASON = "MID_SEASON", "Mid-Season Window"
        EMERGENCY = "EMERGENCY", "Emergency Window"

    season = models.ForeignKey(
        "seasons.Season", on_delete=models.CASCADE, related_name="transfer_windows"
    )
    name = models.CharField(max_length=100, help_text='e.g. "2026 Opening Window"')
    window_type = models.CharField(
        max_length=20, choices=WindowType.choices, default=WindowType.OPENING
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to force-close a window early, regardless of its dates.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.season.name})"

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

    @property
    def is_open(self):
        today = timezone.localdate()
        return self.is_active and self.start_date <= today <= self.end_date

    @property
    def status_label(self):
        if not self.is_active:
            return "Closed (manually)"
        today = timezone.localdate()
        if today < self.start_date:
            return "Upcoming"
        if today > self.end_date:
            return "Closed"
        return "Open"


class Transfer(models.Model):
    """
    A single player transfer moving through the 3-stage approval workflow:

        1. Player's (sending) Club Admin initiates          -> PENDING_CLUB
        2. Receiving Club Admin accepts / rejects            -> PENDING_SUBCOUNTY / REJECTED_CLUB
        3. Sub-County Admin approves / rejects                -> APPROVED / REJECTED_SUBCOUNTY

    Only on Sub-County approval does the player's club actually change.
    """

    class TransferType(models.TextChoices):
        PERMANENT = "PERMANENT", "Permanent Transfer"
        LOAN = "LOAN", "Loan"
        FREE_AGENT = "FREE_AGENT", "Free Agent Signing"

    class Status(models.TextChoices):
        PENDING_CLUB = "PENDING_CLUB", "Awaiting Receiving Club"
        PENDING_SUBCOUNTY = "PENDING_SUBCOUNTY", "Awaiting Sub-County Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED_CLUB = "REJECTED_CLUB", "Rejected by Receiving Club"
        REJECTED_SUBCOUNTY = "REJECTED_SUBCOUNTY", "Rejected by Sub-County Admin"
        CANCELLED = "CANCELLED", "Cancelled by Initiator"

    window = models.ForeignKey(
        TransferWindow, on_delete=models.PROTECT, related_name="transfers"
    )
    player = models.ForeignKey(
        "players.Player", on_delete=models.CASCADE, related_name="transfers"
    )
    from_club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_out",
        help_text="Left blank for a free-agent signing.",
    )
    to_club = models.ForeignKey(
        "clubs.Club", on_delete=models.CASCADE, related_name="transfers_in"
    )
    transfer_type = models.CharField(
        max_length=20, choices=TransferType.choices, default=TransferType.PERMANENT
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Transfer/loan fee in KES. Leave blank if undisclosed or free.",
    )
    loan_end_date = models.DateField(
        null=True, blank=True, help_text="Only relevant for loan transfers."
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING_CLUB
    )

    initiated_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="transfers_initiated",
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    club_response_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfer_club_responses",
    )
    club_response_at = models.DateTimeField(null=True, blank=True)
    club_rejection_reason = models.CharField(max_length=255, blank=True)

    subcounty_response_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfer_subcounty_responses",
    )
    subcounty_response_at = models.DateTimeField(null=True, blank=True)
    subcounty_rejection_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        origin = self.from_club.name if self.from_club else "Free Agent"
        return f"{self.player.full_name}: {origin} \u2192 {self.to_club.name} ({self.get_status_display()})"

    def clean(self):
        if self.to_club_id and self.from_club_id and self.to_club_id == self.from_club_id:
            raise ValidationError("A player cannot be transferred to the same club.")
        if self.transfer_type == self.TransferType.FREE_AGENT and self.from_club_id:
            raise ValidationError("Free agent signings should not have a sending club.")

    # ------------------------------------------------------------------
    # Workflow transitions. Each raises ValidationError on an illegal
    # transition so views can catch it and show a friendly message.
    # ------------------------------------------------------------------

    def accept_by_club(self, user):
        if self.status != self.Status.PENDING_CLUB:
            raise ValidationError("This transfer is not awaiting a club decision.")
        self.status = self.Status.PENDING_SUBCOUNTY
        self.club_response_by = user
        self.club_response_at = timezone.now()
        self.save()

    def reject_by_club(self, user, reason=""):
        if self.status != self.Status.PENDING_CLUB:
            raise ValidationError("This transfer is not awaiting a club decision.")
        self.status = self.Status.REJECTED_CLUB
        self.club_response_by = user
        self.club_response_at = timezone.now()
        self.club_rejection_reason = reason
        self.save()

    def approve_by_subcounty(self, user):
        if self.status != self.Status.PENDING_SUBCOUNTY:
            raise ValidationError("This transfer is not awaiting Sub-County approval.")
        self.status = self.Status.APPROVED
        self.subcounty_response_by = user
        self.subcounty_response_at = timezone.now()
        self.save()

        # The player only actually moves once the Sub-County Admin signs off.
        if self.transfer_type != self.TransferType.LOAN:
            self.player.club = self.to_club
            self.player.save(update_fields=["club"])
        else:
            # For loans, move the player for the duration of the loan too;
            # returning them is a separate transfer initiated at loan_end_date.
            self.player.club = self.to_club
            self.player.save(update_fields=["club"])

    def reject_by_subcounty(self, user, reason=""):
        if self.status != self.Status.PENDING_SUBCOUNTY:
            raise ValidationError("This transfer is not awaiting Sub-County approval.")
        self.status = self.Status.REJECTED_SUBCOUNTY
        self.subcounty_response_by = user
        self.subcounty_response_at = timezone.now()
        self.subcounty_rejection_reason = reason
        self.save()

    def cancel(self, user):
        if self.status != self.Status.PENDING_CLUB:
            raise ValidationError("Only transfers still awaiting the receiving club can be cancelled.")
        self.status = self.Status.CANCELLED
        self.save()

    @property
    def is_final(self):
        return self.status in {
            self.Status.APPROVED,
            self.Status.REJECTED_CLUB,
            self.Status.REJECTED_SUBCOUNTY,
            self.Status.CANCELLED,
        }

    def timeline(self):
        """
        Ordered list of steps for the status-timeline UI on the transfer card.
        Each step: label, state ("done" / "rejected" / "pending" / "upcoming"), timestamp, actor.
        """
        steps = [
            {
                "label": "Initiated",
                "state": "done",
                "timestamp": self.requested_at,
                "actor": self.initiated_by,
                "detail": f"By {self.from_club.name if self.from_club else 'free agent signing'}",
            }
        ]

        if self.status == self.Status.CANCELLED:
            steps.append({"label": "Cancelled", "state": "rejected", "timestamp": None, "actor": None, "detail": ""})
            return steps

        if self.status == self.Status.REJECTED_CLUB:
            steps.append(
                {
                    "label": "Rejected by receiving club",
                    "state": "rejected",
                    "timestamp": self.club_response_at,
                    "actor": self.club_response_by,
                    "detail": self.club_rejection_reason,
                }
            )
            return steps

        club_state = "done" if self.club_response_at else "pending"
        steps.append(
            {
                "label": "Accepted by receiving club",
                "state": club_state,
                "timestamp": self.club_response_at,
                "actor": self.club_response_by,
                "detail": "",
            }
        )

        if self.status == self.Status.REJECTED_SUBCOUNTY:
            steps.append(
                {
                    "label": "Rejected by Sub-County Admin",
                    "state": "rejected",
                    "timestamp": self.subcounty_response_at,
                    "actor": self.subcounty_response_by,
                    "detail": self.subcounty_rejection_reason,
                }
            )
            return steps

        subcounty_state = "done" if self.status == self.Status.APPROVED else "upcoming" if club_state == "pending" else "pending"
        steps.append(
            {
                "label": "Approved by Sub-County Admin",
                "state": subcounty_state,
                "timestamp": self.subcounty_response_at,
                "actor": self.subcounty_response_by,
                "detail": "",
            }
        )
        return steps