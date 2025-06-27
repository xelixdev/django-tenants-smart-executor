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
