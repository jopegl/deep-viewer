from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from experiments.models import Experiment

from .services.charts import training_curve, training_metric_names
from .services.tasks import get_analysis


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