from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from ..forms.experiment_forms import ExperimentForm
from ..forms.filter_forms import ExperimentFilterForm
from ..models import Experiment, Project


class ExperimentListView(LoginRequiredMixin, ListView):
    model = Experiment
    template_name = "experiments/experimentsList.html"
    context_object_name = "experiment_list"

    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"], analyst=self.request.user)
        self.filter_form = ExperimentFilterForm(self.request.GET)
        return self.filter_form.filter(self.project.experiments.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["filter_form"] = self.filter_form
        context["total_count"] = self.project.experiments.count()
        return context


class ExperimentCreateView(LoginRequiredMixin, CreateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = "experiments/experimentCreate.html"

    def get_success_url(self):
        return reverse("experiment_list", kwargs={"pk": self.object.project.pk})

    def get_project(self):
        if not hasattr(self, "_project"):
            self._project = get_object_or_404(
                Project, pk=self.kwargs["pk"], analyst=self.request.user
            )
        return self._project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        form.instance.project = self.get_project()
        return super().form_valid(form)


class ExperimentUpdateView(LoginRequiredMixin, UpdateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = "experiments/experimentUpdate.html"

    def get_queryset(self):
        return Experiment.objects.filter(project__analyst=self.request.user)

    def get_success_url(self):
        return reverse("experiment_list", kwargs={"pk": self.object.project_id})


class ExperimentDeleteView(LoginRequiredMixin, DeleteView):
    model = Experiment
    template_name = "experiments/experimentConfirmDelete.html"

    def get_queryset(self):
        return Experiment.objects.filter(project__analyst=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Experimento "{self.object.name}" excluído.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("experiment_list", kwargs={"pk": self.object.project_id})