from django import forms
from django.db.models import Q

from ..models import StepUnit, TaskType


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
    filter_fields = ("q", "task", "unit")

    q = search_field("Buscar por nome, arquitetura ou notas")
    task = select_field("Tarefa", [
        ("", "Todas as tarefas"),
        (TaskType.CLASSIF, "Classificação"),
        (TaskType.REGR, "Regressão"),
        ("none", "Sem teste importado"),
    ])
    unit = select_field("Unidade", [("", "Época e iteração")] + list(StepUnit.choices))
    order = select_field("Ordenar", [
        ("-created_at", "Mais recentes"),
        ("created_at", "Mais antigos"),
        ("name", "Nome (A a Z)"),
    ])

    def apply_filters(self, queryset, data):
        q = data["q"].strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(architecture__icontains=q) | Q(notes__icontains=q)
            )
        if data["unit"]:
            queryset = queryset.filter(step_unit=data["unit"])
        if data["task"] == "none":
            queryset = queryset.filter(outputs__isnull=True)
        elif data["task"]:
            queryset = queryset.filter(outputs__task=data["task"]).distinct()
        return queryset
