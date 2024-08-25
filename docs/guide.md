# User Guide

`django-pgbulk` comes with the following functions:

- Use [pgbulk.upsert][] to do an `INSERT ON CONFLICT` statement.
- Use [pgbulk.update][] to do a bulk `UPDATE` statement.
- Use [pgbulk.copy][] to do a `COPY FROM` statement.
- Use [pgbulk.aupsert][], [pgbulk.aupdate][], or [pgbulk.acopy][] for async versions.

Below we show examples and advanced functionality.

## Using `pgbulk.upsert`

[pgbulk.upsert][] allows for updating or inserting rows atomically and returning results based on inserts or updates. Update fields, returned values, and ignoring unchanged rows can be configured.

See [the Postgres INSERT docs](https://www.postgresql.org/docs/current/sql-insert.html) for more information on how `ON CONFLICT` works.

#### A basic bulk upsert on a model

```python
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
```

#### Return the results of an upsert

```python
results = pgbulk.upsert(
    MyModel,
    [
        MyModel(int_field=1, some_attr="some_val1"),
        MyModel(int_field=2, some_attr="some_val2"),
    ],
    ["int_field"],
    ["some_attr"],
    # `True` will return all columns. One can also explicitly
    # list which columns will be returned
    returning=True
)

# Print which results were created
print(results.created)

# Print which results were updated.
# By default, if an update results in no changes, it will not
# be updated and will not be returned.
print(results.updated)
```

#### Use an expression for updates

In the example, we increment `some_int_field` by one whenever an update happens. Otherwise it defaults to zero:

```python
pgbulk.upsert(
    MyModel,
    [
        MyModel(some_int_field=0, some_key="a"),
        MyModel(some_int_field=0, some_key="b")
    ],
    ["some_key"],
    [
        # Use UpdateField to specify an expression for the update.
        pgbulk.UpdateField(
            "some_int_field",
            expression=models.F("some_int_field") + 1
        )
    ],
)
```

#### Ignore updating unchanged rows

```python
pgbulk.upsert(
    MyModel,
    [
        MyModel(int_field=1, some_attr="some_val1"),
        MyModel(int_field=2, some_attr="some_val2"),
    ],
    ["int_field"],
    ["some_attr"],
    ignore_unchanged=True
)
```

!!! warning

    Triggers and auto-generated fields not in the update won't be applied. Unchanged rows also won't be returned if using `returning=True`.

## Using `pgbulk.update`

[pgbulk.update][] issues updates to multiple rows with an `UPDATE SET ... FROM VALUES` statement. Update fields, returned values, and ignoring unchanged rows can be configured.

#### Update an attribute of multiple models in bulk

```python
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
```

#### Use an expression in an update

In the example, we increment `some_int_field` by one:

```python
pgbulk.update(
    MyModel,
    [
        MyModel(some_int_field=0, some_key="a"),
        MyModel(some_int_field=0, some_key="b")
    ],
    [
        # Use UpdateField to specify an expression for the update.
        pgbulk.UpdateField(
            "some_int_field",
            expression=models.F("some_int_field") + 1
        )
    ],
)
```

#### Return the results of an update

```python
results = pgbulk.upsert(
    MyModel,
    [
        MyModel(int_field=1, some_attr="some_val1"),
        MyModel(int_field=2, some_attr="some_val2"),
    ],
    ["int_field", "some_attr"],
    # `True` will return all columns. One can also explicitly
    # list which columns will be returned.
    returning=True
)

# Results can be accessed as a tuple
print(results[0].int_field)
```

#### Ignore updating unchanged rows

```python
pgbulk.upsert(
    MyModel,
    [
        MyModel(int_field=1, some_attr="some_val1"),
        MyModel(int_field=2, some_attr="some_val2"),
    ],
    ["int_field"],
    ignore_unchanged=True
)
```

!!! warning

    Triggers and auto-generated fields not in the update won't be applied. Unchanged rows also won't be returned if using `returning=True`.

## Using `pgbulk.copy`

Using `pgbulk.copy` issues a `COPY ... FROM STDIN` statement to insert rows, which can be substantially faster than bulk `INSERT` statement or Django's `bulk_create`. Unlike `bulk_create`, `pgbulk.copy` cannot return inserted results.

!!! note

    `pgbulk.copy` is not only available when using psycopg2.

#### Inserting Rows

```python
import pgbulk

pgbulk.copy(
    models.TestModel,
    [
        models.TestModel(int_field=5, float_field=1),
        models.TestModel(int_field=6, float_field=2),
        models.TestModel(int_field=7, float_field=3),
    ],
)
```

#### Inserting Specific Columns

Specify columns or use `exclude` to configure which columns are copied:

```python
pgbulk.copy(
    models.TestModel,
    [
        models.TestModel(int_field=5, float_field=1),
        models.TestModel(int_field=6, float_field=2),
        models.TestModel(int_field=7, float_field=3),
    ],
    ["int_field"]  # Only copy the int_field
)
```

```python
pgbulk.copy(
    ...,
    exclude=["generated_field"]  # Exclude only this field
)
```

!!! note

    Columns that are excluded from the copy must be generated, nullable, or have database defaults.
