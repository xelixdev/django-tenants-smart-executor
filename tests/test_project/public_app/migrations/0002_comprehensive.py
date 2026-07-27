import django.db.models.deletion
from django.db import models

from django_tenants_smart_executor import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("public_app", "0001_initial"),
    ]

    operations = [
        # CreateModel
        migrations.CreateModel(
            name="PublicExtra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("value", models.IntegerField(default=0)),
            ],
        ),
        # CreateModel (will be used for DeleteModel and RenameModel)
        migrations.CreateModel(
            name="PublicToDelete",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="PublicToRename",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ],
        ),
        # AlterModelTable
        migrations.AlterModelTable(
            name="PublicExtra",
            table="public_app_extra_custom",
        ),
        # AlterModelTableComment
        migrations.AlterModelTableComment(
            name="PublicExtra",
            table_comment="Extra public records",
        ),
        # AlterModelOptions
        migrations.AlterModelOptions(
            name="PublicExtra",
            options={"ordering": ["name"]},
        ),
        # AddField
        migrations.AddField(
            model_name="PublicExtra",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        # AddField (order_by field for AlterOrderWithRespectTo)
        migrations.AddField(
            model_name="PublicExtra",
            name="client",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="public_app.client",
            ),
        ),
        # AlterField
        migrations.AlterField(
            model_name="PublicExtra",
            name="name",
            field=models.CharField(max_length=200),
        ),
        # RenameField
        migrations.RenameField(
            model_name="PublicExtra",
            old_name="value",
            new_name="score",
        ),
        # AddIndex
        migrations.AddIndex(
            model_name="PublicExtra",
            index=models.Index(fields=["name"], name="public_extra_name_idx"),
        ),
        # RemoveIndex
        migrations.RemoveIndex(
            model_name="PublicExtra",
            name="public_extra_name_idx",
        ),
        # RenameIndex (need an index to rename)
        migrations.AddIndex(
            model_name="PublicExtra",
            index=models.Index(fields=["score"], name="public_extra_score_idx"),
        ),
        migrations.RenameIndex(
            model_name="PublicExtra",
            old_name="public_extra_score_idx",
            new_name="public_extra_score_renamed_idx",
        ),
        # AddConstraint
        migrations.AddConstraint(
            model_name="PublicExtra",
            constraint=models.CheckConstraint(condition=models.Q(score__gte=0), name="public_extra_score_non_negative"),
        ),
        # AlterConstraint
        migrations.AlterConstraint(
            model_name="PublicExtra",
            name="public_extra_score_non_negative",
            constraint=models.CheckConstraint(condition=models.Q(score__gte=0), name="public_extra_score_non_negative"),
        ),
        # RemoveConstraint
        migrations.RemoveConstraint(
            model_name="PublicExtra",
            name="public_extra_score_non_negative",
        ),
        # AlterUniqueTogether
        migrations.AlterUniqueTogether(
            name="PublicExtra",
            unique_together={("name", "score")},
        ),
        # AlterIndexTogether
        migrations.AlterIndexTogether(
            name="PublicExtra",
            index_together={("name", "description")},
        ),
        # AlterOrderWithRespectTo
        migrations.AlterOrderWithRespectTo(
            name="PublicExtra",
            order_with_respect_to="client",
        ),
        # AlterModelManagers
        migrations.AlterModelManagers(
            name="PublicExtra",
            managers=[],
        ),
        # RemoveField
        migrations.RemoveField(
            model_name="PublicExtra",
            name="description",
        ),
        # RenameModel
        migrations.RenameModel(
            old_name="PublicToRename",
            new_name="PublicRenamed",
        ),
        # DeleteModel
        migrations.DeleteModel(
            name="PublicToDelete",
        ),
        # Cleanup
        migrations.AlterUniqueTogether(
            name="publicextra",
            unique_together=None,
        ),
        migrations.RemoveIndex(
            model_name="publicextra",
            name="public_extra_score_renamed_idx",
        ),
        migrations.DeleteModel(
            name="PublicRenamed",
        ),
        migrations.DeleteModel(
            name="PublicExtra",
        ),
    ]
