django-pgbulk
=============

``django-pgplus``, forked from
`django-manager-utils <https://django-manager-utils.readthedocs.io>`__,
provides several optimized bulk operations for Postgres:

1. `pgbulk.update` - For updating a list of models in bulk. Although Django
   provides a ``bulk_update`` in 2.2, it performs individual updates for
   every row and does not perform a native bulk update.
2. `pgbulk.upsert` - For doing a bulk update or insert. This function uses
   postgres ``UPDATE ON CONFLICT`` syntax to perform an atomic upsert
   operation. There are several options to this function that allow the
   user to avoid touching rows if they result in a duplicate update, along
   with returning which rows were updated, created, or untouched. Users can
   also use ``models.F`` objects on conflicts.
3. `pgbulk.sync` - For syncing a list of models with a table. Does a bulk
   upsert and also deletes any rows in the source queryset that were not
   part of the input data.


pgbulk.update
-------------
.. autofunction:: pgbulk.update


pgbulk.upsert
-------------
.. autofunction:: pgbulk.upsert


pgbulk.sync
-----------
.. autofunction:: pgbulk.sync
