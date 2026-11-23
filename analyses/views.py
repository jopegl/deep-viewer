from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify

from experiments.models import Experiment, Output, Project, TaskType

from .services.charts import ranking_chart, training_curve, training_metric_names
from .services.export import write_metrics, write_predictions
from .services.ranking import rank_experiments, ranking_outputs, ranking_tasks
from .services.tasks import get_analysis


def _choose(value, options):
    return value if value in options else options[0]


def _csv_response(*name_parts):
    filename = "_".join(slugify(part) or "arquivo" for part in name_parts) + ".csv"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    return response


@login_required
def experiment_results(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)

    metric_names = training_metric_names(experiment)
    selected_metric = request.GET.get("metric", "loss")
    if selected_metric not in metric_names:
        selected_metric = "loss"

    outputs = list(experiment.outputs.all())
    selected_output = request.GET.get("output")
    output = next((o for o in outputs if o.name == selected_output), outputs[0] if outputs else None)

    analysis = get_analysis(output.task).analyze(output) if output is not None else None

    return render(request, "analyses/experiment_results.html", {
        "experiment": experiment,
        "metric_names": metric_names,
        "selected_metric": selected_metric,
        "training_chart": training_curve(experiment, selected_metric),
        "outputs": outputs,
        "output": output,
        "test_metrics": analysis["metrics"] if analysis else None,
        "test_chart": analysis["chart"] if analysis else None,
        "worst_errors": analysis["worst_errors"] if analysis else [],
        "test_template": analysis["template_name"] if analysis else None,
    })

@login_required
def project_ranking(request, pk):
    project = get_object_or_404(Project, pk=pk, analyst=request.user)
    tasks = ranking_tasks(project)
    context = {
        "project": project,
        "tasks": [(task, TaskType(task).label) for task in tasks],
    }
    if not tasks:
        return render(request, "analyses/project_ranking.html", context)

    task = _choose(request.GET.get("task"), tasks)
    analysis = get_analysis(task)
    metric = _choose(request.GET.get("metric"), list(analysis.ranking_metrics))

    output_names = ranking_outputs(project, task)
    output_name = request.GET.get("output", "")
    if output_name not in output_names:
        output_name = ""
    show_output = not output_name and len(output_names) > 1

    columns = [
        {"key": key, "label": label, "selected": key == metric}
        for key, label in analysis.ranking_metrics.items()
    ]
    rows = rank_experiments(project, task, metric, output_name or None)
    for row in rows:
        name = row["experiment"].name
        row["label"] = f"{name} · {row['output'].name}" if show_output else name
        row["cells"] = [
            {"value": row["metrics"][column["key"]], "selected": column["selected"]}
            for column in columns
        ]

    metric_label = analysis.ranking_metrics[metric]
    context.update({
        "task": task,
        "metric": metric,
        "metric_label": metric_label,
        "columns": columns,
        "output_names": output_names,
        "output_name": output_name,
        "show_output": show_output,
        "lower_is_better": metric in analysis.lower_is_better,
        "rows": rows,
        "chart": ranking_chart(
            [row["label"] for row in rows], [row["value"] for row in rows], metric_label
        ) if rows else None,
    })
    return render(request, "analyses/project_ranking.html", context)


@login_required
def export_metrics(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)
    response = _csv_response(experiment.name, "metricas")
    write_metrics(experiment, response)
    return response


@login_required
def export_predictions(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)
    output = get_object_or_404(Output, experiment=experiment, name=request.GET.get("output", ""))
    response = _csv_response(experiment.name, output.name, "predicoes")
    write_predictions(output, response)
    return response
