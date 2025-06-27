from django.apps import AppConfig


class TenantAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.test_project.tenant_app"
