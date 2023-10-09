# django-pgbulk

`django-pgbulk` provides functions for doing native Postgres bulk upserts (i.e. [UPDATE ON CONFLICT](https://www.postgresql.org/docs/current/sql-insert.html)) and bulk updates.

Bulk upserts can distinguish between updated and created rows and optionally ignore redundant updates.

Bulk updates are true bulk updates, unlike Django's [bulk_update](https://docs.djangoproject.com/en/4.2/ref/models/querysets/#bulk-update) which can still suffer from *O(N)* queries and can create poor locking scenarios.

## Quick Start

Do a bulk upsert on a model:

    import pgbulk

    pgbulk.upsert(
        MyModel,
        [
            MyModel(int_field=1, some_attr="some_val1"),
            MyModel(int_field=2, some_attr="some_val2"),
        ],
        # These are the fields that identify the uniqueness constraint.
        ["int_field"],
        # These are the fields that will be updated if the row already
        # exists. If not provided, all fields will be updated
        ["some_attr"]
    )

Do a bulk update on a model:

    import pgbulk

    pgbulk.update(
        MyModel,
        [
            MyModel(id=1, some_attr='some_val1'),
            MyModel(id=2, some_attr='some_val2')
        ],
        # These are the fields that will be updated. If not provided,
        # all fields will be updated
        ['some_attr']
    )

[View the django-pgbulk docs](https://django-pgbulk.readthedocs.io/) for more information.

## Compatibility

`django-pgbulk` is compatible with Python 3.8 - 3.12, Django 3.2 - 4.2, Psycopg 2 - 3, and Postgres 12 - 16.

## Documentation

[View the django-pgbulk docs here](https://django-pgbulk.readthedocs.io/)

## Installation

Install `django-pgbulk` with:

    pip3 install django-pgbulk

After this, add `pgbulk` to the `INSTALLED_APPS` setting of your Django project.

## Contributing Guide

For information on setting up django-pgbulk for development and contributing changes, view [CONTRIBUTING.md](CONTRIBUTING.md).

## Primary Authors

- [Wes Kendall](https://github.com/wesleykendall)
