from django import forms
from django.core.exceptions import ValidationError
from ..models import *


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"] 

    def __init__(self, *args, analyst=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.analyst = analyst

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = Project.objects.filter(analyst=self.analyst, name__iexact=name)

        # Na edição (UpdateView), exclui o próprio projeto da verificação
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(
                "Você já possui um projeto com este nome. Escolha outro."
            )
        return name