from experiments.models import Output, TaskType

from .metrics import output_metrics


RANKING_METRICS = {
    TaskType.CLASSIF: {
        "accuracy": "Acurácia",
        "f1": "F1 (macro)",
        "precision": "Precisão (macro)",
        "recall": "Recall (macro)",
    },
    TaskType.REGR: {
        "mae": "MAE",
        "rmse": "RMSE",
        "r2": "R²",
        "mre": "MRE",
    },
}


LOWER_IS_BETTER = {"mae", "rmse", "mre"}


def rank_experiments(project, task, metric, output_name=None):
    outputs = Output.objects.filter(experiment__project=project, task=task).select_related("experiment")
    if output_name:
        outputs = outputs.filter(name=output_name)

    rows = []
    for output in outputs:
        metrics = output_metrics(output)
        if metrics is None or metrics[metric] is None:
            continue
        rows.append({
            "experiment": output.experiment,
            "output": output,
            "value": metrics[metric],
            "metrics": metrics,
        })

    rows.sort(key=lambda row: row["value"], reverse=metric not in LOWER_IS_BETTER)
    for position, row in enumerate(rows, start=1):
        row["position"] = position
    return rows