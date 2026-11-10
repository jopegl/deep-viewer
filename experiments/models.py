from django.conf import settings
from django.db import models


class SplitType(models.TextChoices):
    VAL = "val", "Validação"
    TRAIN = "train", "Treino"


class TaskType(models.TextChoices):
    CLASSIF = "Classification", "Classificação"
    REGR = "Regression", "Regressão"


class ExperimentFileType(models.TextChoices):
    TRAIN = "train", "Treino"
    TEST = "test", "Teste"


class StepUnit(models.TextChoices):
    EPOCH = "epoch", "Época"
    ITER = "iter", "Iteração"


class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=200, blank=True)
    analyst = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Experiment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="experiments")
    name = models.CharField(max_length=100)
    architecture = models.CharField(max_length=50, blank=True)
    notes = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    step_unit = models.CharField(max_length=15, choices=StepUnit.choices, default=StepUnit.EPOCH)

    def __str__(self):
        if self.architecture:
            return f"{self.name} ({self.architecture})"
        return self.name

    def test_sample_count(self):
        return sum(o.classi_preds.count() + o.regr_preds.count() for o in self.outputs.all())

    def task_label(self):
        tasks = {output.task for output in self.outputs.all()}
        if not tasks:
            return ""
        if len(tasks) > 1:
            return "Classificação + regressão"
        return TaskType(tasks.pop()).label


class Output(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="outputs")
    name = models.CharField(max_length=100)
    task = models.CharField(max_length=20, choices=TaskType.choices)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["experiment", "name"], name="unique_output_per_experiment"),
        ]

    def __str__(self):
        return f"{self.experiment} · {self.name}"


class Hyperparameter(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="hyperparameters")
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}: {self.value}"


class TrainingStep(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="steps")
    step = models.IntegerField()
    train_loss = models.FloatField()
    val_loss = models.FloatField(null=True, blank=True)
    learning_rate = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["step"]

    def __str__(self):
        return f"Step {self.step}"


class StepMetric(models.Model):
    step = models.ForeignKey(TrainingStep, on_delete=models.CASCADE, related_name="metrics")
    metric = models.CharField(max_length=200)
    value = models.FloatField()
    split = models.CharField(max_length=15, choices=SplitType.choices)

    def __str__(self):
        return f"{self.metric}: {self.value}"


class ImportedFile(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="files")
    kind = models.CharField(max_length=20, choices=ExperimentFileType.choices)
    file = models.FileField(upload_to="imports/")
    original_name = models.CharField(max_length=250)
    imported_at = models.DateTimeField(auto_now_add=True)
    column_mapping = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.original_name} ({self.kind})"


class ClassificationPrediction(models.Model):
    output = models.ForeignKey(Output, on_delete=models.CASCADE, related_name="classi_preds")
    sample_id = models.CharField(max_length=100)
    true_label = models.CharField(max_length=100)
    predicted_label = models.CharField(max_length=100)

    def __str__(self):
        return f"Sample {self.sample_id}"


class RegressionPrediction(models.Model):
    output = models.ForeignKey(Output, on_delete=models.CASCADE, related_name="regr_preds")
    sample_id = models.CharField(max_length=100)
    true_label = models.FloatField()
    predicted_label = models.FloatField()

    def __str__(self):
        return f"Sample {self.sample_id}"


class HistoryEntry(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="proj_history")
    experiment = models.ForeignKey(
        Experiment, on_delete=models.CASCADE, null=True, blank=True, related_name="experiment_history"
    )
    action = models.CharField(max_length=50)
    details = models.TextField(max_length=200, blank=True)
    analyst = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.action}"