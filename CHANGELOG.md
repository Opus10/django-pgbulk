# Changelog
## 1.0.0 (2020-06-26)
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

