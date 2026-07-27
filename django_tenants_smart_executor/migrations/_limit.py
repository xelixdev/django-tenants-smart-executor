import logging

from django.conf import settings
from django_tenants.utils import app_labels

from django_tenants_smart_executor.executors import MIGRATING_TENANT

logger = logging.getLogger("django_tenants_smart_executor.migrations")


def should_limit_state_apply(migration_type: str, app_label: str) -> bool:
    """
    Figure out whether the migration should limit the state apply, because it's a migration from a irrelevant app
    for the current schema. The schema we are applying is determined by MIGRATING_TENANT.
    :param migration_type: The name of migration for logs
    :param app_label: The label of the app that is being migrated
    :return: Boolean, whether it should be ignored
    """

    state_limit = getattr(settings, "SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA", None)
    state_exceptions = getattr(settings, "SMART_EXECUTOR_LIMIT_STATE_EXCEPTIONS_MAP", {})
    migrating_tenant = MIGRATING_TENANT.get()

    if (
        (
            state_limit in ("public", "full")
            and migrating_tenant is False
            and app_label not in app_labels(settings.SHARED_APPS)
        )
        or (
            state_limit in ("tenant", "full")
            and migrating_tenant is True
            and app_label not in app_labels(settings.TENANT_APPS)
        )
    ) and app_label not in state_exceptions.get(migrating_tenant, set()):
        logger.info(
            "State limit is set to %s, running on %s schema, ignoring %s on %s",
            state_limit,
            "tenant" if migrating_tenant else "public",
            migration_type,
            app_label,
        )
        return True
    return False
