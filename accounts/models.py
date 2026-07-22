from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Central user model for FCMS.
    Every login (Super Admin, Sub-County Admin, Club Admin, Referee)
    is a CustomUser distinguished by `role`.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        SUBCOUNTY_ADMIN = "SUBCOUNTY_ADMIN", "Sub-County Admin"
        CLUB_ADMIN = "CLUB_ADMIN", "Club Admin"
        REFEREE = "REFEREE", "Referee"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLUB_ADMIN,
        help_text="Determines what this user can see and do in FCMS.",
    )
    phone_number = models.CharField(max_length=20, blank=True)

    # Club Admins are tied to exactly one club. Nullable because other
    # roles (Super Admin, Sub-County Admin, Referee) have no club.
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admins",
        help_text="Only set for Club Admin role.",
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # --- Convenience role checks, used throughout views/templates ---
    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_subcounty_admin(self):
        return self.role == self.Role.SUBCOUNTY_ADMIN

    @property
    def is_club_admin(self):
        return self.role == self.Role.CLUB_ADMIN

    @property
    def is_referee_role(self):
        return self.role == self.Role.REFEREE