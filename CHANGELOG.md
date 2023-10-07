# Changelog
## 1.4.0 (2023-06-08)
### Feature
  - Added Python 3.11, Django 4.2, and Psycopg 3 support [Wesley Kendall, f606b0b]

    Adds Python 3.11, Django 4.2, and Psycopg 3 support along with tests for multiple Postgres versions. Drops support for Django 2.2.

## 1.3.0 (2022-12-12)
### Feature
  - Sort bulk update objects [Wesley Kendall, f766617]

    Objects passed to ``pgbulk.update`` are now sorted to reduce the likelihood of
    a deadlock when executed concurrently.
### Trivial
  - Updated with latest Python template [Wesley Kendall, 9652cd2]
  - Updated with latest Django template [Wesley Kendall, 6ef27e6]

## 1.2.6 (2022-08-26)
### Trivial
  - Test against Django 4.1 and other CI improvements [Wes Kendall, 9eedff4]

## 1.2.5 (2022-08-24)
### Trivial
  - Fix ReadTheDocs builds [Wes Kendall, 15832a5]

## 1.2.4 (2022-08-20)
### Trivial
  - Updated with latest Django template [Wes Kendall, 4e9e095]

## 1.2.3 (2022-08-20)
### Trivial
  - Fix release note rendering and code formatting changes [Wes Kendall, 94f1192]

## 1.2.2 (2022-08-17)
### Trivial
  - README and intro documentation fix [Wes Kendall, e75930e]

## 1.2.1 (2022-07-31)
### Trivial
  - Updated with latest Django template, fixing doc builds [Wes Kendall, c3ed424]

## 1.2.0 (2022-03-14)
### Feature
  - Handle func-based fields and allow expressions in upserts [Wes Kendall, 64458c5]

    ``pgbulk.upsert`` allows users to provide a ``pgbulk.UpdateField`` object
    to the ``update_fields`` argument, allowing a users to specify an expression
    that happens if an update occurs.

    This allows, for example, a user to do ``models.F('my_field') + 1`` and
    increment integer fields in a ``pgbulk.upsert``.

    Along with this, fields that cast to ``Func`` and other expressions are
    properly handled during upsert.

## 1.1.1 (2022-03-14)
### Trivial
  - Updates to latest template, dropping py3.6 support and adding Django4 support [Wes Kendall, 35a04b0]

## 1.1.0 (2022-01-08)
### Bug
  - Fix error when upserting custom AutoFields [Wes Kendall, 114eb45]

    ``upsert()`` previously errored when using a custom auto-incrementing field. This
    has been tested and fixed.

## 1.0.2 (2021-06-06)
### Trivial
  - Updated with the latest Django template [Wes Kendall, 71a2678]

## 1.0.1 (2020-06-29)
### Trivial
  - Update with the latest public django app template. [Wes Kendall, 271b456]

## 1.0.0 (2020-06-27)
### Api-Break
  - Initial release of django-pgbulk. [Wes Kendall, 7070a26]

    The initial release of django-pgbulk includes three functions for
    bulk operations in postgres:

    1. ``pgbulk.update`` - For updating a list of models in bulk. Although Django
       provides a ``bulk_update`` in 2.2, it performs individual updates for
       every row and does not perform a native bulk update.
    2. ``pgbulk.upsert`` - For doing a bulk update or insert. This function uses
       postgres ``UPDATE ON CONFLICT`` syntax to perform an atomic upsert
       operation. There are several options to this function that allow the
       user to avoid touching rows if they result in a duplicate update, along
       with returning which rows were updated, created, or untouched.
    3. ``pgbulk.sync`` - For syncing a list of models with a table. Does a bulk
       upsert and also deletes any rows in the source queryset that were not
       part of the input data.
