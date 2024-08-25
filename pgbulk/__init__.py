"""
Bulk Postgres upsert and update functions:

- Use [pgbulk.upsert][] to do a native Postgres `INSERT ON CONFLICT` statement.
- Use [pgbulk.update][] to do a native Postgres bulk `UPDATE` statement.
- Use [pgbulk.aupsert][] or [pgbulk.aupdate][] for async versions of these functions.
"""

from pgbulk.core import UpdateField, UpsertResult, aupdate, aupsert, update, upsert
from pgbulk.version import __version__

__all__ = ["update", "aupdate", "upsert", "aupsert", "UpsertResult", "UpdateField", "__version__"]
