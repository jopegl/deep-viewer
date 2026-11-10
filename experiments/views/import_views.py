from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms.import_forms import ColumnMappingForm, OutputTaskForm, UploadForm
from ..models import Experiment, ExperimentFileType
from ..services.exceptions import ImportValidationError
from ..services.importing import continue_import, finish_test_import, start_import
from ..services.parsing import (
    TEST_FIELDS,
    TRAIN_FIELDS,
    TRAIN_OPTIONAL,
    expected_columns_test,
    expected_columns_train,
)

SESSION_KEY = "pending_import"


def _mapping_fields(experiment, kind):
    if kind == ExperimentFileType.TRAIN:
        names = expected_columns_train(experiment.step_unit)
        fields = {field: TRAIN_FIELDS[field] for field in names}
        required = [field for field in fields if field not in TRAIN_OPTIONAL]
    else:
        fields = dict(TEST_FIELDS)
        required = list(fields)
    return fields, required


def _pending(request, experiment):
    pending = request.session.get(SESSION_KEY)
    if not pending or pending["experiment"] != experiment.pk:
        return None
    return pending


def _go_to_next_step(request, experiment, kind, result):
    if result["next"] == "done":
        request.session.pop(SESSION_KEY, None)
        summary = result["summary"]
        messages.success(request, f"Planilha importada: {summary['steps']} passos e {summary['metrics']} métricas.")
        return redirect("experiment_import", pk=experiment.pk)

    pending = {"experiment": experiment.pk, "kind": kind}
    pending.update({key: value for key, value in result.items() if key != "next"})
    request.session[SESSION_KEY] = pending

    if result["next"] == "mapping":
        return redirect("experiment_import_mapping", pk=experiment.pk)
    return redirect("experiment_import_tasks", pk=experiment.pk)


@login_required
def import_upload(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            kind = form.cleaned_data["kind"]
            try:
                result = start_import(experiment, kind, form.cleaned_data["file"])
            except ImportValidationError as e:
                for msg in e.messages:
                    form.add_error("file", msg)
            else:
                return _go_to_next_step(request, experiment, kind, result)
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

    pending = _pending(request, experiment)
    if pending is None or "missing" not in pending:
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
                result = continue_import(experiment, kind, pending["stored_path"], form.get_mapping())
            except ImportValidationError as e:
                form.add_error(None, e.messages)
            else:
                return _go_to_next_step(request, experiment, kind, result)
    else:
        form = ColumnMappingForm(**form_options)

    return render(request, "experiments/import_mapping.html", {
        "form": form,
        "experiment": experiment,
        "missing": pending["missing"],
    })


@login_required
def import_tasks(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)

    pending = _pending(request, experiment)
    if pending is None or "outputs" not in pending:
        messages.error(request, "Não há nenhuma importação pendente para este experimento.")
        return redirect("experiment_import", pk=experiment.pk)

    form = OutputTaskForm(request.POST or None, outputs=pending["outputs"])
    if request.method == "POST" and form.is_valid():
        try:
            summary = finish_test_import(experiment, pending["stored_path"], pending["mapping"], form.get_tasks())
        except ImportValidationError as e:
            form.add_error(None, e.messages)
        else:
            request.session.pop(SESSION_KEY, None)
            messages.success(
                request,
                f"Planilha importada: {summary['samples']} amostras em {summary['outputs']} saída(s).",
            )
            return redirect("experiment_results", pk=experiment.pk)

    return render(request, "experiments/import_tasks.html", {
        "form": form,
        "experiment": experiment,
    })
