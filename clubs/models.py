from django.db import models


class Club(models.Model):
    """A registered football club under the Sub-County FA."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Approval"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=150, unique=True)
    logo = models.ImageField(upload_to="club_logos/", blank=True, null=True)
    ward = models.CharField(max_length=100, help_text="Administrative ward the club represents.")
    registration_number = models.CharField(max_length=50, unique=True)
    home_ground = models.CharField(max_length=150, blank=True)
    contact_name = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name