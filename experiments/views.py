from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ColumnMappingForm, UploadForm
from .models import Experiment, ExperimentFileType
from .services.importing import finish_import, start_import
from .services.parsing import (
    TEST_FIELDS,
    TRAIN_FIELDS,
    TRAIN_OPTIONAL,
    expected_columns_test,
    expected_columns_train,
)

SESSION_KEY = "pending_import"


def _summary_text(kind, summary):
    if kind == ExperimentFileType.TRAIN:
        return f"{summary['steps']} passos e {summary['metrics']} métricas"
    return f"{summary['samples']} amostras"


def _mapping_fields(experiment, kind):
    if kind == ExperimentFileType.TRAIN:
        names = expected_columns_train(experiment.step_unit)
        fields = {field: TRAIN_FIELDS[field] for field in names}
        required = [field for field in fields if field not in TRAIN_OPTIONAL]
    else:
        fields = dict(TEST_FIELDS)
        required = list(fields)
    return fields, required


@login_required
def import_upload(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            kind = form.cleaned_data["kind"]
            try:
                result = start_import(experiment, kind, form.cleaned_data["file"])
            except Exception as e:
                for msg in e.messages:
                    form.add_error("file", msg)
            else:
                if result["imported"]:
                    messages.success(request, f"Planilha importada: {_summary_text(kind, result['summary'])}.")
                    return redirect("experiment_import", pk=experiment.pk)

                request.session[SESSION_KEY] = {
                    "experiment": experiment.pk,
                    "kind": kind,
                    "stored_path": result["stored_path"],
                    "columns": result["columns"],
                    "mapping": result["mapping"],
                    "missing": result["missing"],
                }
                return redirect("experiment_import_mapping", pk=experiment.pk)
    else:
        form = UploadForm()

    return render(request, "experiments/import_upload.html", {
        "form": form,
        "experiment": experiment,
        "train_columns": expected_columns_train(experiment.step_unit).values(),
        "test_columns": expected_columns_test().values(),
    })


@login_required
def import_mapping(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)

    pending = request.session.get(SESSION_KEY)
    if not pending or pending["experiment"] != experiment.pk:
        messages.error(request, "Não há nenhuma importação pendente para este experimento.")
        return redirect("experiment_import", pk=experiment.pk)

    kind = pending["kind"]
    fields, required = _mapping_fields(experiment, kind)
    form_options = {
        "columns": pending["columns"],
        "fields": fields,
        "required_fields": required,
        "initial_mapping": pending["mapping"],
    }

    if request.method == "POST":
        form = ColumnMappingForm(request.POST, **form_options)
        if form.is_valid():
            try:
                summary = finish_import(experiment, kind, pending["stored_path"], form.get_mapping())
            except Exception as e:
                form.add_error(None, e.messages)
            else:
                del request.session[SESSION_KEY]
                messages.success(request, f"Planilha importada: {_summary_text(kind, summary)}.")
                return redirect("experiment_import", pk=experiment.pk)
    else:
        form = ColumnMappingForm(**form_options)

    return render(request, "experiments/import_mapping.html", {
        "form": form,
        "experiment": experiment,
        "missing": pending["missing"],
    })