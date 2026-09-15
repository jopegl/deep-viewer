from django.db import models
from django.conf import settings

class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(max_length=500, blank = True)

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
    name = models.CharField(max_length = 150)
    project = models.ForeignKey (
        Project,
        on_delete = models.CASCADE,
        related_name='experiments'
    )

    dataset = models.CharField(max_length=200, blank=True)
    architecture = models.CharField(max_length=200, blank=True)

    hyperparameters = models.JSONField(blank=True, default=dict)

    notes = models.TextField(blank=True)

    run_at = models.DateTimeField(
        help_text="When the training run actually happened (may differ from creation date)"
    )

    created_at = models.DateTimeField(auto_now_add=True)



 

 


