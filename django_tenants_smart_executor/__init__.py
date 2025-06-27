from __future__ import annotations

__all__ = ["load_executor", "SmartMultiprocessingExecutor", "SmartStandardExecutor"]


import django_tenants.migration_executors

from .executors import (
    SmartMultiprocessingExecutor,
    SmartStandardExecutor,
)


def load_executor(codename: str | None) -> type[django_tenants.migration_executors.MigrationExecutor]:
    """
    A function to be set in GET_EXECUTOR_FUNCTION, which loads an executor for django-tenants.
    """
    if codename == "standard" or codename is None:
        return SmartStandardExecutor

    if codename == "multiprocessing":
        return SmartMultiprocessingExecutor

    raise ValueError(f"Unknown executor {codename}")
