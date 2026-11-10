from experiments.models import TaskType

from .metrics import experiment_metrics


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


def rank_experiments(project, task, metric):
    rows = []
    for experiment in project.experiments.filter(task=task):
        metrics = experiment_metrics(experiment)
        if metrics is None or metrics[metric] is None:
            continue
        rows.append({"experiment": experiment, "value": metrics[metric], "metrics": metrics})

    rows.sort(key=lambda row: row["value"], reverse=metric not in LOWER_IS_BETTER)
    for position, row in enumerate(rows, start=1):
        row["position"] = position
    return rows