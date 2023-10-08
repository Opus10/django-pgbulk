"""
Bulk Postgres upsert and update functions.

Briefly, these are the core functions and objects:

- Use [pgbulk.upsert][] to do a native Postgres `INSERT ON CONFLICT` statement.
- Use [pgbulk.update][] to do a native Postgres bulk `UPDATE` statement.
- Use [pgbulk.aupsert][] or [pgbulk.aupdate][] for async versions of these functions.

[pgbulk.upsert][] has other objects related to advanced usage:

- [pgbulk.UpsertResult][] encapsulates created and updated values when using the
  `returning` flag of [pgbulk.upsert][].
- [pgbulk.UpdateField][] allows one to specify expressions for updating fields
  in the upsert, for example, incrementing fields or conditionally ignoring
  updates.
"""

from pgbulk.core import UpdateField, UpsertResult, aupdate, aupsert, update, upsert
from pgbulk.version import __version__

__all__ = ["update", "aupdate", "upsert", "aupsert", "UpsertResult", "UpdateField", "__version__"]
