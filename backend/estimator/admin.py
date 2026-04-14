from django.contrib import admin

from estimator.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "fp", "effort_pm", "tdev_months", "updated_at")
    search_fields = ("name",)
