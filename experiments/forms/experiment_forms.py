from django import forms
from ..models import *


class ExperimentForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = [
            "name",
            "architecture",
            "notes",
            "task",
            "step_unit"
        ]
