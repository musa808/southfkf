from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from competitions.models import Competition
from fixtures.models import Fixture

from .forms import GoalEventForm, GoalEventFormSet, MatchResultForm
from .models import GoalEvent, MatchResult


def _can_manage(user):
    return user.is_authenticated and (user.is_super_admin or user.is_subcounty_admin)


@login_required
def result_list(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)
    results = (
        MatchResult.objects.filter(fixture__competition=competition)
        .select_related(
            "fixture__home_team__club",
            "fixture__away_team__club",
            "fixture__group",
            "fixture__knockout_fixture__round",
        )
        .prefetch_related("goals__scorer")
        .order_by("fixture__match_date")
    )
    return render(request, "results/result_list.html", {"competition": competition, "results": results})


@login_required
@user_passes_test(_can_manage)
def enter_result(request, fixture_pk):
    fixture = get_object_or_404(
        Fixture.objects.select_related(
            "competition", "home_team__club", "away_team__club"
        ),
        pk=fixture_pk,
    )

    if hasattr(fixture, "result"):
        return redirect("results:edit", fixture_pk=fixture.pk)

    if request.method == "POST":
        form = MatchResultForm(request.POST)
        formset = GoalEventFormSet(request.POST, form_kwargs={"fixture": fixture})
        if form.is_valid() and formset.is_valid():
            # Mark fixture as played BEFORE saving the result. The
            # MatchResult post_save signal triggers standings
            # recalculation immediately, and that recalculation only
            # counts fixtures with status=PLAYED — so this must happen
            # first, or the just-entered result gets silently excluded.
            fixture.status = Fixture.Status.PLAYED
            fixture.save(update_fields=["status"])

            result = form.save(commit=False)
            result.fixture = fixture
            result.full_clean()
            result.save()
            formset.instance = result
            formset.save()
            messages.success(request, "Result recorded.")
            return redirect("results:list", competition_pk=fixture.competition_id)
    else:
        form = MatchResultForm()
        formset = GoalEventFormSet(form_kwargs={"fixture": fixture})

    return render(
        request,
        "results/enter_result.html",
        {"form": form, "formset": formset, "fixture": fixture},
    )


@login_required
@user_passes_test(_can_manage)
def edit_result(request, fixture_pk):
    fixture = get_object_or_404(
        Fixture.objects.select_related(
            "competition", "home_team__club", "away_team__club"
        ),
        pk=fixture_pk,
    )
    result = get_object_or_404(MatchResult, fixture=fixture)

    if request.method == "POST":
        form = MatchResultForm(request.POST, instance=result)
        formset = GoalEventFormSet(request.POST, instance=result, form_kwargs={"fixture": fixture})
        if form.is_valid() and formset.is_valid():
            result = form.save()
            formset.save()
            messages.success(request, "Result updated.")
            return redirect("results:list", competition_pk=fixture.competition_id)
    else:
        form = MatchResultForm(instance=result)
        formset = GoalEventFormSet(instance=result, form_kwargs={"fixture": fixture})

    return render(
        request,
        "results/enter_result.html",
        {"form": form, "formset": formset, "fixture": fixture, "result": result},
    )