from django.urls import path, include
from .views import project_views



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
         name="project_delete")

]

