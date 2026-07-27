import pytest

from tests.test_project.public_app.models import Client


@pytest.mark.django_db
class TestCreateTenant:
    def test_create_tenant_default(self, settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = None

        Client.objects.create(name="Default", schema_name="default")

    def test_create_tenant_skip_state_full(self, settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "full"

        Client.objects.create(name="Skip", schema_name="skip")
