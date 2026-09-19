from django.urls import path

from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("new/", views.project_create, name="project_create"),
    path("<int:project_id>/experiments/", views.experiment_list, name="experiment_list"),
    path("<int:project_id>/experiments/new/", views.experiment_create, name="experiment_create"),
]