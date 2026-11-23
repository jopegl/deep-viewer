from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Count

from ..models import Experiment
from ..services.folds import parse_fold_name


class ExperimentForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = [
            "name",
            "group_name",
            "fold",
            "architecture",
            "notes",
            "step_unit",
        ]
        labels = {
            "group_name": "Grupo",
            "fold": "Fold",
        }
        help_texts = {
            "group_name": "Escolha um grupo da lista ou digite um nome novo para criar outro. Experimentos do mesmo grupo aparecem juntos, como os folds de uma validação cruzada.",
            "fold": "Deixe grupo e fold em branco para preencher pelo nome, como em “EfficientNet CV1 Fold 3”.",
        }
        widgets = {
            "group_name": forms.TextInput(attrs={
                "autocomplete": "off",
                "placeholder": "Escolha um grupo ou digite um nome novo",
                "data-group-options": "group-options",
            }),
            "fold": forms.NumberInput(attrs={"min": 0}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project or (self.instance.project if self.instance.pk else None)
        self.group_options = self._group_options()

    def _group_options(self):
        if self.project is None:
            return []
        groups = (
            self.project.experiments.exclude(group_name="")
            .values("group_name")
            .annotate(count=Count("pk"))
        )
        options = [{"name": group["group_name"], "count": group["count"]} for group in groups]
        return sorted(options, key=lambda option: option["name"].lower())

    def _others(self):
        others = Experiment.objects.filter(project=self.project)
        if self.instance.pk:
            others = others.exclude(pk=self.instance.pk)
        return others

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self._others().filter(name__iexact=name).exists():
            raise ValidationError("Já existe um experimento com este nome neste projeto.")
        return name

    def clean(self):
        cleaned = super().clean()
        group = (cleaned.get("group_name") or "").strip()
        fold = cleaned.get("fold")

        if not group and fold is None and cleaned.get("name"):
            parsed = parse_fold_name(cleaned["name"])
            if parsed:
                group, fold = parsed

        known = {option["name"].lower(): option["name"] for option in self.group_options}
        group = known.get(group.lower(), group)
        cleaned["group_name"] = group
        cleaned["fold"] = fold

        if fold is not None and self._others().filter(group_name__iexact=group, fold=fold).exists():
            place = f"no grupo “{group}”" if group else "entre os experimentos sem grupo"
            self.add_error("fold", f"Já existe um experimento com o fold {fold} {place}.")
        return cleaned
