# User Guide

`django-pgbulk` comes with the following functions:

- Use [pgbulk.upsert][] to do a native Postgres `INSERT ON CONFLICT` statement.
- Use [pgbulk.update][] to do a native Postgres bulk `UPDATE` statement.
- Use [pgbulk.aupsert][] or [pgbulk.aupdate][] for async versions of these functions.

Below we show examples and advanced functionality.

## Using `pgbulk.upsert`

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

#### Don't apply updates if the rows are identical

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

    Triggers and auto-generated fields not in the update won't be applied. Identical rows also won't be returned if using `returning=True`.

## Using `pgbulk.update`

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

#### Don't apply updates if the rows are identical

Use `ignore_unchanged=True` to avoid identical updates:

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

    Triggers and auto-generated fields not in the update won't be applied. Identical rows also won't be returned if using `returning=True`.
