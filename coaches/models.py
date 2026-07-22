from django.db import models
from django.conf import settings
from django.urls import reverse


class CoachRole(models.TextChoices):
    HEAD_COACH = "HEAD", "Head Coach"
    ASSISTANT_COACH = "ASSISTANT", "Assistant Coach"
    GOALKEEPING_COACH = "GK", "Goalkeeping Coach"
    FITNESS_COACH = "FITNESS", "Fitness Coach"
    YOUTH_COACH = "YOUTH", "Youth Coach"


class LicenseLevel(models.TextChoices):
    CAF_A = "CAF_A", "CAF A License"
    CAF_B = "CAF_B", "CAF B License"
    CAF_C = "CAF_C", "CAF C License"
    CAF_PRO = "CAF_PRO", "CAF Pro License"
    NONE = "NONE", "No License"


class Coach(models.Model):
    # Optional link to a login account, if coaches get portal access
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_profile",
        null=True,
        blank=True,
    )
    # ASSUMPTION: clubs app has a model called Club. Adjust if different.
    club = models.ForeignKey(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coaches",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=CoachRole.choices, default=CoachRole.HEAD_COACH)
    license_level = models.CharField(max_length=20, choices=LicenseLevel.choices, default=LicenseLevel.NONE)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to="coaches/photos/", null=True, blank=True)
    date_joined_club = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("coaches:coach-detail", kwargs={"pk": self.pk})