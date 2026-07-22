from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q

from .models import Coach
from .forms import CoachForm

# NOTE: swap LoginRequiredMixin for your project's existing role-based mixin/decorator
# (e.g. the one used in players/clubs apps) if coach management should be admin/club-staff only.


class CoachListView(LoginRequiredMixin, ListView):
    model = Coach
    template_name = "coaches/coach_list.html"
    context_object_name = "coaches"
    paginate_by = 20

    def get_queryset(self):
        qs = Coach.objects.select_related("club").all()
        q = self.request.GET.get("q")
        club_id = self.request.GET.get("club")
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
            )
        if club_id:
            qs = qs.filter(club_id=club_id)
        return qs


class CoachDetailView(LoginRequiredMixin, DetailView):
    model = Coach
    template_name = "coaches/coach_detail.html"
    context_object_name = "coach"


class CoachCreateView(LoginRequiredMixin, CreateView):
    model = Coach
    form_class = CoachForm
    template_name = "coaches/coach_form.html"


class CoachUpdateView(LoginRequiredMixin, UpdateView):
    model = Coach
    form_class = CoachForm
    template_name = "coaches/coach_form.html"


class CoachDeleteView(LoginRequiredMixin, DeleteView):
    model = Coach
    template_name = "coaches/coach_confirm_delete.html"
    success_url = reverse_lazy("coaches:coach-list")