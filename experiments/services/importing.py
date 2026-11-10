import pandas as pd
from django.core.files.storage import default_storage
from django.db import transaction

from experiments.models import (
    ClassificationPrediction,
    ExperimentFileType,
    Output,
    RegressionPrediction,
    StepMetric,
    TaskType,
    TrainingStep,
)
from experiments.services.parsing import (
    detect_task,
    find_metric_columns,
    find_outputs,
    match_test_columns,
    match_train_columns,
    prepare_outputs,
    prepare_test,
    prepare_training,
    read_table,
)

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


def save_outputs(experiment, outputs):
    experiment.outputs.all().delete()
    for data in outputs:
        output = Output.objects.create(experiment=experiment, name=data["name"], task=data["task"])
        model = RegressionPrediction if data["task"] == TaskType.REGR else ClassificationPrediction
        model.objects.bulk_create(
            [model(output=output, sample_id=s, true_label=t, predicted_label=p) for s, t, p in data["rows"]],
            batch_size=BATCH_SIZE,
        )


def save_test(experiment, predictions, task):
    rows = list(zip(
        predictions["sample_id"],
        predictions["true_label"],
        predictions["predicted_label"],
    ))
    save_outputs(experiment, [{"name": "principal", "task": task, "rows": rows}])


def store_upload(experiment, uploaded_file):
    return default_storage.save(f"imports/{experiment.pk}/{uploaded_file.name}", uploaded_file)


def load_table(stored_path):
    with default_storage.open(stored_path) as f:
        return read_table(f)


def run_import(experiment, kind, df, mapping):
    if kind == ExperimentFileType.TRAIN:
        metric_columns = find_metric_columns(df.columns, mapping)
        steps, metrics = prepare_training(df, mapping, metric_columns)
        with transaction.atomic():
            save_training(experiment, steps, metrics)
        return {"steps": len(steps), "metrics": len(metrics)}

    values = pd.concat([df[mapping["true_label"]], df[mapping["predicted_label"]]]).dropna()
    task = detect_task(values)
    predictions = prepare_test(df, mapping, is_regression=task == TaskType.REGR)
    with transaction.atomic():
        save_test(experiment, predictions, task)
    return {"samples": len(predictions), "task": task}


def start_import(experiment, kind, uploaded_file):
    stored_path = store_upload(experiment, uploaded_file)
    df = load_table(stored_path)

    if kind == ExperimentFileType.TEST and find_outputs(df):
        outputs = prepare_outputs(df)
        with transaction.atomic():
            save_outputs(experiment, outputs)
        names = ", ".join(f"{o['name']} ({o['task']})" for o in outputs)
        return {
            "imported": True,
            "stored_path": stored_path,
            "summary": {"samples": len(df), "outputs": names},
        }

    if kind == ExperimentFileType.TRAIN:
        mapping, missing = match_train_columns(df.columns, experiment.step_unit)
    else:
        mapping, missing = match_test_columns(df.columns)

    if missing:
        return {
            "imported": False,
            "stored_path": stored_path,
            "columns": list(df.columns),
            "mapping": mapping,
            "missing": missing,
        }

    summary = run_import(experiment, kind, df, mapping)
    return {"imported": True, "stored_path": stored_path, "summary": summary}


def finish_import(experiment, kind, stored_path, mapping):
    df = load_table(stored_path)
    return run_import(experiment, kind, df, mapping)