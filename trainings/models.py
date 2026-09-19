from django.db import models

from projects.models import Experiment, Project


class LogFile(models.Model):

    class FileType(models.TextChoices):
        CSV = "csv", "CSV"
        JSON = "json", "JSON"
        TENSORBOARD = "tensorboard", "TensorBoard"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"
        ERROR = "error", "Error"

    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name="log_files",
    )

    file = models.FileField(upload_to="log_files/%Y/%m/")
    file_type = models.CharField(max_length=20, choices=FileType.choices)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Log file"
        verbose_name_plural = "Log files"

    def __str__(self):
        return f"{self.experiment} — {self.file.name}"


class Metric(models.Model):

    class Split(models.TextChoices):
        TRAIN = "train", "Train"
        VAL = "val", "Validation"
        TEST = "test", "Test"

    class StepUnit(models.TextChoices):
        EPOCH = "epoch", "Epoch"
        ITERATION = "iteration", "Iteration"

    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    log_file = models.ForeignKey(
        LogFile,
        on_delete=models.CASCADE,
        related_name="metrics",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=100)
    split = models.CharField(
        max_length=10, choices=Split.choices, default=Split.TRAIN
    )
    fold = models.PositiveIntegerField(null=True, blank=True)
    step = models.PositiveIntegerField()
    step_unit = models.CharField(
        max_length=10, choices=StepUnit.choices, default=StepUnit.EPOCH
    )
    value = models.FloatField()

    class Meta:
        ordering = ["step"]
        indexes = [
            models.Index(fields=["experiment", "name", "split"]),
        ]
        verbose_name = "Metric"
        verbose_name_plural = "Metrics"

    def __str__(self):
        return f"{self.experiment} — {self.name}[{self.split}]@{self.step_unit}{self.step}={self.value}"


class MeasurementType(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="measurement_types",
    )

    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_measurement_type_per_project"
            )
        ]
        verbose_name = "Measurement type"
        verbose_name_plural = "Measurement types"

    def __str__(self):
        return f"{self.name} ({self.unit})" if self.unit else self.name


class Sample(models.Model):

    class Split(models.TextChoices):
        TRAIN = "train", "Train"
        VAL = "val", "Validation"
        TEST = "test", "Test"

    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name="samples",
    )

    identifier = models.CharField(max_length=255)
    split = models.CharField(max_length=10, choices=Split.choices, default=Split.VAL)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["identifier"]
        verbose_name = "Sample"
        verbose_name_plural = "Samples"

    def __str__(self):
        return f"{self.experiment} — {self.identifier}"


class SampleMeasurement(models.Model):

    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        related_name="measurements",
    )
    measurement_type = models.ForeignKey(
        MeasurementType,
        on_delete=models.PROTECT,
        related_name="measurements",
    )

    predicted_value = models.FloatField()
    actual_value = models.FloatField()

    class Meta:
        ordering = ["measurement_type"]
        indexes = [
            models.Index(fields=["sample", "measurement_type"]),
        ]
        verbose_name = "Sample measurement"
        verbose_name_plural = "Sample measurements"

    def __str__(self):
        return (
            f"{self.sample} — {self.measurement_type}: "
            f"pred={self.predicted_value} actual={self.actual_value}"
        )


class SampleMeasurementFile(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"
        ERROR = "error", "Error"

    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name="sample_measurement_files",
    )
    measurement_type = models.ForeignKey(
        MeasurementType,
        on_delete=models.PROTECT,
        related_name="sample_measurement_files",
    )

    file = models.FileField(upload_to="sample_measurement_files/%Y/%m/")

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Sample measurement file"
        verbose_name_plural = "Sample measurement files"

    def __str__(self):
        return f"{self.experiment} — {self.measurement_type} — {self.file.name}"