from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q

from .models import Referee, RefereeAssignment
from .forms import RefereeForm, RefereeAssignmentForm

# NOTE: swap LoginRequiredMixin for your project's existing role-based mixin/decorator
# if referee management should be restricted to admins/match officials staff.


class RefereeListView(LoginRequiredMixin, ListView):
    model = Referee
    template_name = "referees/referee_list.html"
    context_object_name = "referees"
    paginate_by = 20

    def get_queryset(self):
        qs = Referee.objects.all()
        q = self.request.GET.get("q")
        grade = self.request.GET.get("grade")
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
            )
        if grade:
            qs = qs.filter(grade=grade)
        return qs


class RefereeDetailView(LoginRequiredMixin, DetailView):
    model = Referee
    template_name = "referees/referee_detail.html"
    context_object_name = "referee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assignments"] = self.object.assignments.select_related("fixture").order_by(
            "-fixture__kickoff_datetime"
        )
        return context


class RefereeCreateView(LoginRequiredMixin, CreateView):
    model = Referee
    form_class = RefereeForm
    template_name = "referees/referee_form.html"


class RefereeUpdateView(LoginRequiredMixin, UpdateView):
    model = Referee
    form_class = RefereeForm
    template_name = "referees/referee_form.html"


class RefereeDeleteView(LoginRequiredMixin, DeleteView):
    model = Referee
    template_name = "referees/referee_confirm_delete.html"
    success_url = reverse_lazy("referees:referee-list")


# --- Match assignment views ---

class AssignmentListView(LoginRequiredMixin, ListView):
    model = RefereeAssignment
    template_name = "referees/assignment_list.html"
    context_object_name = "assignments"
    paginate_by = 30

    def get_queryset(self):
        return RefereeAssignment.objects.select_related("referee", "fixture").order_by(
            "-fixture__kickoff_datetime"
        )


class AssignmentCreateView(LoginRequiredMixin, CreateView):
    model = RefereeAssignment
    form_class = RefereeAssignmentForm
    template_name = "referees/assignment_form.html"
    success_url = reverse_lazy("referees:assignment-list")


class AssignmentUpdateView(LoginRequiredMixin, UpdateView):
    model = RefereeAssignment
    form_class = RefereeAssignmentForm
    template_name = "referees/assignment_form.html"
    success_url = reverse_lazy("referees:assignment-list")


class AssignmentDeleteView(LoginRequiredMixin, DeleteView):
    model = RefereeAssignment
    template_name = "referees/assignment_confirm_delete.html"
    success_url = reverse_lazy("referees:assignment-list")