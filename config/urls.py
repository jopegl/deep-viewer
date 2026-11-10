from django.contrib import admin
from django.urls import path, include
from accounts.views import admin_redirect

urlpatterns = [
    path("admin/login/", admin_redirect),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path("accounts/", include("django.contrib.auth.urls")),
    path('', include("experiments.urls")),
    path('', include('analyses.urls'))
]
