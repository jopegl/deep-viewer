from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ExperimentForm, ProjectForm
from .models import Project
from .services import create_experiment, list_experiments


@login_required
def project_list(request):
    projects = Project.objects.filter(created_by=request.user)
    return render(request, "projects/project_list.html", {"projects": projects})


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            return redirect("project_list")
    else:
        form = ProjectForm()
    return render(request, "projects/project_form.html", {"form": form})


@login_required
def experiment_list(request, project_id):
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    experiments = list_experiments(project)
    return render(
        request,
        "projects/experiment_list.html",
        {"project": project, "experiments": experiments},
    )


@login_required
def experiment_create(request, project_id):
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    error = None
    if request.method == "POST":
        form = ExperimentForm(request.POST)
        if form.is_valid():
            try:
                create_experiment(
                    project=project,
                    name=form.cleaned_data["name"],
                    run_at=form.cleaned_data["run_at"],
                    dataset=form.cleaned_data["dataset"],
                    architecture=form.cleaned_data["architecture"],
                    hyperparameters=form.cleaned_data["hyperparameters"],
                    notes=form.cleaned_data["notes"],
                )
                return redirect("experiment_list", project_id=project.id)
            except ValidationError as e:
                error = e.message_dict
    else:
        form = ExperimentForm()
    return render(
        request,
        "projects/experiment_form.html",
        {"form": form, "project": project, "error": error},
    )