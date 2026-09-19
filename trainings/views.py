from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Experiment, Project

from .forms import LogFileForm, MeasurementTypeForm, SampleMeasurementFileForm
from .models import LogFile, MeasurementType, SampleMeasurementFile
from .services import (
    create_log_file,
    create_measurement_type,
    create_sample_measurement_file,
    delete_log_file,
    delete_measurement_type,
    delete_sample_measurement_file,
    list_log_files,
    list_measurement_types,
    list_sample_measurement_files,
)


def _get_project(request, project_id):
    return get_object_or_404(Project, pk=project_id, created_by=request.user)


def _get_experiment(request, project_id, experiment_id):
    project = _get_project(request, project_id)
    experiment = get_object_or_404(Experiment, pk=experiment_id, project=project)
    return project, experiment


@login_required
def measurement_type_list(request, project_id):
    project = _get_project(request, project_id)
    measurement_types = list_measurement_types(project)
    return render(
        request,
        "trainings/measurement_type_list.html",
        {"project": project, "measurement_types": measurement_types},
    )


@login_required
def measurement_type_create(request, project_id):
    project = _get_project(request, project_id)
    if request.method == "POST":
        form = MeasurementTypeForm(request.POST)
        if form.is_valid():
            create_measurement_type(
                project=project,
                name=form.cleaned_data["name"],
                unit=form.cleaned_data["unit"],
            )
            return redirect("measurement_type_list", project_id=project.id)
    else:
        form = MeasurementTypeForm()
    return render(
        request,
        "trainings/measurement_type_form.html",
        {"form": form, "project": project},
    )


@login_required
def measurement_type_delete(request, project_id, measurement_type_id):
    project = _get_project(request, project_id)
    measurement_type = get_object_or_404(MeasurementType, pk=measurement_type_id, project=project)
    if request.method == "POST":
        delete_measurement_type(measurement_type)
        return redirect("measurement_type_list", project_id=project.id)
    return render(
        request,
        "trainings/measurement_type_confirm_delete.html",
        {"measurement_type": measurement_type, "project": project},
    )


@login_required
def log_file_list(request, project_id, experiment_id):
    project, experiment = _get_experiment(request, project_id, experiment_id)
    log_files = list_log_files(experiment)
    return render(
        request,
        "trainings/log_file_list.html",
        {"project": project, "experiment": experiment, "log_files": log_files},
    )


@login_required
def log_file_create(request, project_id, experiment_id):
    project, experiment = _get_experiment(request, project_id, experiment_id)
    if request.method == "POST":
        form = LogFileForm(request.POST, request.FILES)
        if form.is_valid():
            create_log_file(
                experiment=experiment,
                file=form.cleaned_data["file"],
                file_type=form.cleaned_data["file_type"],
            )
            return redirect("log_file_list", project_id=project.id, experiment_id=experiment.id)
    else:
        form = LogFileForm()
    return render(
        request,
        "trainings/log_file_form.html",
        {"form": form, "project": project, "experiment": experiment},
    )


@login_required
def log_file_delete(request, project_id, experiment_id, log_file_id):
    project, experiment = _get_experiment(request, project_id, experiment_id)
    log_file = get_object_or_404(LogFile, pk=log_file_id, experiment=experiment)
    if request.method == "POST":
        delete_log_file(log_file)
        return redirect("log_file_list", project_id=project.id, experiment_id=experiment.id)
    return render(
        request,
        "trainings/log_file_confirm_delete.html",
        {"log_file": log_file, "project": project, "experiment": experiment},
    )


@login_required
def sample_measurement_file_list(request, project_id, experiment_id):
    project, experiment = _get_experiment(request, project_id, experiment_id)
    sample_files = list_sample_measurement_files(experiment)
    return render(
        request,
        "trainings/sample_measurement_file_list.html",
        {"project": project, "experiment": experiment, "sample_files": sample_files},
    )


@login_required
def sample_measurement_file_create(request, project_id, experiment_id):
    project, experiment = _get_experiment(request, project_id, experiment_id)
    if request.method == "POST":
        form = SampleMeasurementFileForm(request.POST, request.FILES, project=project)
        if form.is_valid():
            create_sample_measurement_file(
                experiment=experiment,
                measurement_type=form.cleaned_data["measurement_type"],
                file=form.cleaned_data["file"],
            )
            return redirect(
                "sample_measurement_file_list", project_id=project.id, experiment_id=experiment.id
            )
    else:
        form = SampleMeasurementFileForm(project=project)
    return render(
        request,
        "trainings/sample_measurement_file_form.html",
        {"form": form, "project": project, "experiment": experiment},
    )


@login_required
def sample_measurement_file_delete(request, project_id, experiment_id, sample_file_id):
    project, experiment = _get_experiment(request, project_id, experiment_id)
    sample_file = get_object_or_404(SampleMeasurementFile, pk=sample_file_id, experiment=experiment)
    if request.method == "POST":
        delete_sample_measurement_file(sample_file)
        return redirect(
            "sample_measurement_file_list", project_id=project.id, experiment_id=experiment.id
        )
    return render(
        request,
        "trainings/sample_measurement_file_confirm_delete.html",
        {"sample_file": sample_file, "project": project, "experiment": experiment},
    )