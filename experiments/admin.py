from django.contrib import admin

from .models import (
    ClassificationPrediction,
    Experiment,
    HistoryEntry,
    Hyperparameter,
    ImportedFile,
    Output,
    Project,
    RegressionPrediction,
    StepMetric,
    TrainingStep,
)


class ExperimentInline(admin.TabularInline):
    model = Experiment
    extra = 0
    fields = ("name", "architecture", "step_unit")
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "analyst", "created_at")
    list_filter = ("analyst",)
    search_fields = ("name", "description")
    inlines = [ExperimentInline]


class HyperparameterInline(admin.TabularInline):
    model = Hyperparameter
    extra = 1


class ImportedFileInline(admin.TabularInline):
    model = ImportedFile
    extra = 0
    readonly_fields = ("imported_at",)


class OutputInline(admin.TabularInline):
    model = Output
    extra = 0
    fields = ("name", "task")
    show_change_link = True


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "step_unit", "architecture", "created_at")
    list_filter = ("step_unit", "project")
    search_fields = ("name", "architecture", "notes")
    readonly_fields = ("created_at",)
    list_select_related = ("project",)
    inlines = [OutputInline, HyperparameterInline, ImportedFileInline]


@admin.register(Output)
class OutputAdmin(admin.ModelAdmin):
    list_display = ("name", "experiment", "task")
    list_filter = ("task", "experiment__project")
    search_fields = ("name", "experiment__name")
    list_select_related = ("experiment",)


@admin.register(Hyperparameter)
class HyperparameterAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "experiment")
    list_filter = ("experiment__project",)
    search_fields = ("name", "experiment__name")


class StepMetricInline(admin.TabularInline):
    model = StepMetric
    extra = 0


@admin.register(TrainingStep)
class TrainingStepAdmin(admin.ModelAdmin):
    list_display = ("experiment", "step", "train_loss", "val_loss", "learning_rate")
    list_filter = ("experiment",)
    ordering = ("experiment", "step")
    list_select_related = ("experiment",)
    inlines = [StepMetricInline]


@admin.register(StepMetric)
class StepMetricAdmin(admin.ModelAdmin):
    list_display = ("step", "metric", "split", "value")
    list_filter = ("split", "metric", "step__experiment")
    list_select_related = ("step__experiment",)


@admin.register(ImportedFile)
class ImportedFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "kind", "experiment", "imported_at")
    list_filter = ("kind",)
    search_fields = ("original_name", "experiment__name")
    readonly_fields = ("imported_at",)


@admin.register(ClassificationPrediction)
class ClassificationPredictionAdmin(admin.ModelAdmin):
    list_display = ("sample_id", "output", "true_label", "predicted_label")
    list_filter = ("output__experiment", "output")
    search_fields = ("sample_id",)
    list_select_related = ("output__experiment",)


@admin.register(RegressionPrediction)
class RegressionPredictionAdmin(admin.ModelAdmin):
    list_display = ("sample_id", "output", "true_label", "predicted_label")
    list_filter = ("output__experiment", "output")
    search_fields = ("sample_id",)
    list_select_related = ("output__experiment",)


@admin.register(HistoryEntry)
class HistoryEntryAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "action", "project", "experiment", "analyst")
    list_filter = ("action", "project")
    search_fields = ("details",)
    readonly_fields = ("timestamp",)