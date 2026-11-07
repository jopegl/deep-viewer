from django.shortcuts import render
from django.http import HttpRequest
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..forms.project_forms import *

# Create your views here.

class ProjectListView(ListView):
    model = Project
    template_name = "projects/projectsHome.html"
    context_object_name = "projects"

    def get_queryset(self):
      return Project.objects.filter(analyst=self.request.user)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name =  'projects/projectsCreate.html'
    success_url = reverse_lazy("project_list")

    def form_valid(self, form):
        form.instance.analyst = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
  model = Project
  form_class = ProjectForm
  template_name = "projects/projectUpdate.html"
  success_url = reverse_lazy("project_list")


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
  model = Project
  template_name = "projects/projectConfirmDelete.html"
  success_url = reverse_lazy("project_list")