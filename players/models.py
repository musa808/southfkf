from django.db import models

from clubs.models import Club


class Player(models.Model):

    class Position(models.TextChoices):
        GOALKEEPER = "GK", "Goalkeeper"
        DEFENDER = "DEF", "Defender"
        MIDFIELDER = "MID", "Midfielder"
        FORWARD = "FWD", "Forward"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        INJURED = "INJURED", "Injured"
        INACTIVE = "INACTIVE", "Inactive"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="players")
    date_of_birth = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=5, choices=Position.choices, blank=True)
    jersey_number = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    photo = models.ImageField(upload_to="player_photos/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["club", "last_name", "first_name"]
        unique_together = ("club", "jersey_number")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.club.name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"