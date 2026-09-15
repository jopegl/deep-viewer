from django.db import models

from projects.models import Experiment  # ajuste o import se renomear o app


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
        help_text="Null if the metric was added manually instead of parsed from a file",
    )

    name = models.CharField(max_length=100, help_text="e.g. loss, accuracy, iou, f1")
    split = models.CharField(
        max_length=10, choices=Split.choices, default=Split.TRAIN
    )
    step = models.PositiveIntegerField(help_text="Epoch number or iteration/step number")
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