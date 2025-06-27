from __future__ import annotations

__all__ = [
    "SmartStandardExecutor",
    "SmartMultiprocessingExecutor",
]


import functools
import logging
import multiprocessing
from collections.abc import Iterable
from typing import Any

import django_tenants.migration_executors
from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder
from django_tenants.migration_executors.base import run_migrations
from django_tenants.signals import schema_migrated
from django_tenants.utils import schema_context

logger = logging.getLogger("django_tenants_smart_executor")


def needs_migrations(nodes: set[tuple[str, str]], schema_name: str, options: dict) -> bool:
    """
    Returns whether we need to run migrations for a given schema.
    If running migrations on a specific app/label, always run migrations.
    Otherwise, compare already applied migrations to currently existing migrations (passed in `nodes`).
    """
    if options["app_label"] or options["migration_name"]:  # need specific app/label -> migrate everything
        return True

    migrated_already: set[tuple[str, str]]

    with schema_context(schema_name):
        migrated_already = set(MigrationRecorder(connection=connection).applied_migrations().keys())

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
        return run_migrations(args, options, codename, schema_name, allow_atomic=False, idx=idx, count=count)
    else:
        return trigger_signals(schema_name)


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
            processes = getattr(settings, "TENANT_MULTIPROCESSING_MAX_PROCESSES", 4)
            chunks = getattr(settings, "TENANT_MULTIPROCESSING_CHUNKS", 2)

            from django.db import connections

            con = connections[self.TENANT_DB_ALIAS]
            con.close()
            con.connection = None

            run_migrations_p = functools.partial(
                run_migrations_percent, self.args, self.options, self.codename, len(tenants), nodes
            )
            p = multiprocessing.Pool(processes=processes)
            p.map(run_migrations_p, enumerate(tenants), chunks)
