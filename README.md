# Django Tenants Smart Executor

When using [django-tenants](https://github.com/django-tenants/django-tenants), migrations can be quite slow when you have a lot of tenants.
This is the case even if there are actually no migrations to run.
This package provides executors that skip running the migrations for a tenant if there are no migrations to run.
If there's no migratuons to run, the `schema_migrated` signal is still triggered.

## Installation

Install using pip (or your package manager of choice):
```bash
pip install django-tenants-smart-executor
```

And configure the `GET_EXECUTOR_FUNCTION` in your `settings.py`:
```python
GET_EXECUTOR_FUNCTION = "django_tenants_smart_executor.load_executor"
```

## Usage

When you run migrations when all tenants are migrated, the output will look something like this:

```bash
$ python manage.py migrate_schemas
No migrations needed for schema public, only triggering signals
No migrations needed for schema test, only triggering signals
```

The multiprocessing executor is also supported.

```bash
$ python manage.py migrate_schemas --executor multiprocessing
No migrations needed for schema public, only triggering signals
No migrations needed for schema test, only triggering signals
```

## Limiting model state to the current schema

Even when there's nothing to run, and even for migrations that don't apply any SQL to the current
schema (because `django-tenants`' `TenantSyncRouter` blocks them), Django still rebuilds its
in-memory model state (`ProjectState`) for every migration of every app in `INSTALLED_APPS`. This
can be a significant and completely unnecessary cost when running migrations against a lot of
tenants.

Set `SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA` in your `settings.py` to a `django_tenants_smart_executor.LimitStateToSchema`
value to skip building that state for migrations belonging to an app that isn't allowed to migrate
on the schema currently being migrated. The setting defaults to `None`, which doesn't limit
anything.

```python
from django_tenants_smart_executor import LimitStateToSchema

SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = LimitStateToSchema.FULL
```

The available options are:

| Option   | Skips state while migrating | Safe with `ForeignKey`s from... |
|----------|------------------------------|----------------------------------|
| `FULL`   | public schema and tenant schemas | neither direction (no cross-schema `ForeignKey`s at all) |
| `PUBLIC` | public schema only          | `TENANT_APPS` to `SHARED_APPS` (tenant -> public) |
| `TENANT` | tenant schemas only         | `SHARED_APPS` to `TENANT_APPS` (public -> tenant) |

In other words, pick `PUBLIC` or `TENANT` to keep the full state (and thus stay safe) on the side
that has incoming cross-schema `ForeignKey`s, and only skip building state on the other side. If you
have `ForeignKey`s in both directions, none of these options are safe to use.
