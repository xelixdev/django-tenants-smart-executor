# Django Tenants Smart Executor

When using [django-tenants](https://github.com/django-tenants/django-tenants), running migrations becomes quite a problem time-wise, especially as your list of tenants grows and the number of your apps and models increases.
This is the case even if there are actually no migrations to run.

This package provides two methods of speeding up migrations for `django-tenants`.

1. The first method is to skip running the migration on a schema if there are no migrations to run. If there are no migrations to run, the `schema_migrated` signal is still triggered.
2. The second method is to skip applying the state part of migrations in a schema when running a migration from the other schema. For example, if running a migration in the public schema, applying the tenant app state migrations is not necessary.

## Installation

Install using pip (or your package manager of choice):
```bash
pip install django-tenants-smart-executor
```

## Skipping schema migration if there are no migrations to run

Configure the `GET_EXECUTOR_FUNCTION` in your `settings.py`:
```python
GET_EXECUTOR_FUNCTION = "django_tenants_smart_executor.load_executor"
```

This will tell `django-tenants` to use the executor from this package, which will skip the migrations if there is nothing to run.

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

## Skipping state migration on schema

By default, this functionality is off. If you want to use it, you need to use the `GET_EXECUTOR_FUNCTION` configuration mentioned above.
There are three possible modes for this functionality, configured by the `SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA` setting.

1. Full (`full`). You can use this if there are no relationships between the public and tenant schemas.
2. Public (`public`). This will skip the state migrations of tenant apps when running on public schema. This is safe to use when there are no relationships from the tenant schema to the public schema.
3. Tenant (`tenant`). This will skip the state migrations of public apps when running on tenant schema. This is safe to use when there are no relationships from the public schema to the tenant schema.

On top of this, you can further configure exceptions with `SMART_EXECUTOR_LIMIT_STATE_EXCEPTIONS_MAP`. That option should be a dictionary of boolean (whether it's in the tenant schema) to iterables of apps which should be migrated regardless of the mode.

For example, with the following settings, the only public app that will have state migrations applied in the tenant schemas will be `account`. There will be no state migrations for tenant apps performed in public schema.

```python
SMART_EXECUTOR_LIMIT_STATE_TO_SCHEMA = "full"
SMART_EXECUTOR_LIMIT_STATE_EXCEPTIONS_MAP: dict[bool, set[str]] = {
    True: {  # in tenant schema, do migrate these public apps
        "account",
    },
    False: set(),  # in public schema, there are no exceptions for any tenant apps
}
```

Then, you will need to replace every single `django.db.migrations` import with `django_tenants_smart_executor.migrations` in your migration files. This is to use the modified version which can skip the state migration. All public classes and functions from the module are reexported, so you can do a simple find & replace.

The [ruff](https://docs.astral.sh/ruff/) rule [TID251](https://docs.astral.sh/ruff/rules/banned-api/) is useful for enforcing this.

```toml

[ruff.lint.flake8-tidy-imports.banned-api]
"django.db.migrations" = { msg = "Use django_tenants_smart_executor.migrations" }
```

### When to use this

Because this option is disabling state operations, you should only run this when applying migrations, not when creating new migrations or linting them using various tools. You may want to only run this in tests to speed up your tests, but in theory applying in production should be fine as well. Definitely do not contigure this to run when running `makemigrations`.
