from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..forms.experiment_forms import *

class ExperimentListView(ListView):
    model = Experiment
    template_name = "experiments/experimentsList.html"
    context_object_name = "experiment_list"

    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return Experiment.objects.filter(project=self.project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

class ExperimentCreateView(LoginRequiredMixin, CreateView):
    model = Experiment
    form_class = ExperimentForm
    template_name =  'experiments/experimentCreate.html'
    success_url = reverse_lazy("experiment_list")

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
  success_url = reverse_lazy("experiment_list")


class ExperimentDeleteView(LoginRequiredMixin, DeleteView):
  model = Experiment
  template_name = "experiments/experimentConfirmDelete.html"
  success_url = reverse_lazy("experiment_list")