from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from experiments.models import Experiment, TaskType

from .services.charts import (
    confusion_matrix_chart,
    training_curve,
    training_metric_names,
    true_vs_predicted_chart,
)
from .services.metrics import experiment_metrics, worst_errors


@login_required
def experiment_results(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk, project__analyst=request.user)
    is_regression = experiment.task == TaskType.REGR

    metric_names = training_metric_names(experiment)
    selected_metric = request.GET.get("metric", "loss")
    if selected_metric not in metric_names:
        selected_metric = "loss"

    if is_regression:
        test_chart = true_vs_predicted_chart(experiment)
    else:
        test_chart = confusion_matrix_chart(experiment)

    return render(request, "analyses/experiment_results.html", {
        "experiment": experiment,
        "is_regression": is_regression,
        "metric_names": metric_names,
        "selected_metric": selected_metric,
        "training_chart": training_curve(experiment, selected_metric),
        "test_metrics": experiment_metrics(experiment),
        "test_chart": test_chart,
        "worst_errors": worst_errors(experiment),
    })