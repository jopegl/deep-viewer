from django.urls import path, include
from .views import project_views, import_views, experiment_views



urlpatterns = [
    
     path('projects/', 
         project_views.ProjectListView.as_view(), 
         name= "project_list"
         ),

     path('projects/create/', 
         project_views.ProjectCreateView.as_view(), 
         name="project_create"),

     path('projects/<int:pk>/delete/', 
         project_views.ProjectDeleteView.as_view(), 
         name="project_delete"),

     path('projects/<int:pk>/update/', 
          project_views.ProjectUpdateView.as_view(), 
          name="project_update"),

     path('projects/<int:pk>/experiments/', 
          experiment_views.ExperimentListView.as_view(), 
          name="experiment_list"),

     path('projects/<int:pk>/experiments/create/', 
          experiment_views.ExperimentCreateView.as_view(),
          name="experiment_create"),

     path("experiments/<int:pk>/delete/", 
          experiment_views.ExperimentDeleteView.as_view(), 
          name="experiment_delete"),

     path("experiments/<int:pk>/import/", import_views.import_upload, name="experiment_import"),

     path("experiments/<int:pk>/import/tasks/", import_views.import_tasks, name="experiment_import_tasks"),

     path("experiments/<int:pk>/import/columns/", import_views.import_mapping, name="experiment_import_mapping"),

]

