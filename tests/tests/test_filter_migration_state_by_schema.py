import pytest
from django.db import connection
from django.db.migrations.migration import Migration
from django.db.migrations.operations import AddField
from django.db.migrations.state import ProjectState
from django.db.models import IntegerField
from django_tenants.utils import get_tenant_database_alias
from pytest_django.fixtures import SettingsWrapper

from django_tenants_smart_executor.executors import (
    LimitStateToSchema,
    filter_migration_state_by_schema,
    maybe_filter_migration_state_by_schema,
)


def _make_migration(app_label: str) -> Migration:
    migration = Migration("0001_test", app_label)
    # `model_name` doesn't exist in an empty `ProjectState`, so calling `state_forwards` for this
    # operation (unless skipped) blows up with a `KeyError`, letting us prove whether it actually ran.
    migration.operations = [
        AddField(model_name="does_not_exist", name="some_field", field=IntegerField(default=0)),
    ]
    return migration


@pytest.fixture(autouse=True)
def restore_schema():
    yield
    connection.set_schema_to_public()


@pytest.mark.django_db
class TestFilterMigrationStateBySchema:
    def test_skips_mutate_state_for_app_not_allowed_on_public_schema(self):
        connection.set_schema_to_public()
        migration = _make_migration("tenant_app")  # only in TENANT_APPS

        with filter_migration_state_by_schema(database=get_tenant_database_alias()):
            result = migration.mutate_state(ProjectState(), preserve=True)

        assert result.models == {}

    def test_skips_apply_for_app_not_allowed_on_public_schema(self):
        connection.set_schema_to_public()
        migration = _make_migration("tenant_app")  # only in TENANT_APPS

        with filter_migration_state_by_schema(database=get_tenant_database_alias()):
            state = ProjectState()
            result = migration.apply(state, schema_editor=None)

        assert result is state

    def test_does_not_skip_mutate_state_for_app_allowed_on_public_schema(self):
        connection.set_schema_to_public()
        migration = _make_migration("public_app")  # in SHARED_APPS

        with filter_migration_state_by_schema(database=get_tenant_database_alias()), pytest.raises(KeyError):
            migration.mutate_state(ProjectState(), preserve=True)

    def test_skips_mutate_state_for_app_not_allowed_on_tenant_schema(self):
        connection.set_schema("tenant_schema", include_public=False)
        migration = _make_migration("public_app")  # only in SHARED_APPS

        with filter_migration_state_by_schema(database=get_tenant_database_alias()):
            result = migration.mutate_state(ProjectState(), preserve=True)

        assert result.models == {}

    def test_does_not_skip_mutate_state_for_app_allowed_on_tenant_schema(self):
        connection.set_schema("tenant_schema", include_public=False)
        migration = _make_migration("tenant_app")  # in TENANT_APPS

        with filter_migration_state_by_schema(database=get_tenant_database_alias()), pytest.raises(KeyError):
            migration.mutate_state(ProjectState(), preserve=True)

    def test_without_filter_mutate_state_raises_for_any_app(self):
        # Sanity check: without the filter active, `state_forwards` always runs, regardless of schema.
        connection.set_schema_to_public()
        migration = _make_migration("tenant_app")

        with pytest.raises(KeyError):
            migration.mutate_state(ProjectState(), preserve=True)


@pytest.mark.django_db
class TestMaybeFilterMigrationStateBySchema:
    def test_no_setting_never_filters(self, settings: SettingsWrapper):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = None
        connection.set_schema_to_public()
        migration = _make_migration("tenant_app")

        with maybe_filter_migration_state_by_schema(is_public=True), pytest.raises(KeyError):
            migration.mutate_state(ProjectState(), preserve=True)

    def test_full_filters_on_public(self, settings: SettingsWrapper):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = LimitStateToSchema.FULL
        connection.set_schema_to_public()
        migration = _make_migration("tenant_app")  # only in TENANT_APPS

        with maybe_filter_migration_state_by_schema(is_public=True):
            result = migration.mutate_state(ProjectState(), preserve=True)

        assert result.models == {}

    def test_full_filters_on_tenant(self, settings: SettingsWrapper):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = LimitStateToSchema.FULL
        connection.set_schema("tenant_schema", include_public=False)
        migration = _make_migration("public_app")  # only in SHARED_APPS

        with maybe_filter_migration_state_by_schema(is_public=False):
            result = migration.mutate_state(ProjectState(), preserve=True)

        assert result.models == {}

    def test_public_filters_on_public(self, settings: SettingsWrapper):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = LimitStateToSchema.PUBLIC
        connection.set_schema_to_public()
        migration = _make_migration("tenant_app")  # only in TENANT_APPS

        with maybe_filter_migration_state_by_schema(is_public=True):
            result = migration.mutate_state(ProjectState(), preserve=True)

        assert result.models == {}

    def test_public_does_not_filter_on_tenant(self, settings: SettingsWrapper):
        # `LimitStateToSchema.PUBLIC` must keep the full state while migrating tenant schemas, so that
        # `TENANT_APPS` models with a `ForeignKey` to a `SHARED_APPS` model still resolve.
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = LimitStateToSchema.PUBLIC
        connection.set_schema("tenant_schema", include_public=False)
        migration = _make_migration("public_app")  # only in SHARED_APPS

        with maybe_filter_migration_state_by_schema(is_public=False), pytest.raises(KeyError):
            migration.mutate_state(ProjectState(), preserve=True)

    def test_tenant_filters_on_tenant(self, settings: SettingsWrapper):
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = LimitStateToSchema.TENANT
        connection.set_schema("tenant_schema", include_public=False)
        migration = _make_migration("public_app")  # only in SHARED_APPS

        with maybe_filter_migration_state_by_schema(is_public=False):
            result = migration.mutate_state(ProjectState(), preserve=True)

        assert result.models == {}

    def test_tenant_does_not_filter_on_public(self, settings: SettingsWrapper):
        # `LimitStateToSchema.TENANT` must keep the full state while migrating the public schema, so
        # that `SHARED_APPS` models with a `ForeignKey` to a `TENANT_APPS` model still resolve.
        settings.SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = LimitStateToSchema.TENANT
        connection.set_schema_to_public()
        migration = _make_migration("tenant_app")  # only in TENANT_APPS

        with maybe_filter_migration_state_by_schema(is_public=True), pytest.raises(KeyError):
            migration.mutate_state(ProjectState(), preserve=True)
