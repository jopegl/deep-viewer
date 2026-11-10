from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from ..forms.filter_forms import ProjectFilterForm
from ..forms.project_forms import ProjectForm
from ..models import Project


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/projectsHome.html"
    context_object_name = "projects"

    def get_queryset(self):
        self.all_projects = Project.objects.filter(analyst=self.request.user)
        self.filter_form = ProjectFilterForm(self.request.GET)
        queryset = self.all_projects.annotate(n_experiments=Count("experiments"))
        return self.filter_form.filter(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["total_count"] = self.all_projects.count()
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/projectsCreate.html"
    success_url = reverse_lazy("project_list")

    def form_valid(self, form):
        form.instance.analyst = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/projectUpdate.html"
    success_url = reverse_lazy("project_list")

    def get_queryset(self):
        return Project.objects.filter(analyst=self.request.user)


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = "projects/projectConfirmDelete.html"
    success_url = reverse_lazy("project_list")

    def get_queryset(self):
        return Project.objects.filter(analyst=self.request.user)
