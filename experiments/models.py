from django.db import models
from django.conf import settings

# Create your models here.
class SplitType(models.TextChoices):
    VAL =  "val"
    TRAIN = "train"

class TaskType(models.TextChoices):
    CLASSIF = "Classification", "Classif"
    REGR = "Regression", "Regr"

class ExperimentFileType(models.TextChoices):
    TRAIN = "train"
    TEST = "test"

class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=200)
    analyst = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField()

    def __str__(self):
                return self.name

class Experiment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name= "experiments")
    name = models.CharField(max_length=100)
    architecture = models.CharField(max_length=50)
    notes = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    task = models.CharField(max_length=15, choices=TaskType.choices)

    def __str__(self):
                return f"{self.name} ({self.architecture})"
    
class Hyperparameter(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name= "hyperparameters")
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    def __str__(self):
                return f"{self.name}: {self.value}"


class TrainingEpoch(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name= "epochs")
    epoch = models.IntegerField()
    train_loss = models.FloatField()
    val_loss = models.FloatField()
    learning_rate = models.FloatField()

    def __str__(self):
                return f"Epoch {self.epoch}"

class EpochMetric(models.Model):
    epoch = models.ForeignKey(TrainingEpoch, on_delete=models.CASCADE, related_name= "metrics")
    metric = models.CharField(max_length=200)
    value = models.FloatField()
    split = models.CharField(max_length=15, choices=SplitType.choices)

    def __str__(self):
            return f"{self.metric}: {self.value}"

class ImportedFile(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="files")
    kind = models.CharField(max_length=20, choices=ExperimentFileType.choices)
    path = models.CharField(max_length=100)
    original_name = models.CharField(max_length=50)
    imported_at = models.DateTimeField(auto_now_add=True)
    column_mapping = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.original_name} ({self.kind}), Path: {self.path}"


class ClassificationPrediction(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="classi_preds")
    sample_id = models.CharField(max_length=10)
    true_label = models.CharField(max_length=30)
    predicted_label = models.CharField(max_length=30)

    def __str__(self):
                return f"Sample {self.sample_id}"


class RegressionPrediction(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="regr_preds")
    sample_id = models.CharField(max_length=10)
    true_label = models.FloatField()
    predicted_label = models.FloatField()

    def __str__(self):
                return f"Sample {self.sample_id}"


class HistoryEntry(models.Model):
      project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="proj_history")
      experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, null=True, blank=True, related_name="experiment_history")
      action = models.CharField(max_length=20)
      details = models.TextField(max_length=200, blank=True, null=True)
      analyst = models.CharField(max_length=30)
      timestamp = models.DateTimeField(auto_now_add=True)

      def __str__(self):
                  return f"[{self.timestamp}] {self.action}"
