"""
Bulk Postgres upsert and update functions:

- Use [pgbulk.upsert][] to do an `INSERT ON CONFLICT` statement.
- Use [pgbulk.update][] to do a bulk `UPDATE` statement.
- Use [pgbulk.copy][] to do a `COPY FROM` statement.
- Use [pgbulk.aupsert][], [pgbulk.aupdate][], or [pgbulk.acopy][] for async versions.
"""

from pgbulk.core import UpdateField, UpsertResult, acopy, aupdate, aupsert, copy, update, upsert
from pgbulk.version import __version__

__all__ = [
    "acopy",
    "update",
    "aupdate",
    "copy",
    "upsert",
    "aupsert",
    "UpsertResult",
    "UpdateField",
    "__version__",
]
