from django.contrib import admin

from .models import Transfer, TransferWindow


@admin.register(TransferWindow)
class TransferWindowAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "window_type", "start_date", "end_date", "is_active", "is_open")
    list_filter = ("season", "window_type", "is_active")
    search_fields = ("name",)

    @admin.display(boolean=True)
    def is_open(self, obj):
        return obj.is_open


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "from_club",
        "to_club",
        "transfer_type",
        "status",
        "window",
        "requested_at",
    )
    list_filter = ("status", "transfer_type", "window")
    search_fields = ("player__first_name", "player__last_name", "from_club__name", "to_club__name")
    readonly_fields = (
        "requested_at",
        "club_response_at",
        "subcounty_response_at",
    )