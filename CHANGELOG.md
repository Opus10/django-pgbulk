# Changelog

## 2.3.0 (2023-12-27)

### Feature

  - Add `exclude` arguments to `pgbulk.upsert` and `pgbulk.update`. [Maxwell Muoto, cde5904]

    Add `exclude` arguments to `pgbulk.upsert` and `pgbulk.update`.

    Users can now use `exclude=["field_name"]` to exclude fields for updating or upserting data.

## 2.2.0 (2023-11-26)

### Feature

  - Django 5.0 compatibility [Wesley Kendall, e7848ed]

    Support and test against Django 5 with psycopg2 and psycopg3.

## 2.1.1 (2023-11-23)

### Trivial

  - Add py.typed file, fix typing issues [Maxwell Muoto, 76f6e77]

## 2.1.0 (2023-11-03)

### Bug

  - Allow updates on custom primary key fields [Wesley Kendall, 4dbfb1c]

    `pgbulk.update` would fail on models with custom primary key fields when
    no `update_fields` argument was supplied. This has been fixed.

## 2.0.4 (2023-10-10)

### Trivial

  - Improve base type annotations, avoid type annotations in comments [Maxwell Muoto, 862e253]

## 2.0.3 (2023-10-09)

### Trivial

  - Added Opus10 branding to docs [Wesley Kendall, c2f9d18]

## 2.0.2 (2023-10-08)

### Trivial

  - Add additional docs and notes around async usaged and model signals. [Wesley Kendall, 4cce843]

## 2.0.1 (2023-10-08)

### Trivial

  - Fix release notes [Wesley Kendall, 8a88b7a]

## 2.0.0 (2023-10-08)

### Api-Break

  - Python 3.12 / async support, dropping of `pgbulk.sync` and `return_untouched` [Wesley Kendall, de70607]

    This version of `django-pgbulk` breaks the API in the following manner:

    - `pgbulk.upsert` no longer supports the `return_untouched` argument. It had race conditions and will only be brought back if those race conditions can be addressed.
    - `pgbulk.upsert`'s `ignore_duplicate_updates` was renamed to `redundant_updates`. The default functionality is still the same, but the argument now has the opposite meaning.
    - `pgbulk.sync` was dropped since it relied on the `return_untouched` argument.

    This release also includes the following changes:

    - Python 3.12 is supported and Python 3.7 is dropped
    - Postgres 16 support
    - Async-compatible `pgbulk.aupsert` and `pgbulk.aupdate` were added
    - New documentation theme and formatting with Material for Mkdocs
    - Type annotations for public functions and classes

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
