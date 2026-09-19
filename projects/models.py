from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(max_length=500, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_projects",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Experiment(models.Model):
    name = models.CharField(max_length=150)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="experiments",
    )

    dataset = models.CharField(max_length=200, blank=True)
    architecture = models.CharField(max_length=200, blank=True)

    hyperparameters = models.JSONField(blank=True, default=dict)

    notes = models.TextField(blank=True)

    run_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_experiment_name_per_project"
            )
        ]

    def clean(self):
        if self.run_at and self.run_at > timezone.now():
            raise ValidationError({"run_at": "run_at cannot be in the future"})
        if not isinstance(self.hyperparameters, dict):
            raise ValidationError({"hyperparameters": "hyperparameters must be a JSON object"})

    def __str__(self):
        return self.name