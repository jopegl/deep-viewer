from django import forms

from .models import Experiment, Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]


class ExperimentForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ["name", "dataset", "architecture", "hyperparameters", "notes", "run_at"]
        widgets = {
            "run_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "hyperparameters": forms.Textarea(attrs={"rows": 4}),
        }