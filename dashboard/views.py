from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from clubs.models import Club
from competitions.models import Competition
from fixtures.models import Fixture
from results.models import GoalEvent
from seasons.models import Season
from standings.models import StandingsRow


@login_required
def home(request):
    user = request.user
    active_season = Season.objects.filter(is_active=True).first()
    today = timezone.localdate()

    # --- Clubs summary ---
    total_clubs = Club.objects.count()
    active_clubs = Club.objects.filter(status=Club.Status.ACTIVE).count()
    pending_clubs = Club.objects.filter(status=Club.Status.PENDING).count()

    # --- Active season competitions ---
    ongoing_competitions = (
        Competition.objects.filter(season=active_season, status=Competition.Status.ONGOING)
        .select_related("season")
        if active_season else Competition.objects.none()
    )

    # --- Upcoming fixtures (next 7 days across all ongoing competitions) ---
    upcoming_fixtures = (
        Fixture.objects.filter(
            competition__status=Competition.Status.ONGOING,
            status=Fixture.Status.SCHEDULED,
            match_date__gte=today,
            match_date__lte=today + timezone.timedelta(days=7),
        )
        .select_related("home_team__club", "away_team__club", "competition")
        .order_by("match_date", "kickoff_time")[:8]
    )

    # --- Recent results (last 5 played fixtures) ---
    recent_results = (
        Fixture.objects.filter(
            competition__status=Competition.Status.ONGOING,
            status=Fixture.Status.PLAYED,
        )
        .select_related(
            "home_team__club", "away_team__club",
            "result", "competition",
        )
        .order_by("-match_date", "-id")[:5]
    )

    # --- Top scorers across all ongoing competitions in active season ---
    top_scorers = []
    if active_season:
        top_scorers = (
            GoalEvent.objects.filter(
                result__fixture__competition__season=active_season,
                result__fixture__competition__status=Competition.Status.ONGOING,
                is_own_goal=False,
                scorer__isnull=False,
            )
            .values(
                "scorer__id",
                "scorer__first_name",
                "scorer__last_name",
                "scorer__club__name",
            )
            .annotate(goals=Count("id"))
            .order_by("-goals")[:5]
        )

    # --- Pending club approvals (admin roles only) ---
    pending_approvals = []
    if user.is_super_admin or user.is_subcounty_admin:
        pending_approvals = Club.objects.filter(status=Club.Status.PENDING).order_by("created_at")

    context = {
        "active_season": active_season,
        "ongoing_competitions": ongoing_competitions,
        "total_clubs": total_clubs,
        "active_clubs": active_clubs,
        "pending_clubs": pending_clubs,
        "upcoming_fixtures": upcoming_fixtures,
        "recent_results": recent_results,
        "top_scorers": top_scorers,
        "pending_approvals": pending_approvals,
        "today": today,
    }
    return render(request, "dashboard/home.html", context)