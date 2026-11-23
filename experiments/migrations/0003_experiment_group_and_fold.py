import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0002_experiment_unique_experiment_name_per_project_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="group_name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="experiment",
            name="fold",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="experiment",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("group_name"),
                models.F("fold"),
                models.F("project"),
                condition=models.Q(("fold__isnull", False)),
                name="unique_fold_per_group",
            ),
        ),
    ]
