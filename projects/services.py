from .models import Experiment


def create_experiment(project, name, run_at, dataset="", architecture="", hyperparameters=None, notes=""):
    experiment = Experiment(
        project=project,
        name=name,
        run_at=run_at,
        dataset=dataset,
        architecture=architecture,
        hyperparameters=hyperparameters or {},
        notes=notes,
    )
    experiment.full_clean()
    experiment.save()
    return experiment


def get_experiment(experiment_id):
    return Experiment.objects.get(pk=experiment_id)


def list_experiments(project):
    return Experiment.objects.filter(project=project)


def update_experiment(experiment, **fields):
    for field, value in fields.items():
        setattr(experiment, field, value)
    experiment.full_clean()
    experiment.save()
    return experiment


def delete_experiment(experiment):
    experiment.delete()