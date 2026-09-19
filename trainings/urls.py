from django.urls import path

from . import views

urlpatterns = [
    path("projects/<int:project_id>/measurement-types/", views.measurement_type_list, name="measurement_type_list"),
    path("projects/<int:project_id>/measurement-types/new/", views.measurement_type_create, name="measurement_type_create"),
    path("projects/<int:project_id>/measurement-types/<int:measurement_type_id>/delete/", views.measurement_type_delete, name="measurement_type_delete"),

    path("projects/<int:project_id>/experiments/<int:experiment_id>/log-files/", views.log_file_list, name="log_file_list"),
    path("projects/<int:project_id>/experiments/<int:experiment_id>/log-files/new/", views.log_file_create, name="log_file_create"),
    path("projects/<int:project_id>/experiments/<int:experiment_id>/log-files/<int:log_file_id>/delete/", views.log_file_delete, name="log_file_delete"),

    path("projects/<int:project_id>/experiments/<int:experiment_id>/sample-files/", views.sample_measurement_file_list, name="sample_measurement_file_list"),
    path("projects/<int:project_id>/experiments/<int:experiment_id>/sample-files/new/", views.sample_measurement_file_create, name="sample_measurement_file_create"),
    path("projects/<int:project_id>/experiments/<int:experiment_id>/sample-files/<int:sample_file_id>/delete/", views.sample_measurement_file_delete, name="sample_measurement_file_delete"),
]