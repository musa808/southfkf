from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse


class RefereeGrade(models.TextChoices):
    INTERNATIONAL = "INTL", "International"
    NATIONAL = "NATIONAL", "National"
    REGIONAL = "REGIONAL", "Regional"
    COUNTY = "COUNTY", "County"
    ASPIRING = "ASPIRING", "Aspiring"


class MatchRole(models.TextChoices):
    CENTER = "CENTER", "Center Referee"
    ASSISTANT_1 = "AR1", "Assistant Referee 1"
    ASSISTANT_2 = "AR2", "Assistant Referee 2"
    FOURTH = "FOURTH", "Fourth Official"
    VAR = "VAR", "VAR Official"


class Referee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referee_profile",
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=20, choices=RefereeGrade.choices, default=RefereeGrade.ASPIRING)
    license_number = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to="referees/photos/", null=True, blank=True)
    home_region = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_grade_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("referees:referee-detail", kwargs={"pk": self.pk})


class RefereeAssignment(models.Model):
    referee = models.ForeignKey(Referee, on_delete=models.CASCADE, related_name="assignments")
    # ASSUMPTION: fixtures app has a model called Fixture with a "kickoff_datetime" field.
    # Adjust field name below (and in clean()) if yours differs, e.g. "match_date" or "date_time".
    fixture = models.ForeignKey(
        "fixtures.Fixture",
        on_delete=models.CASCADE,
        related_name="referee_assignments",
    )
    role = models.CharField(max_length=10, choices=MatchRole.choices, default=MatchRole.CENTER)
    confirmed = models.BooleanField(default=False)
    fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["fixture", "role"],
                name="unique_role_per_fixture",
            ),
        ]

    def __str__(self):
        return f"{self.referee.full_name} - {self.get_role_display()} - Fixture #{self.fixture_id}"

    def clean(self):
        if not self.referee_id or not self.fixture_id:
            return
        # Prevent the same referee being double-booked at the same kickoff time
        conflicting = RefereeAssignment.objects.filter(
            referee=self.referee,
            fixture__kickoff_datetime=self.fixture.kickoff_datetime,
        ).exclude(pk=self.pk)
        if conflicting.exists():
            raise ValidationError(
                f"{self.referee.full_name} is already assigned to another fixture at this kickoff time."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)