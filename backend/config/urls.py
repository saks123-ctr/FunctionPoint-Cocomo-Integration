from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from estimator.api.views import CalculateCOCOMOView, CalculateFPView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("calculate-fp/", CalculateFPView.as_view()),
    path("calculate-cocomo/", CalculateCOCOMOView.as_view()),
    path("api/", include("estimator.api.urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="dashboard"),
]
