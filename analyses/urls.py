from django.urls import path

from . import views

urlpatterns = [
    path("experiments/<int:pk>/results/", views.experiment_results, name="experiment_results"),
]