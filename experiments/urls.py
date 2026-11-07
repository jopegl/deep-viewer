from django.urls import path

from . import views

urlpatterns = [
    path("experiments/<int:pk>/import/", views.import_upload, name="experiment_import"),
    path("experiments/<int:pk>/import/columns/", views.import_mapping, name="experiment_import_mapping"),
]