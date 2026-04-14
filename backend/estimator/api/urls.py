from django.urls import path

from estimator.api import views

urlpatterns = [
    path("calculate-fp/", views.CalculateFPView.as_view(), name="calculate-fp"),
    path("calculate-cocomo/", views.CalculateCOCOMOView.as_view(), name="calculate-cocomo"),
    path("projects/", views.ProjectListCreateView.as_view(), name="projects"),
    path("export-pdf/<int:project_id>/", views.ExportProjectPDFView.as_view(), name="export-pdf"),
    path("meta/", views.GSCMetaView.as_view(), name="meta"),
]
