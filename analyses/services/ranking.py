from experiments.models import Output, TaskType

from .tasks import get_analysis


def rank_experiments(project, task, metric, output_name=None):
    analysis = get_analysis(task)
    outputs = Output.objects.filter(experiment__project=project, task=task).select_related("experiment")
    if output_name:
        outputs = outputs.filter(name=output_name)

    rows = []
    for output in outputs:
        metrics = analysis.output_metrics(output)
        if metrics is None or metrics[metric] is None:
            continue
        rows.append({
            "experiment": output.experiment,
            "output": output,
            "value": metrics[metric],
            "metrics": metrics,
        })

    rows.sort(key=lambda row: row["value"], reverse=metric not in analysis.lower_is_better)
    for position, row in enumerate(rows, start=1):
        row["position"] = position
    return rows


def ranking_tasks(project):
    used = set(Output.objects.filter(experiment__project=project).values_list("task", flat=True))
    return [task for task in TaskType.values if task in used]


def ranking_outputs(project, task):
    names = Output.objects.filter(experiment__project=project, task=task).values_list("name", flat=True)
    return sorted(set(names))
