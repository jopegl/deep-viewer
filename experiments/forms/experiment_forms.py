from django import forms
from django.core.exceptions import ValidationError
from ..models import *


class ExperimentForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = [
            "name",
            "architecture",
            "notes",
            "step_unit"
        ]

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = Experiment.objects.filter(project=self.project, name__iexact=name)

        # Na edição (UpdateView), exclui o próprio experimento da verificação
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(
                "Já existe um experimento com este nome neste projeto."
            )
        return name
