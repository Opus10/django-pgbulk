# django-pgbulk

`django-pgbulk` provides several optimized bulk operations for Postgres:

1. [pgbulk.update][] - For updating a list of models in bulk. Although Django provides a `bulk_update` in 2.2, it performs individual updates for every row in some circumstances and does not perform a native bulk update.
2. [pgbulk.upsert][] - For doing a bulk update or insert. This function uses Postgres's `UPDATE ON CONFLICT` syntax to perform an atomic upsert operation.
3. [pgbulk.copy][] - For inserting values using `COPY FROM`. Can be significantly faster than a native `INSERT` or Django's `bulk_create`.

!!! note

    Use [pgbulk.aupdate][], [pgbulk.aupsert][], and [pgbulk.acopy][] for async-compatible versions.

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

Do a bulk copy on a model:

    import pgbulk

    pgbulk.copy(
        MyModel,
        # Insert these rows using COPY FROM
        [
            MyModel(id=1, some_attr='some_val1'),
            MyModel(id=2, some_attr='some_val2')
        ],
    )

## Advanced Features

Here are some advanced features at a glance:

- [pgbulk.upsert][] can categorize which rows were inserted or updated.
- [pgbulk.upsert][] and [pgbulk.update][] can ignore updating unchanged fields.
- [pgbulk.upsert][] and [pgbulk.update][] can use expressions in updates.

## Compatibility

`django-pgbulk` is compatible with Python 3.8 - 3.12, Django 3.2 - 5.0, Psycopg 2 - 3, and Postgres 13 - 16.

## Next Steps

View the [user guide section](guide.md), which has more examples and advanced usage.
