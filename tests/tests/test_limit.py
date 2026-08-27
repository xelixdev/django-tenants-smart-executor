import pytest
from pytest_django import Settings

from django_tenants_smart_executor.executors import MIGRATING_TENANT
from django_tenants_smart_executor.migrations._limit import should_limit_state_apply


@pytest.fixture(autouse=True)
def reset_migrating_tenant():
    token = MIGRATING_TENANT.set(False)
    yield
    MIGRATING_TENANT.reset(token)


class TestShouldLimitStateApply:
    def test_no_limit_configured(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = None

        MIGRATING_TENANT.set(False)
        assert should_limit_state_apply("migrate", "tenant_app") is False

        MIGRATING_TENANT.set(True)
        assert should_limit_state_apply("migrate", "public_app") is False

    def test_unknown_limit_value_is_ignored(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "unknown"

        MIGRATING_TENANT.set(False)
        assert should_limit_state_apply("migrate", "tenant_app") is False

    def test_public_limit_blocks_non_shared_app_on_public_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "public"
        MIGRATING_TENANT.set(False)

        assert should_limit_state_apply("migrate", "tenant_app") is True

    def test_public_limit_allows_shared_app_on_public_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "public"
        MIGRATING_TENANT.set(False)

        assert should_limit_state_apply("migrate", "public_app") is False

    def test_public_limit_does_not_apply_on_tenant_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "public"
        MIGRATING_TENANT.set(True)

        assert should_limit_state_apply("migrate", "tenant_app") is False

    def test_public_limit_respects_exceptions_map(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "public"
        settings.SMART_EXECUTOR_LIMIT_STATE_EXCEPTIONS_MAP = {False: ["tenant_app"], True: []}
        MIGRATING_TENANT.set(False)

        assert should_limit_state_apply("migrate", "tenant_app") is False

    def test_tenant_limit_blocks_non_tenant_app_on_tenant_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "tenant"
        MIGRATING_TENANT.set(True)

        assert should_limit_state_apply("migrate", "public_app") is True

    def test_tenant_limit_allows_tenant_app_on_tenant_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "tenant"
        MIGRATING_TENANT.set(True)

        assert should_limit_state_apply("migrate", "tenant_app") is False

    def test_tenant_limit_does_not_apply_on_public_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "tenant"
        MIGRATING_TENANT.set(False)

        assert should_limit_state_apply("migrate", "public_app") is False

    def test_tenant_limit_respects_exceptions_map(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "tenant"
        settings.SMART_EXECUTOR_LIMIT_STATE_EXCEPTIONS_MAP = {False: [], True: ["public_app"]}
        MIGRATING_TENANT.set(True)

        assert should_limit_state_apply("migrate", "public_app") is False

    def test_full_limit_blocks_non_shared_app_on_public_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "full"
        MIGRATING_TENANT.set(False)

        assert should_limit_state_apply("migrate", "tenant_app") is True

    def test_full_limit_blocks_non_tenant_app_on_tenant_schema(self, settings: Settings):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "full"
        MIGRATING_TENANT.set(True)

        assert should_limit_state_apply("migrate", "public_app") is True
