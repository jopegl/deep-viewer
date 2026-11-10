from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from experiments.models import Experiment, TaskType

from .services.charts import (
    confusion_matrix_chart,
    training_curve,
    training_metric_names,
    true_vs_predicted_chart,
)
from .services.metrics import output_metrics, worst_errors


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

    is_regression = output is not None and output.task == TaskType.REGR
    test_metrics = None
    test_chart = None
    errors = []
    if output is not None:
        test_metrics = output_metrics(output)
        test_chart = true_vs_predicted_chart(output) if is_regression else confusion_matrix_chart(output)
        errors = worst_errors(output)

    return render(request, "analyses/experiment_results.html", {
        "experiment": experiment,
        "metric_names": metric_names,
        "selected_metric": selected_metric,
        "training_chart": training_curve(experiment, selected_metric),
        "outputs": outputs,
        "output": output,
        "is_regression": is_regression,
        "test_metrics": test_metrics,
        "test_chart": test_chart,
        "worst_errors": errors,
    })