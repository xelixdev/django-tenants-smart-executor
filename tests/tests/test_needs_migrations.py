import pytest
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from django_tenants_smart_executor.executors import needs_migrations


@pytest.mark.django_db
class TestNeedsMigrations:
    @pytest.fixture
    def nodes(self) -> set[tuple[str, str]]:
        return set(MigrationRecorder(connection=connection).applied_migrations().keys())

    def test_needs_migrations_identical(self, nodes: set[tuple[str, str]]):
        assert needs_migrations(nodes, "public", {"app_label": None, "migration_name": None}) is False

        # if specific app or migration need to run migrations
        assert needs_migrations(nodes, "public", {"app_label": "a", "migration_name": None}) is True
        assert needs_migrations(nodes, "public", {"app_label": None, "migration_name": "a"}) is True

    def test_something_not_migrated(self, nodes: set[tuple[str, str]]):
        assert needs_migrations(nodes | {("a", "b")}, "public", {"app_label": None, "migration_name": None}) is True
