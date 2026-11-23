from django.urls import path

from . import views

urlpatterns = [
    path("experiments/<int:pk>/results/", views.experiment_results, name="experiment_results"),
    path("experiments/<int:pk>/export/metrics/", views.export_metrics, name="experiment_export_metrics"),
    path("experiments/<int:pk>/export/predictions/", views.export_predictions, name="experiment_export_predictions"),
    path("projects/<int:pk>/ranking/", views.project_ranking, name="project_ranking"),
]