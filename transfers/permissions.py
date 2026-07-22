from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def club_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_club_admin and request.user.club_id):
            messages.error(request, "You must be a Club Admin assigned to a club to do that.")
            return redirect("transfers:dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def subcounty_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_subcounty_admin or request.user.is_super_admin):
            messages.error(request, "Only the Sub-County Admin can do that.")
            return redirect("transfers:dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped