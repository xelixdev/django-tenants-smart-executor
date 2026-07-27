from django.db import models

from django_tenants_smart_executor import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tenant_app", "0001_initial"),
    ]

    operations = [
        # CreateModel
        migrations.CreateModel(
            name="TenantExtra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("value", models.IntegerField(default=0)),
            ],
        ),
        # CreateModel (will be used for DeleteModel and RenameModel)
        migrations.CreateModel(
            name="TenantToDelete",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="TenantToRename",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ],
        ),
        # CreateModel (will be used for AlterOrderWithRespectTo)
        migrations.CreateModel(
            name="TenantParent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ],
        ),
        # AlterModelTable
        migrations.AlterModelTable(
            name="TenantExtra",
            table="tenant_app_extra_custom",
        ),
        # AlterModelTableComment
        migrations.AlterModelTableComment(
            name="TenantExtra",
            table_comment="Extra tenant records",
        ),
        # AlterModelOptions
        migrations.AlterModelOptions(
            name="TenantExtra",
            options={"ordering": ["name"]},
        ),
        # AddField
        migrations.AddField(
            model_name="TenantExtra",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        # AddField (FK for AlterOrderWithRespectTo)
        migrations.AddField(
            model_name="TenantExtra",
            name="parent",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=models.deletion.SET_NULL,
                to="tenant_app.tenantparent",
            ),
        ),
        # AlterField
        migrations.AlterField(
            model_name="TenantExtra",
            name="name",
            field=models.CharField(max_length=200),
        ),
        # RenameField
        migrations.RenameField(
            model_name="TenantExtra",
            old_name="value",
            new_name="score",
        ),
        # AddIndex
        migrations.AddIndex(
            model_name="TenantExtra",
            index=models.Index(fields=["name"], name="tenant_extra_name_idx"),
        ),
        # RemoveIndex
        migrations.RemoveIndex(
            model_name="TenantExtra",
            name="tenant_extra_name_idx",
        ),
        # RenameIndex
        migrations.AddIndex(
            model_name="TenantExtra",
            index=models.Index(fields=["score"], name="tenant_extra_score_idx"),
        ),
        migrations.RenameIndex(
            model_name="TenantExtra",
            old_name="tenant_extra_score_idx",
            new_name="tenant_extra_score_renamed_idx",
        ),
        # AddConstraint
        migrations.AddConstraint(
            model_name="TenantExtra",
            constraint=models.CheckConstraint(condition=models.Q(score__gte=0), name="tenant_extra_score_non_negative"),
        ),
        # AlterConstraint
        migrations.AlterConstraint(
            model_name="TenantExtra",
            name="tenant_extra_score_non_negative",
            constraint=models.CheckConstraint(condition=models.Q(score__gte=0), name="tenant_extra_score_non_negative"),
        ),
        # RemoveConstraint
        migrations.RemoveConstraint(
            model_name="TenantExtra",
            name="tenant_extra_score_non_negative",
        ),
        # AlterUniqueTogether
        migrations.AlterUniqueTogether(
            name="TenantExtra",
            unique_together={("name", "score")},
        ),
        # AlterIndexTogether
        migrations.AlterIndexTogether(
            name="TenantExtra",
            index_together={("name", "description")},
        ),
        # AlterOrderWithRespectTo
        migrations.AlterOrderWithRespectTo(
            name="TenantExtra",
            order_with_respect_to="parent",
        ),
        # AlterModelManagers
        migrations.AlterModelManagers(
            name="TenantExtra",
            managers=[],
        ),
        # RemoveField
        migrations.RemoveField(
            model_name="TenantExtra",
            name="description",
        ),
        # RenameModel
        migrations.RenameModel(
            old_name="TenantToRename",
            new_name="TenantRenamed",
        ),
        # DeleteModel
        migrations.DeleteModel(
            name="TenantToDelete",
        ),
        # Cleanup
        migrations.AlterUniqueTogether(
            name="tenantextra",
            unique_together=None,
        ),
        migrations.RemoveIndex(
            model_name="tenantextra",
            name="tenant_extra_score_renamed_idx",
        ),
        migrations.DeleteModel(
            name="TenantRenamed",
        ),
        migrations.DeleteModel(
            name="TenantExtra",
        ),
        migrations.DeleteModel(
            name="TenantParent",
        ),
    ]
