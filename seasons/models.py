from django.db import models


class Season(models.Model):
    """
    A football season/year, e.g. "2026 Season".
    One Season can hold many Competitions (League, Cup, Friendly series, etc).
    """

    name = models.CharField(max_length=100, unique=True, help_text='e.g. "2026 Season"')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(
        default=False,
        help_text="Only one season should be active at a time. Used as the default for new fixtures/dashboards.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Enforce a single active season — mirrors how the Sub-County Admin
        # actually works (one season "live" at a time).
        if self.is_active:
            Season.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)