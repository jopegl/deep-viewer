import csv

from experiments.services.tasks import get_task

from .tasks import get_analysis


def write_metrics(experiment, file):
    writer = csv.writer(file)
    writer.writerow(["output", "task", "metric", "value"])
    for output in experiment.outputs.order_by("name"):
        analysis = get_analysis(output.task)
        metrics = analysis.output_metrics(output)
        if metrics is None:
            continue
        for key in [*analysis.ranking_metrics, "n_samples"]:
            value = metrics[key]
            writer.writerow([output.name, output.task, key, "" if value is None else value])


def write_predictions(output, file):
    writer = csv.writer(file)
    writer.writerow(["sample_id", "true_label", "predicted_label"])
    rows = (
        get_task(output.task)
        .predictions(output)
        .order_by("pk")
        .values_list("sample_id", "true_label", "predicted_label")
    )
    writer.writerows(rows)
