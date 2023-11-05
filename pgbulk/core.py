import itertools
from collections import UserString, namedtuple
from typing import Iterable, List, Type, Union

from asgiref.sync import sync_to_async
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, models
from django.db.models.sql.compiler import SQLCompiler
from django.utils import timezone
from django.utils.version import get_version_tuple

UpdateFieldsTypeDef = Union[
    List[str], List["UpsertResult"], List[Union["UpsertResult", str]], None
]


def _psycopg_version():
    try:
        import psycopg as Database  # type: ignore
    except ImportError:
        import psycopg2 as Database
    except Exception as exc:  # pragma: no cover
        raise ImproperlyConfigured("Error loading psycopg2 or psycopg module") from exc

    version_tuple = get_version_tuple(Database.__version__.split(" ", 1)[0])

    if version_tuple[0] not in (2, 3):  # pragma: no cover
        raise ImproperlyConfigured(f"Pysocpg version {version_tuple[0]} not supported")

    return version_tuple


psycopg_version = _psycopg_version()
psycopg_maj_version = psycopg_version[0]


if psycopg_maj_version == 2:
    from psycopg2.extensions import AsIs as Literal
elif psycopg_maj_version == 3:
    import psycopg.adapt

    class Literal:  # pragma: no cover
        def __init__(self, val):
            self.val = val

    class LiteralDumper(psycopg.adapt.Dumper):  # pragma: no cover
        def dump(self, obj):
            return obj.val.encode("utf-8")

        def quote(self, obj):
            return self.dump(obj)

else:
    raise AssertionError


class UpdateField(UserString):
    """
    For expressing an update field as an expression to an upsert
    operation.

    Example:

        results = pgbulk.upsert(
            MyModel,
            [
                MyModel(some_int_field=0, some_key="a"),
                MyModel(some_int_field=0, some_key="b")
            ],
            ["some_key"],
            [
                pgbulk.UpdateField(
                    "some_int_field",
                    expression=models.F('some_int_field') + 1
                )
            ],
        )
    """

    def __init__(self, field: str, expression: Union[models.Expression, None] = None):
        self.data = field
        self.expression = expression


class UpsertResult(list):
    """
    Returned by [pgbulk.upsert][] when the `returning` argument is provided.

    Wraps a list of named tuples where the names correspond to the underlying
    Django model attribute names.

    Also provides properties to access created and updated rows.
    """

    @property
    def created(self) -> List[namedtuple]:
        """Return the created rows"""
        return [i for i in self if i.status_ == "c"]

    @property
    def updated(self) -> List[namedtuple]:
        """Return the updated rows"""
        return [i for i in self if i.status_ == "u"]


def _quote(field):
    return '"{0}"'.format(field)


def _get_update_fields(queryset, to_update, exclude=None):
    """
    Get the fields to be updated in an upsert.

    Always exclude auto_now_add and primary key fields
    """
    exclude = exclude or []
    model = queryset.model
    fields = {
        **{field.attname: field for field in model._meta.fields},
        **{field.name: field for field in model._meta.fields},
    }

    if to_update is None:
        to_update = [field.attname for field in model._meta.fields]

    to_update = [
        attname
        for attname in to_update
        if (
            attname not in exclude
            and not getattr(fields[attname], "auto_now_add", False)
            and not fields[attname].primary_key
        )
    ]

    return to_update


def _fill_auto_fields(queryset, values):
    """
    Given a list of models, fill in auto_now and auto_now_add fields
    for upserts. Since django manager utils passes Django's ORM, these values
    have to be automatically constructed
    """
    model = queryset.model
    auto_field_names = [
        f.attname
        for f in model._meta.fields
        if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False)
    ]
    now = timezone.now()
    for value in values:
        for f in auto_field_names:
            setattr(value, f, now)

    return values


def _prep_sql_args(queryset, connection, cursor, sql_args):
    if psycopg_maj_version == 3:
        cursor.adapters.register_dumper(Literal, LiteralDumper)

    compiler = SQLCompiler(query=queryset.query, connection=connection, using=queryset.using)

    return [
        Literal(cursor.mogrify(*sql_arg.as_sql(compiler, connection)).decode("utf-8"))
        if hasattr(sql_arg, "as_sql")
        else sql_arg
        for sql_arg in sql_args
    ]


def _get_field_db_val(queryset, field, value, connection):
    if hasattr(value, "resolve_expression"):  # pragma: no cover
        # Handle cases when the field is of type "Func" and other expressions.
        # This is useful for libraries like django-rdkit that can't easily be tested
        return value.resolve_expression(queryset.query, allow_joins=False, for_save=True)
    else:
        return field.get_db_prep_save(value, connection)


def _sort_by_unique_fields(queryset, model_objs, unique_fields):
    """
    Sort a list of models by their unique fields.

    Sorting models in an upsert greatly reduces the chances of deadlock
    when doing concurrent upserts
    """
    model = queryset.model
    connection = connections[queryset.db]
    unique_fields = [field for field in model._meta.fields if field.attname in unique_fields]

    def sort_key(model_obj):
        return tuple(
            _get_field_db_val(queryset, field, getattr(model_obj, field.attname), connection)
            for field in unique_fields
        )

    return sorted(model_objs, key=sort_key)


def _get_values_for_row(queryset, model_obj, all_fields):
    connection = connections[queryset.db]
    return [
        # Convert field value to db value
        # Use attname here to support fields with custom db_column names
        _get_field_db_val(queryset, field, getattr(model_obj, field.attname), connection)
        for field in all_fields
    ]


def _get_values_for_rows(queryset, model_objs, all_fields):
    connection = connections[queryset.db]
    row_values = []
    sql_args = []

    for i, model_obj in enumerate(model_objs):
        sql_args.extend(_get_values_for_row(queryset, model_obj, all_fields))
        if i == 0:
            row_values.append(
                "({0})".format(
                    ", ".join(["%s::{0}".format(f.db_type(connection)) for f in all_fields])
                )
            )
        else:
            row_values.append("({0})".format(", ".join(["%s"] * len(all_fields))))

    return row_values, sql_args


def _get_return_fields_sql(returning):
    return_fields_sql = ", ".join(_quote(field) for field in returning)
    return_fields_sql += ", CASE WHEN xmax = 0 THEN 'c' ELSE 'u' END AS status_"
    return return_fields_sql


def _get_upsert_sql(
    queryset,
    model_objs,
    unique_fields,
    update_fields,
    returning,
    redundant_updates=False,
):
    """
    Generates the postgres specific sql necessary to perform an upsert
    (ON CONFLICT) INSERT INTO table_name (field1, field2)
    VALUES (1, 'two')
    ON CONFLICT (unique_field) DO UPDATE SET field2 = EXCLUDED.field2;
    """
    model = queryset.model
    update_expressions = {f: f.expression for f in update_fields if getattr(f, "expression", None)}

    # Use all fields except pk unless the uniqueness constraint is the pk field
    all_fields = [
        field
        for field in model._meta.fields
        if field.column in unique_fields or not isinstance(field, models.AutoField)
    ]

    all_field_names = [field.column for field in all_fields]
    returning = returning if returning is not True else [f.column for f in model._meta.fields]
    all_field_names_sql = ", ".join([_quote(field) for field in all_field_names])

    # Convert field names to db column names
    unique_fields = [model._meta.get_field(unique_field) for unique_field in unique_fields]
    update_fields = [model._meta.get_field(update_field) for update_field in update_fields]

    row_values, sql_args = _get_values_for_rows(queryset, model_objs, all_fields)

    unique_field_names_sql = ", ".join([_quote(field.column) for field in unique_fields])
    update_fields_expressions = {
        field.column: f"EXCLUDED.{_quote(field.column)}" for field in update_fields
    }
    if update_expressions:
        connection = connections[queryset.db]
        compiler = SQLCompiler(query=queryset.query, connection=connection, using=queryset.using)
        with connection.cursor() as cursor:
            for field_name, expr in update_expressions.items():
                expr = expr.resolve_expression(queryset.query, allow_joins=False, for_save=True)
                val = cursor.mogrify(*expr.as_sql(compiler, connection))
                if isinstance(val, bytes):  # Psycopg 2/3 return different types
                    val = val.decode("utf-8")

                update_fields_expressions[model._meta.get_field(field_name).column] = val

    update_fields_sql = ", ".join(
        f"{_quote(field.column)} = {update_fields_expressions[field.column]}"
        for field in update_fields
    )

    return_sql = "RETURNING " + _get_return_fields_sql(returning) if returning else ""
    ignore_duplicates_sql = ""
    if not redundant_updates:
        ignore_duplicates_sql = (
            " WHERE ({update_fields_sql}) IS DISTINCT FROM ({excluded_update_fields_sql}) "
        ).format(
            update_fields_sql=", ".join(
                "{0}.{1}".format(model._meta.db_table, _quote(field.column))
                for field in update_fields
            ),
            excluded_update_fields_sql=", ".join(update_fields_expressions.values()),
        )

    on_conflict = (
        "DO UPDATE SET {0} {1}".format(update_fields_sql, ignore_duplicates_sql)
        if update_fields
        else "DO NOTHING"
    )

    row_values_sql = ", ".join(row_values)
    sql = (
        " INSERT INTO {table_name} ({all_field_names_sql})"
        " VALUES {row_values_sql}"
        " ON CONFLICT ({unique_field_names_sql}) {on_conflict} {return_sql}"
    ).format(
        table_name=model._meta.db_table,
        all_field_names_sql=all_field_names_sql,
        row_values_sql=row_values_sql,
        unique_field_names_sql=unique_field_names_sql,
        on_conflict=on_conflict,
        return_sql=return_sql,
    )

    return sql, sql_args


def _fetch(
    queryset,
    model_objs,
    unique_fields,
    update_fields,
    returning,
    redundant_updates=False,
):
    """
    Perfom the upsert
    """
    connection = connections[queryset.db]
    upserted = []

    if model_objs:
        sql, sql_args = _get_upsert_sql(
            queryset,
            model_objs,
            unique_fields,
            update_fields,
            returning,
            redundant_updates=redundant_updates,
        )

        with connection.cursor() as cursor:
            sql_args = _prep_sql_args(queryset, connection, cursor, sql_args)
            cursor.execute(sql, sql_args)
            if cursor.description:
                nt_result = namedtuple("Result", [col[0] for col in cursor.description])
                upserted = [nt_result(*row) for row in cursor.fetchall()]

    return UpsertResult(upserted)


def _upsert(
    queryset: Union[Type[models.Model], models.QuerySet],
    model_objs: Iterable[models.Model],
    unique_fields: List[str],
    update_fields: UpdateFieldsTypeDef = None,
    returning: Union[List[str], bool] = False,
    redundant_updates: bool = False,
):
    """
    Perform a bulk upsert on a table

    Args:
        queryset: A model or a queryset that defines the
            collection to upsert.
        model_objs: An iterable of Django models to upsert.
        unique_fields: A list of fields that define the uniqueness
            of the model. The model must have a unique constraint on these
            fields.
        update_fields: A list of fields to update
            whenever objects already exist. If an empty list is provided, it
            is equivalent to doing a bulk insert on the objects that don't
            exist. If `None`, all fields will be updated. If you want to
            perform an expression such as an `F` object on a field when
            it is updated, use the [pgbulk.UpdateField][] class. See
            examples below.
        returning: If True, returns all fields. If a list,
            only returns fields in the list.
        redundant_updates: Don't perform an update
            if all columns are identical to the row in the database.
    """
    queryset = queryset if isinstance(queryset, models.QuerySet) else queryset.objects.all()

    # Populate automatically generated fields in the rows like date times
    _fill_auto_fields(queryset, model_objs)

    # Sort the rows to reduce the chances of deadlock during concurrent upserts
    model_objs = _sort_by_unique_fields(queryset, model_objs, unique_fields)
    update_fields = _get_update_fields(queryset, update_fields, exclude=unique_fields)

    return _fetch(
        queryset,
        model_objs,
        unique_fields,
        update_fields,
        returning,
        redundant_updates=redundant_updates,
    )


def update(
    queryset: Union[Type[models.Model], models.QuerySet],
    model_objs: Iterable[models.Model],
    update_fields: Union[List[str], None] = None,
) -> None:
    """
    Performs a bulk update.

    Args:
        queryset: The queryset to use when bulk updating
        model_objs: Model object values to use for the update
        update_fields: A list of fields on the
            model objects to update. If `None`, all fields will be updated.

    Note:
        Model signals such as `post_save` are not emitted.

    Example:
        Update an attribute of multiple models in bulk::

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
    """
    queryset = queryset if isinstance(queryset, models.QuerySet) else queryset.objects.all()
    connection = connections[queryset.db]
    model = queryset.model
    update_fields = _get_update_fields(queryset, update_fields)

    # Sort the model objects to reduce the likelihood of deadlocks
    model_objs = sorted(model_objs, key=lambda obj: obj.pk)

    # Add the pk to the value fields so we can join during the update
    value_fields = [model._meta.pk.attname] + update_fields

    row_values = [
        [
            _get_field_db_val(
                queryset,
                model_obj._meta.get_field(field),
                getattr(model_obj, model_obj._meta.get_field(field).attname),
                connection,
            )
            for field in value_fields
        ]
        for model_obj in model_objs
    ]

    # If we do not have any values or fields to update, just return
    if len(row_values) == 0 or len(update_fields) == 0:
        return []

    db_types = [model._meta.get_field(field).db_type(connection) for field in value_fields]

    value_fields_sql = ", ".join(
        '"{field}"'.format(field=model._meta.get_field(field).column) for field in value_fields
    )

    update_fields_sql = ", ".join(
        [
            '"{field}" = "new_values"."{field}"'.format(field=model._meta.get_field(field).column)
            for field in update_fields
        ]
    )

    values_sql = ", ".join(
        [
            "({0})".format(
                ", ".join(
                    [
                        "%s::{0}".format(db_types[i]) if not row_number and i else "%s"
                        for i, _ in enumerate(row)
                    ]
                )
            )
            for row_number, row in enumerate(row_values)
        ]
    )

    update_sql = (
        "UPDATE {table} "
        "SET {update_fields_sql} "
        "FROM (VALUES {values_sql}) AS new_values ({value_fields_sql}) "
        'WHERE "{table}"."{pk_field}" = "new_values"."{pk_field}"'
    ).format(
        table=model._meta.db_table,
        pk_field=model._meta.pk.column,
        update_fields_sql=update_fields_sql,
        values_sql=values_sql,
        value_fields_sql=value_fields_sql,
    )

    update_sql_params = list(itertools.chain(*row_values))

    with connection.cursor() as cursor:
        update_sql_params = _prep_sql_args(queryset, connection, cursor, update_sql_params)
        return cursor.execute(update_sql, update_sql_params)


async def aupdate(
    queryset: Union[Type[models.Model], models.QuerySet],
    model_objs: Iterable[models.Model],
    update_fields: Union[List[str], None] = None,
) -> None:
    """
    Perform an asynchronous bulk update.

    See [pgbulk.update][]

    Note:
        Like other async Django ORM methods, `aupdate` currently wraps `update` in
        a `sync_to_async` wrapper. It does not yet use an asynchronous database
        driver but will in the future.
    """
    return await sync_to_async(update)(queryset, model_objs, update_fields)


def upsert(
    queryset: Union[Type[models.Model], models.QuerySet],
    model_objs: Iterable[models.Model],
    unique_fields: List[str],
    update_fields: UpdateFieldsTypeDef = None,
    *,
    returning: Union[List[str], bool] = False,
    redundant_updates: bool = False,
) -> UpsertResult:
    """
    Perform a bulk upsert.

    Args:
        queryset: A model or a queryset that defines the
            collection to upsert
        model_objs: An iterable of Django models to upsert. All models
            in this list will be bulk upserted.
        unique_fields: A list of fields that define the uniqueness
            of the model. The model must have a unique constraint on these
            fields
        update_fields: A list of fields to update whenever objects already exist.
            If an empty list is provided, it is equivalent to doing a bulk insert on
            the objects that don't exist. If `None`, all fields will be updated.
            If you want to perform an expression such as an `F` object on a field when
            it is updated, use the [pgbulk.UpdateField][] class. See examples below.
        returning: If True, returns all fields. If a list, only returns fields
            in the list. If False, do not return results from the upsert.
        redundant_updates: Perform an update
            even if all columns are identical to the row in the database.

    Returns:
        The upsert result, an iterable list of all upsert objects. Use the `.updated`
            and `.created` attributes to iterate over created or updated elements.

    Note:
        Model signals such as `post_save` are not emitted.

    Example:
        A basic bulk upsert on a model:

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

    Example:
        Return the results of an upsert:

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

    Example:
        Upsert values and update rows even when the update is meaningless
        (i.e. a redundant update). This is turned off by default, but it
        can be enabled in case postgres triggers or other processes
        need to happen as a result of an update:

            pgbulk.upsert(
                MyModel,
                [
                    MyModel(int_field=1, some_attr="some_val1"),
                    MyModel(int_field=2, some_attr="some_val2"),
                ],
                ["int_field"],
                ["some_attr"],
                # Perform updates in the database even if it's identical
                redundant_updates=True
            )

    Example:
        Use an expression for a field if an update happens. In the example
        below, we increment `some_int_field` by one whenever an update happens.
        Otherwise it defaults to zero:

            results = pgbulk.upsert(
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
    """
    return _upsert(
        queryset,
        model_objs,
        unique_fields,
        update_fields=update_fields,
        returning=returning,
        redundant_updates=redundant_updates,
    )


async def aupsert(
    queryset: Union[Type[models.Model], models.QuerySet],
    model_objs: Iterable[models.Model],
    unique_fields: List[str],
    update_fields: UpdateFieldsTypeDef = None,
    *,
    returning: Union[List[str], bool] = False,
    redundant_updates: bool = False,
) -> UpsertResult:
    """
    Perform an asynchronous bulk upsert.

    See [pgbulk.upsert][]

    Note:
        Like other async Django ORM methods, `aupsert` currently wraps `upsert` in
        a `sync_to_async` wrapper. It does not yet use an asynchronous database
        driver but will in the future.
    """
    return await sync_to_async(upsert)(
        queryset,
        model_objs,
        unique_fields,
        update_fields,
        returning=returning,
        redundant_updates=redundant_updates,
    )
