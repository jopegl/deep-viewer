import pandas as pd

from experiments.models import StepMetric, TrainingStep, ClassificationPrediction, RegressionPrediction, TaskType

BATCH_SIZE = 2000


def _float_or_none(value):
    return None if pd.isna(value) else float(value)


def _int_or_none(value):
    return None if pd.isna(value) else int(value)


def save_training(experiment, steps, metrics):
    experiment.steps.all().delete() 

    TrainingStep.objects.bulk_create(
        [
            TrainingStep(
                experiment=experiment,
                step=int(row.step),
                epoch=_int_or_none(row.epoch),
                train_loss=float(row.train_loss),
                val_loss=_float_or_none(row.val_loss),
                learning_rate=_float_or_none(row.learning_rate),
            )
            for row in steps.itertuples(index=False)
        ],
        batch_size=BATCH_SIZE,
    )

    step_ids = dict(experiment.steps.values_list("step", "id"))
    StepMetric.objects.bulk_create(
        [
            StepMetric(step_id=step_ids[m["step"]], metric=m["metric"], split=m["split"], value=m["value"])
            for m in metrics
        ],
        batch_size=BATCH_SIZE,
    )


def save_test(experiment, predictions): 
    experiment.classi_preds.all().delete()
    experiment.regr_preds.all().delete()

    if experiment.task == TaskType.REGR:
        model = RegressionPrediction
    else:
        model = ClassificationPrediction

    model.objects.bulk_create(
        [
            model(
                experiment=experiment,
                sample_id=row.sample_id,
                true_label=row.true_label,
                predicted_label=row.predicted_label,
            )
            for row in predictions.itertuples(index=False)
        ],
        batch_size=BATCH_SIZE,
    )