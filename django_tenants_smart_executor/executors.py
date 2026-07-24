from __future__ import annotations

__all__ = [
    "SmartStandardExecutor",
    "SmartMultiprocessingExecutor",
    "LimitStateToSchema",
]

import enum
import functools
import logging
import multiprocessing
from collections.abc import Iterable
from contextlib import AbstractContextManager, ContextDecorator, nullcontext
from typing import Any

import django_tenants.migration_executors
from django.conf import settings
from django.db import connection, connections, router
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.migration import Migration
from django.db.migrations.recorder import MigrationRecorder
from django_tenants.migration_executors.base import run_migrations
from django_tenants.signals import schema_migrated
from django_tenants.utils import get_tenant_database_alias

try:
    from django_tenants.migration_executors.multiproc import get_pool
except ImportError:  # get_pool is only available 3.10.2+

    def get_pool():
        processes = getattr(settings, "TENANT_MULTIPROCESSING_MAX_PROCESSES", 4)
        return multiprocessing.Pool(processes=processes)


logger = logging.getLogger("django_tenants_smart_executor")


class schema_context_without_public(ContextDecorator):  # noqa: N801
    """
    Like schema_context, but without public schema.
    """

    def __init__(self, *args, **kwargs):
        self.schema_name = args[0]
        self.database = kwargs.get("database", get_tenant_database_alias())
        super().__init__()

    def __enter__(self):
        self.connection = connections[self.database]
        self.previous_tenant = connection.tenant
        self.connection.set_schema(self.schema_name, include_public=False)

    def __exit__(self, *exc):
        if self.previous_tenant is None:
            self.connection.set_schema_to_public()
        else:
            self.connection.set_tenant(self.previous_tenant)


def needs_migrations(nodes: set[tuple[str, str]], schema_name: str, options: dict) -> bool:
    """
    Returns whether we need to run migrations for a given schema.
    If running migrations on a specific app/label, always run migrations.
    Otherwise, compare already applied migrations to currently existing migrations (passed in `nodes`).
    """
    if options["app_label"] or options["migration_name"]:  # need specific app/label -> migrate everything
        return True

    migrated_already: set[tuple[str, str]]

    # need to exclude public schema so if there's no migration table it doesn't pick up the one in public
    with schema_context_without_public(schema_name):
        migration_recorder = MigrationRecorder(connection=connection)
        if not migration_recorder.has_table():
            return True
        migrated_already = set(migration_recorder.applied_migrations().keys())

        for node in nodes:
            if node not in migrated_already:
                return True

    return False


def trigger_signals(schema_name: str) -> None:
    """
    Send the signals even with no migrations!
    """
    logger.warning("No migrations needed for schema %s, only triggering signals", schema_name)
    schema_migrated.send(None, schema_name=schema_name)


class LimitStateToSchema(enum.Enum):
    """
    Valid values for the `SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA` setting (see `filter_migration_state_by_schema`).
    The default, when the setting is unset (`None`), is to not limit anything.

    - `public`: skip obsolete state building migrating public schema. Unsafe if the public schema has
                `ForeignKey`s to tenant schemas.
    - `tenant`: skip obsolete state building migrating tenant schemas. Unsafe if the tenant schemas have
                `ForeignKey`s to public schema.
    - `full`: skip obsolete state building migrating all schemas. Unsafe if there are `ForeignKey`s
              between schemas.
    """

    FULL = "full"
    PUBLIC = "public"
    TENANT = "tenant"


class filter_migration_state_by_schema(ContextDecorator):  # noqa: N801
    """
    While active, skips building/mutating the in-memory `ProjectState` (i.e. `Migration.apply` and
    `Migration.mutate_state`, which call each operation's `state_forwards`, e.g.
    `AddField.state_forwards` -> `ProjectState.add_field`) for migrations whose app isn't allowed to
    migrate on the current schema, as determined by the configured database routers (e.g.
    `TenantSyncRouter`).

    Django always builds the full historical model state for every migration on every run, even
    though the router already prevents the actual SQL (`database_forwards`) from running for apps that
    don't belong to the current schema. Building that state can be a substantial part of the total
    migration time and is entirely unnecessary for a schema that will never contain that app's tables.

    Enabled via the `SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA` setting (see `LimitStateToSchema` for the
    available options and their cross-schema-dependency caveats).
    """

    def __init__(self, database: str | None = None):
        self.database = database or get_tenant_database_alias()

    def _is_allowed(self, app_label: str) -> bool:
        return router.allow_migrate(self.database, app_label)

    def __enter__(self):
        self.original_mutate_state = Migration.mutate_state
        self.original_apply = Migration.apply

        is_allowed = self._is_allowed
        original_mutate_state = self.original_mutate_state
        original_apply = self.original_apply

        def mutate_state(migration, project_state, preserve=True):
            if not is_allowed(migration.app_label):
                return project_state.clone() if preserve else project_state
            return original_mutate_state(migration, project_state, preserve=preserve)

        def apply(migration, project_state, schema_editor, collect_sql=False):
            if not is_allowed(migration.app_label):
                return project_state
            return original_apply(migration, project_state, schema_editor, collect_sql=collect_sql)

        Migration.mutate_state = mutate_state
        Migration.apply = apply

        return self

    def __exit__(self, *exc):
        Migration.mutate_state = self.original_mutate_state
        Migration.apply = self.original_apply


def maybe_filter_migration_state_by_schema(*, is_public: bool, database: str | None = None) -> AbstractContextManager:
    """
    Returns `filter_migration_state_by_schema` if enabled for the schema currently being migrated (as
    determined by `is_public` and the `SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA` setting), otherwise a
    no-op context manager.
    """
    limit_to: LimitStateToSchema | None = getattr(settings, "SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA", None)

    if limit_to is None:
        return nullcontext()

    if limit_to == LimitStateToSchema.FULL:
        return filter_migration_state_by_schema(database)

    if limit_to == LimitStateToSchema.PUBLIC and is_public:
        return filter_migration_state_by_schema(database)

    if limit_to == LimitStateToSchema.TENANT and not is_public:
        return filter_migration_state_by_schema(database)

    return nullcontext()


class NeedsMigrationsMixin(django_tenants.migration_executors.MigrationExecutor):
    """
    Shared functionality.
    """

    def get_all_nodes(self) -> set[tuple[str, str]]:
        executor = MigrationExecutor(connection, lambda *args, **kwargs: None)
        return set(executor.loader.graph.nodes.keys())

    def run_public(self, nodes: set[tuple[str, str]], tenants: list[str]) -> None:
        if self.PUBLIC_SCHEMA_NAME in tenants:
            if needs_migrations(nodes, self.PUBLIC_SCHEMA_NAME, self.options):
                with maybe_filter_migration_state_by_schema(is_public=True):
                    run_migrations(self.args, self.options, self.codename, self.PUBLIC_SCHEMA_NAME)
            else:
                trigger_signals(self.PUBLIC_SCHEMA_NAME)
            tenants.pop(tenants.index(self.PUBLIC_SCHEMA_NAME))


class SmartStandardExecutor(NeedsMigrationsMixin, django_tenants.migration_executors.StandardExecutor):
    """
    Sequential order of migrations, run public schema and then all schemas. Check if the migrations need to run fist.
    """

    def run_migrations(self, tenants: list[str] | None = None) -> None:
        nodes = self.get_all_nodes()

        tenants = tenants or []

        self.run_public(nodes, tenants)

        for idx, schema_name in enumerate(tenants):
            if needs_migrations(nodes, schema_name, self.options):
                with maybe_filter_migration_state_by_schema(is_public=False):
                    run_migrations(self.args, self.options, self.codename, schema_name, idx=idx, count=len(tenants))
            else:
                trigger_signals(schema_name)


def run_migrations_percent(
    args: Iterable,
    options: dict,
    codename: str,
    count: int,
    nodes: set[tuple[str, str]],
    idx_schema_name: tuple[int, str],
) -> Any:
    """
    A inner function for multiprocessing Pool in multiprocessing executor, check if need to run migrations and run
    them, or trigger signals.
    """
    idx, schema_name = idx_schema_name

    if needs_migrations(nodes, schema_name, options):
        with maybe_filter_migration_state_by_schema(is_public=False):
            return run_migrations(args, options, codename, schema_name, allow_atomic=False, idx=idx, count=count)
    else:
        trigger_signals(schema_name)
        return None


class SmartMultiprocessingExecutor(NeedsMigrationsMixin, django_tenants.migration_executors.MultiprocessingExecutor):
    """
    Parallel migrations, run public schema first and then all schemas in parallel.
    Checks if the migrations need to run fist.
    """

    def run_migrations(self, tenants: list[str] | None = None) -> None:
        nodes = self.get_all_nodes()

        tenants = tenants or []
        self.run_public(nodes, tenants)

        if tenants:
            chunks = getattr(settings, "TENANT_MULTIPROCESSING_CHUNKS", 2)

            from django.db import connections

            con = connections[self.TENANT_DB_ALIAS]
            con.close()
            con.connection = None

            run_migrations_p = functools.partial(
                run_migrations_percent, self.args, self.options, self.codename, len(tenants), nodes
            )
            p = get_pool()
            p.map(run_migrations_p, enumerate(tenants), chunks)
