from django import forms
from django.db.models import Q

from ..models import Experiment, StepUnit, TaskType


class FilterForm(forms.Form):
    filter_fields = ()
    default_order = "-created_at"

    def is_active(self):
        return any(self.data.get(name) for name in self.filter_fields)

    def filter(self, queryset):
        if not self.is_valid():
            return queryset.order_by(self.default_order)
        queryset = self.apply_filters(queryset, self.cleaned_data)
        return queryset.order_by(self.cleaned_data.get("order") or self.default_order)

    def apply_filters(self, queryset, data):
        return queryset


def search_field(placeholder):
    return forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.SearchInput(attrs={"placeholder": placeholder, "class": "search-input"}),
    )


def select_field(label, choices):
    return forms.ChoiceField(
        required=False,
        label=label,
        choices=choices,
        widget=forms.Select(attrs={"class": "select", "onchange": "this.form.submit()"}),
    )


class ProjectFilterForm(FilterForm):
    filter_fields = ("q",)

    q = search_field("Buscar por nome ou descrição")
    order = select_field("Ordenar", [
        ("-created_at", "Mais recentes"),
        ("created_at", "Mais antigos"),
        ("name", "Nome (A a Z)"),
        ("-n_experiments", "Mais experimentos"),
    ])

    def apply_filters(self, queryset, data):
        q = data["q"].strip()
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(description__icontains=q))
        return queryset


class ExperimentFilterForm(FilterForm):
    filter_fields = ("q", "task", "unit", "group", "fold")

    q = search_field("Buscar por nome, grupo, arquitetura ou notas")
    task = select_field("Tarefa", [
        ("", "Todas as tarefas"),
        (TaskType.CLASSIF, "Classificação"),
        (TaskType.REGR, "Regressão"),
        ("none", "Sem teste importado"),
    ])
    unit = select_field("Unidade", [("", "Época e iteração")] + list(StepUnit.choices))
    group = select_field("Grupo", [])
    fold = select_field("Fold", [])
    order = select_field("Ordenar", [
        ("-created_at", "Mais recentes"),
        ("created_at", "Mais antigos"),
        ("name", "Nome (A a Z)"),
    ])

    def __init__(self, data=None, project=None):
        super().__init__(data)
        experiments = project.experiments.all() if project else Experiment.objects.none()
        groups = sorted(set(experiments.exclude(group_name="").values_list("group_name", flat=True)), key=str.lower)
        folds = sorted(set(experiments.exclude(fold=None).values_list("fold", flat=True)))

        if groups:
            self.fields["group"].choices = (
                [("", "Todos os grupos")] + [(name, name) for name in groups] + [("none", "Sem grupo")]
            )
        else:
            del self.fields["group"]

        if folds:
            self.fields["fold"].choices = [("", "Todos os folds")] + [(str(n), f"Fold {n}") for n in folds]
        else:
            del self.fields["fold"]

    def apply_filters(self, queryset, data):
        q = data["q"].strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(architecture__icontains=q) | Q(notes__icontains=q)
                | Q(group_name__icontains=q)
            )
        group = data.get("group")
        if group == "none":
            queryset = queryset.filter(group_name="")
        elif group:
            queryset = queryset.filter(group_name__iexact=group)
        if data.get("fold"):
            queryset = queryset.filter(fold=int(data["fold"]))
        if data["unit"]:
            queryset = queryset.filter(step_unit=data["unit"])
        if data["task"] == "none":
            queryset = queryset.filter(outputs__isnull=True)
        elif data["task"]:
            queryset = queryset.filter(outputs__task=data["task"]).distinct()
        return queryset
