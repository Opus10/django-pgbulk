# django-pgbulk

`django-pgbulk` provides several optimized bulk operations for Postgres:

1. [pgbulk.update][] - For updating a list of models in bulk. Although Django provides a `bulk_update` in 2.2, it performs individual updates for every row in some circumstances and does not perform a native bulk update.
2. [pgbulk.upsert][] - For doing a bulk update or insert. This function uses Postgres's `UPDATE ON CONFLICT` syntax to perform an atomic upsert operation. There are several options to this function that allow the user to avoid touching rows if they result in a duplicate update, along with returning which rows were updated or created. Users can also use `models.F` objects on conflicts.

!!! note

    Use [pgbulk.aupdate][] and [pgbulk.aupsert][] for async-compatible versions.

## Compatibility

`django-pgbulk` is compatible with Python 3.8 - 3.12, Django 3.2 - 4.2, Psycopg 2 - 3, and Postgres 12 - 16.
