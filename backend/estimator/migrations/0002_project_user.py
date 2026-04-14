from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def delete_projects_without_user(apps, schema_editor):
    Project = apps.get_model("estimator", "Project")
    Project.objects.filter(user__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("estimator", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="user",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="estimator_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(delete_projects_without_user, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="project",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="estimator_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
