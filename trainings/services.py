import csv

from django.db import transaction
from django.utils import timezone

from .models import LogFile, Metric, MeasurementType, Sample, SampleMeasurement, SampleMeasurementFile

NON_METRIC_COLUMNS = {"split", "iteration", "timestamp"}


def create_measurement_type(project, name, unit=""):
    measurement_type = MeasurementType(project=project, name=name, unit=unit)
    measurement_type.full_clean()
    measurement_type.save()
    return measurement_type


def list_measurement_types(project):
    return MeasurementType.objects.filter(project=project)


def get_measurement_type(measurement_type_id):
    return MeasurementType.objects.get(pk=measurement_type_id)


def delete_measurement_type(measurement_type):
    measurement_type.delete()


def create_log_file(experiment, file, file_type):
    log_file = LogFile.objects.create(experiment=experiment, file=file, file_type=file_type)
    parse_metrics_csv(log_file)
    return log_file


def list_log_files(experiment):
    return LogFile.objects.filter(experiment=experiment)


def get_log_file(log_file_id):
    return LogFile.objects.get(pk=log_file_id)


def delete_log_file(log_file):
    log_file.file.delete(save=False)
    log_file.delete()


def create_sample_measurement_file(experiment, measurement_type, file):
    sample_file = SampleMeasurementFile.objects.create(
        experiment=experiment, measurement_type=measurement_type, file=file
    )
    parse_sample_measurement_file(sample_file)
    return sample_file


def list_sample_measurement_files(experiment):
    return SampleMeasurementFile.objects.filter(experiment=experiment)


def get_sample_measurement_file(sample_file_id):
    return SampleMeasurementFile.objects.get(pk=sample_file_id)


def delete_sample_measurement_file(sample_file):
    sample_file.file.delete(save=False)
    sample_file.delete()


def list_metrics(experiment, name=None, split=None):
    qs = Metric.objects.filter(experiment=experiment)
    if name:
        qs = qs.filter(name=name)
    if split:
        qs = qs.filter(split=split)
    return qs


def list_samples(experiment):
    return Sample.objects.filter(experiment=experiment)


def list_sample_measurements(experiment, measurement_type=None):
    qs = SampleMeasurement.objects.filter(sample__experiment=experiment)
    if measurement_type:
        qs = qs.filter(measurement_type=measurement_type)
    return qs


def _mark_error(instance, error):
    instance.status = instance.Status.ERROR
    instance.error_message = str(error)
    instance.save(update_fields=["status", "error_message"])


def _mark_processed(instance):
    instance.status = instance.Status.PROCESSED
    instance.processed_at = timezone.now()
    instance.save(update_fields=["status", "processed_at"])


def _read_csv_rows(file_field):
    with file_field.open("rb") as f:
        content = f.read().decode("utf-8")
    return list(csv.DictReader(content.splitlines()))


def parse_metrics_csv(log_file):
    try:
        rows = _read_csv_rows(log_file.file)

        metrics = []
        for row in rows:
            iteration = int(row["iteration"])
            fold = int(row["split"])
            for column, raw_value in row.items():
                if column in NON_METRIC_COLUMNS:
                    continue
                metrics.append(
                    Metric(
                        experiment=log_file.experiment,
                        log_file=log_file,
                        name=column,
                        split=Metric.Split.VAL,
                        fold=fold,
                        step=iteration,
                        step_unit=Metric.StepUnit.ITERATION,
                        value=float(raw_value),
                    )
                )
    except Exception as e:
        _mark_error(log_file, e)
        return

    with transaction.atomic():
        Metric.objects.bulk_create(metrics)
        _mark_processed(log_file)


def parse_sample_measurement_file(sample_file):
    try:
        rows = _read_csv_rows(sample_file.file)
    except Exception as e:
        _mark_error(sample_file, e)
        return

    try:
        with transaction.atomic():
            for row in rows:
                sample, _ = Sample.objects.get_or_create(
                    experiment=sample_file.experiment,
                    identifier=row["name"],
                )
                SampleMeasurement.objects.create(
                    sample=sample,
                    measurement_type=sample_file.measurement_type,
                    predicted_value=float(row["predicted"]),
                    actual_value=float(row["real"]),
                )
    except Exception as e:
        _mark_error(sample_file, e)
        return

    _mark_processed(sample_file)