import datetime as dt

import ddf
import freezegun
import pytest
from pytz import timezone

import pgbulk
from pgbulk.tests import models


@pytest.mark.django_db
def test_sync_w_char_pk():
    """
    Tests with a model that has a char pk.
    """
    extant_obj1 = ddf.G(models.TestPkChar, my_key='1', char_field='1')
    extant_obj2 = ddf.G(models.TestPkChar, my_key='2', char_field='1')
    extant_obj3 = ddf.G(models.TestPkChar, my_key='3', char_field='1')

    pgbulk.sync(
        models.TestPkChar,
        [
            models.TestPkChar(my_key='3', char_field='2'),
            models.TestPkChar(my_key='4', char_field='2'),
            models.TestPkChar(my_key='5', char_field='2'),
        ],
        ['my_key'],
        ['char_field'],
    )

    assert models.TestPkChar.objects.count() == 3
    assert models.TestPkChar.objects.filter(my_key='3').exists()
    assert models.TestPkChar.objects.filter(my_key='4').exists()
    assert models.TestPkChar.objects.filter(my_key='5').exists()

    with pytest.raises(models.TestPkChar.DoesNotExist):
        models.TestPkChar.objects.get(pk=extant_obj1.pk)
    with pytest.raises(models.TestPkChar.DoesNotExist):
        models.TestPkChar.objects.get(pk=extant_obj2.pk)
    test_model = models.TestPkChar.objects.get(pk=extant_obj3.pk)
    assert test_model.char_field == '2'


@pytest.mark.django_db
def test_sync_no_existing_objs():
    """
    Tests when there are no existing objects before the sync.
    """
    pgbulk.sync(
        models.TestModel,
        [
            models.TestModel(int_field=1),
            models.TestModel(int_field=3),
            models.TestModel(int_field=4),
        ],
        ['int_field'],
        ['float_field'],
    )
    assert models.TestModel.objects.count() == 3
    assert models.TestModel.objects.filter(int_field=1).exists()
    assert models.TestModel.objects.filter(int_field=3).exists()
    assert models.TestModel.objects.filter(int_field=4).exists()


@pytest.mark.django_db
def test_sync_existing_objs_all_deleted():
    """
    Tests when there are existing objects that will all be deleted.
    """
    extant_obj1 = ddf.G(models.TestModel, int_field=1)
    extant_obj2 = ddf.G(models.TestModel, int_field=2)
    extant_obj3 = ddf.G(models.TestModel, int_field=3)

    pgbulk.sync(
        models.TestModel,
        [
            models.TestModel(int_field=4),
            models.TestModel(int_field=5),
            models.TestModel(int_field=6),
        ],
        ['int_field'],
        ['float_field'],
    )

    assert models.TestModel.objects.count() == 3
    assert models.TestModel.objects.filter(int_field=4).exists()
    assert models.TestModel.objects.filter(int_field=5).exists()
    assert models.TestModel.objects.filter(int_field=6).exists()

    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj1.id)
    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj2.id)
    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj3.id)


@pytest.mark.django_db
def test_sync_existing_objs_all_deleted_empty_sync():
    """
    Tests when there are existing objects deleted because of an emtpy sync.
    """
    extant_obj1 = ddf.G(models.TestModel, int_field=1)
    extant_obj2 = ddf.G(models.TestModel, int_field=2)
    extant_obj3 = ddf.G(models.TestModel, int_field=3)

    pgbulk.sync(models.TestModel, [], ['int_field'], ['float_field'])

    assert not models.TestModel.objects.exists()
    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj1.id)
    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj2.id)
    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj3.id)


@pytest.mark.django_db
def test_sync_existing_objs_some_deleted():
    """
    Tests when some existing objects will be deleted.
    """
    extant_obj1 = ddf.G(models.TestModel, int_field=1, float_field=1)
    extant_obj2 = ddf.G(models.TestModel, int_field=2, float_field=1)
    extant_obj3 = ddf.G(models.TestModel, int_field=3, float_field=1)

    pgbulk.sync(
        models.TestModel,
        [
            models.TestModel(int_field=3, float_field=2),
            models.TestModel(int_field=4, float_field=2),
            models.TestModel(int_field=5, float_field=2),
        ],
        ['int_field'],
        ['float_field'],
    )

    assert models.TestModel.objects.count() == 3
    assert models.TestModel.objects.filter(int_field=3).exists()
    assert models.TestModel.objects.filter(int_field=4).exists()
    assert models.TestModel.objects.filter(int_field=5).exists()

    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj1.id)
    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj2.id)
    test_model = models.TestModel.objects.get(id=extant_obj3.id)
    assert test_model.int_field == 3


@pytest.mark.django_db
def test_sync_existing_objs_some_deleted_w_queryset():
    """
    Tests when some existing objects will be deleted on a queryset
    """
    extant_obj0 = ddf.G(models.TestModel, int_field=0, float_field=1)
    extant_obj1 = ddf.G(models.TestModel, int_field=1, float_field=1)
    extant_obj2 = ddf.G(models.TestModel, int_field=2, float_field=1)
    extant_obj3 = ddf.G(models.TestModel, int_field=3, float_field=1)
    extant_obj4 = ddf.G(models.TestModel, int_field=4, float_field=0)

    pgbulk.sync(
        models.TestModel.objects.filter(int_field__lt=4),
        [
            models.TestModel(int_field=1, float_field=2),
            models.TestModel(int_field=2, float_field=2),
            models.TestModel(int_field=3, float_field=2),
        ],
        ['int_field'],
        ['float_field'],
    )

    assert models.TestModel.objects.count() == 4
    assert models.TestModel.objects.filter(int_field=1).exists()
    assert models.TestModel.objects.filter(int_field=2).exists()
    assert models.TestModel.objects.filter(int_field=3).exists()

    with pytest.raises(models.TestModel.DoesNotExist):
        models.TestModel.objects.get(id=extant_obj0.id)

    test_model = models.TestModel.objects.get(id=extant_obj1.id)
    assert test_model.float_field == 2
    test_model = models.TestModel.objects.get(id=extant_obj2.id)
    assert test_model.float_field == 2
    test_model = models.TestModel.objects.get(id=extant_obj3.id)
    assert test_model.float_field == 2
    test_model = models.TestModel.objects.get(id=extant_obj4.id)
    assert test_model.float_field == 0


@pytest.mark.django_db
def test_sync_existing_objs_some_deleted_wo_update():
    """
    Tests when some existing objects will be deleted on a queryset. Run syncing
    with no update fields and verify they are untouched in the sync
    """
    objs = [
        ddf.G(models.TestModel, int_field=i, float_field=i) for i in range(5)
    ]

    results = pgbulk.sync(
        models.TestModel.objects.filter(int_field__lt=4),
        [
            models.TestModel(int_field=1, float_field=2),
            models.TestModel(int_field=2, float_field=2),
            models.TestModel(int_field=3, float_field=2),
        ],
        ['int_field'],
        [],
        returning=True,
    )

    assert len(list(results)) == 4
    assert len(list(results.deleted)) == 1
    assert len(list(results.untouched)) == 3
    assert list(results.deleted)[0].id == objs[0].id


@pytest.mark.django_db
def test_sync_existing_objs_some_deleted_some_updated():
    """
    Tests when some existing objects will be deleted on a queryset. Run syncing
    with some update fields.
    """
    objs = [
        ddf.G(models.TestModel, int_field=i, float_field=i) for i in range(5)
    ]

    results = pgbulk.sync(
        models.TestModel.objects.filter(int_field__lt=4),
        [
            models.TestModel(int_field=1, float_field=2),
            models.TestModel(int_field=2, float_field=2),
            models.TestModel(int_field=3, float_field=2),
        ],
        ['int_field'],
        ['float_field'],
        returning=True,
        ignore_duplicate_updates=True,
    )

    assert len(list(results)) == 4
    assert len(list(results.deleted)) == 1
    assert len(list(results.updated)) == 2
    assert len(list(results.untouched)) == 1
    assert list(results.deleted)[0].id == objs[0].id


@pytest.mark.django_db
def test_upsert_return_upserts_none():
    """
    Tests the return_upserts flag on bulk upserts when there is no data.
    """
    return_values = pgbulk.upsert(
        models.TestModel, [], ['float_field'], ['float_field'], returning=True
    )
    assert not return_values


@pytest.mark.django_db
def test_upsert_return_multi_unique_fields_not_supported():
    """
    The new manager utils supports returning bulk upserts when there are
    multiple unique fields.
    """
    return_values = pgbulk.upsert(
        models.TestModel,
        [],
        ['float_field', 'int_field'],
        ['float_field'],
        returning=True,
    )
    assert not return_values


@pytest.mark.django_db
def test_upsert_return_created_values():
    """
    Tests that values that are created are returned properly when returning
    is True.
    """
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=1),
            models.TestModel(int_field=3),
            models.TestModel(int_field=4),
        ],
        ['int_field'],
        ['float_field'],
        returning=True,
    )

    assert len(list(results.created)) == 3
    for test_model, expected_int in zip(
        sorted(results.created, key=lambda k: k.int_field), [1, 3, 4]
    ):
        assert test_model.int_field == expected_int
        assert test_model.id is not None
    assert models.TestModel.objects.count() == 3


@pytest.mark.django_db
def test_upsert_return_list_of_values():
    """
    Tests that values that are created are returned properly when returning
    is True. Set returning to a list of fields
    """
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=1, float_field=2),
            models.TestModel(int_field=3, float_field=4),
            models.TestModel(int_field=4, float_field=5),
        ],
        ['int_field'],
        ['float_field'],
        returning=['float_field'],
    )

    assert len(list(results.created)) == 3
    with pytest.raises(AttributeError):
        list(results.created)[0].int_field
    assert {2, 4, 5} == {m.float_field for m in results.created}


@pytest.mark.django_db
def test_upsert_return_created_updated_values():
    """
    Tests returning values when the items are either updated or created.
    """
    # Create an item that will be updated
    ddf.G(models.TestModel, int_field=2, float_field=1.0)
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=1, float_field=3.0),
            models.TestModel(int_field=2.0, float_field=3.0),
            models.TestModel(int_field=3, float_field=3.0),
            models.TestModel(int_field=4, float_field=3.0),
        ],
        ['int_field'],
        ['float_field'],
        returning=True,
    )

    created = list(results.created)
    updated = list(results.updated)
    assert len(created) == 3
    assert len(updated) == 1
    for test_model, expected_int in zip(
        sorted(created, key=lambda k: k.int_field), [1, 3, 4]
    ):
        assert test_model.int_field == expected_int
        assert test_model.float_field == 3.0  # almostequals
        assert test_model.id is not None

    assert updated[0].int_field == 2
    assert updated[0].float_field == 3.0  # almostequals
    assert updated[0].id is not None
    assert models.TestModel.objects.count() == 4


@pytest.mark.django_db
def test_upsert_created_updated_auto_datetime_values():
    """
    Tests when the items are either updated or created when auto_now
    and auto_now_add datetime values are used
    """
    # Create an item that will be updated
    with freezegun.freeze_time('2018-09-01 00:00:00'):
        ddf.G(models.TestAutoDateTimeModel, int_field=1)

    with freezegun.freeze_time('2018-09-02 00:00:00'):
        results = pgbulk.upsert(
            models.TestAutoDateTimeModel,
            [
                models.TestAutoDateTimeModel(int_field=1),
                models.TestAutoDateTimeModel(int_field=2),
                models.TestAutoDateTimeModel(int_field=3),
                models.TestAutoDateTimeModel(int_field=4),
            ],
            ['int_field'],
            returning=True,
        )

    assert len(list(results.created)) == 3
    assert len(list(results.updated)) == 1

    expected_auto_now = [
        dt.datetime(2018, 9, 2),
        dt.datetime(2018, 9, 2),
        dt.datetime(2018, 9, 2),
        dt.datetime(2018, 9, 2),
    ]
    expected_auto_now_add = [
        dt.datetime(2018, 9, 1),
        dt.datetime(2018, 9, 2),
        dt.datetime(2018, 9, 2),
        dt.datetime(2018, 9, 2),
    ]
    for i, test_model in enumerate(sorted(results, key=lambda k: k.int_field)):
        assert test_model.auto_now_field == expected_auto_now[i]
        assert test_model.auto_now_add_field == expected_auto_now_add[i]


@pytest.mark.django_db
def test_upsert_wo_update_fields():
    """
    Tests bulk_upsert with no update fields. This function in turn should
    just do a bulk create for any models that do not already exist.
    """
    # Create models that already exist
    ddf.G(models.TestModel, int_field=1, float_field=1)
    ddf.G(models.TestModel, int_field=2, float_field=2)
    # Perform a bulk_upsert with one new model
    pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=1, float_field=3),
            models.TestModel(int_field=2, float_field=3),
            models.TestModel(int_field=3, float_field=3),
        ],
        ['int_field'],
        update_fields=[],
    )
    # Three objects should now exist, but no float fields should be updated
    assert models.TestModel.objects.count() == 3
    for test_model, expected_int_value in zip(
        models.TestModel.objects.order_by('int_field'), [1, 2, 3]
    ):
        assert test_model.int_field == expected_int_value
        assert test_model.float_field == expected_int_value


@pytest.mark.django_db
def test_upsert_w_blank_arguments():
    """
    Tests using required arguments and using blank arguments for everything
    else.
    """
    pgbulk.upsert(models.TestModel, [], ['field'], ['field'])
    assert not models.TestModel.objects.exists()


@pytest.mark.django_db
def test_upsert_no_updates():
    """
    Tests the case when no updates were previously stored (i.e objects are only
    created)
    """
    pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=1, char_field='1', float_field=1),
            models.TestModel(int_field=2, char_field='2', float_field=2),
        ],
        ['int_field'],
        ['char_field', 'float_field'],
    )

    for i, model_obj in enumerate(
        models.TestModel.objects.order_by('int_field')
    ):
        assert model_obj.int_field == i
        assert model_obj.char_field == str(i)
        assert model_obj.float_field == i  # almostequals


@pytest.mark.django_db
def test_upsert_update_fields_returning():
    """
    Tests the case when all updates were previously stored and the int
    field is used as a uniqueness constraint. Assert returned values are
    expected and that it updates all fields by default
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    test_models = [
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)
        for i in range(3)
    ]

    # Update using the int field as a uniqueness constraint
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=1, char_field='1', float_field=1),
            models.TestModel(int_field=2, char_field='2', float_field=2),
        ],
        ['int_field'],
        returning=True,
    )

    assert list(results.created) == []
    assert {u.id for u in results.updated} == {t.id for t in test_models}
    assert {u.int_field for u in results.updated} == {0, 1, 2}
    assert {u.float_field for u in results.updated} == {0, 1, 2}
    assert {u.char_field for u in results.updated} == {'0', '1', '2'}


@pytest.mark.django_db
def test_upsert_no_update_fields_returning():
    """
    Tests the case when all updates were previously stored and the int
    field is used as a uniqueness constraint. This test does not update
    any fields
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=1, char_field='1', float_field=1),
            models.TestModel(int_field=2, char_field='2', float_field=2),
        ],
        ['int_field'],
        [],
        returning=True,
    )

    assert list(results) == []


@pytest.mark.django_db
def test_upsert_update_duplicate_fields_returning_none_updated():
    """
    Tests the case when all updates were previously stored and the upsert
    tries to update the rows with duplicate values.
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='-1', float_field=-1),
            models.TestModel(int_field=1, char_field='-1', float_field=-1),
            models.TestModel(int_field=2, char_field='-1', float_field=-1),
        ],
        ['int_field'],
        ['char_field', 'float_field'],
        returning=True,
        ignore_duplicate_updates=True,
    )

    assert list(results) == []


@pytest.mark.django_db
def test_upsert_update_duplicate_fields_returning_some_updated():
    """
    Tests the case when all updates were previously stored and the upsert
    tries to update the rows with duplicate values. Test when some aren't
    duplicates
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='-1', float_field=-1),
            models.TestModel(int_field=1, char_field='-1', float_field=-1),
            models.TestModel(int_field=2, char_field='0', float_field=-1),
        ],
        ['int_field'],
        ['char_field', 'float_field'],
        returning=['char_field'],
        ignore_duplicate_updates=True,
    )

    assert list(results.created) == []
    assert len(list(results.updated)) == 1
    assert list(results.updated)[0].char_field == '0'


@pytest.mark.django_db
def test_upsert_update_duplicate_fields_returning_some_updated_untouched():
    """
    Tests the case when all updates were previously stored and the upsert
    tries to update the rows with duplicate values. Test when some aren't
    duplicates
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='-1', float_field=-1),
            models.TestModel(int_field=1, char_field='-1', float_field=-1),
            models.TestModel(int_field=2, char_field='0', float_field=-1),
            models.TestModel(int_field=3, char_field='3', float_field=3),
        ],
        ['int_field'],
        ['char_field', 'float_field'],
        returning=['char_field'],
        ignore_duplicate_updates=True,
        return_untouched=True,
    )

    assert len(list(results.updated)) == 1
    assert len(list(results.untouched)) == 2
    assert len(list(results.created)) == 1
    assert list(results.updated)[0].char_field == '0'
    assert list(results.created)[0].char_field == '3'


@pytest.mark.django_db
def test_upsert_update_duplicate_fields_returning_some_updated_ignore_dups():
    """
    Tests the case when all updates were previously stored and the upsert
    tries to update the rows with duplicate values. Test when some aren't
    duplicates and return untouched results. There will be no untouched
    results in this test since we turn off ignoring duplicate updates
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint
    results = pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='-1', float_field=-1),
            models.TestModel(int_field=1, char_field='-1', float_field=-1),
            models.TestModel(int_field=2, char_field='0', float_field=-1),
            models.TestModel(int_field=3, char_field='3', float_field=3),
        ],
        ['int_field'],
        ['char_field', 'float_field'],
        returning=['char_field'],
        ignore_duplicate_updates=False,
        return_untouched=True,
    )

    assert len(list(results.untouched)) == 0
    assert len(list(results.updated)) == 3
    assert len(list(results.created)) == 1
    assert list(results.created)[0].char_field == '3'


@pytest.mark.django_db
def test_upsert_all_updates_unique_int_field():
    """
    Tests the case when all updates were previously stored and the int
    field is used as a uniqueness constraint.
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint
    pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=1, char_field='1', float_field=1),
            models.TestModel(int_field=2, char_field='2', float_field=2),
        ],
        ['int_field'],
        ['char_field', 'float_field'],
    )

    # Verify that the fields were updated
    assert models.TestModel.objects.count() == 3
    for i, model_obj in enumerate(
        models.TestModel.objects.order_by('int_field')
    ):
        assert model_obj.int_field == i
        assert model_obj.char_field == str(i)
        assert model_obj.float_field == i  # almostequals


@pytest.mark.django_db
def test_upsert_all_updates_unique_int_field_update_float_field():
    """
    Tests the case when all updates were previously stored and the int
    field is used as a uniqueness constraint. Only updates the float field
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint
    pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=1, char_field='1', float_field=1),
            models.TestModel(int_field=2, char_field='2', float_field=2),
        ],
        ['int_field'],
        update_fields=['float_field'],
    )

    # Verify that the float field was updated
    assert models.TestModel.objects.count() == 3
    for i, model_obj in enumerate(
        models.TestModel.objects.order_by('int_field')
    ):
        assert model_obj.int_field == i
        assert model_obj.char_field == '-1'
        assert model_obj.float_field == i  # almostequals


@pytest.mark.django_db
def test_upsert_some_updates_unique_int_field_update_float_field():
    """
    Tests the case when some updates were previously stored and the int
    field is used as a uniqueness constraint. Only updates the float field.
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(2):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint. The first two
    # are updated while the third is created
    pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=1, char_field='1', float_field=1),
            models.TestModel(int_field=2, char_field='2', float_field=2),
        ],
        ['int_field'],
        ['float_field'],
    )

    # Verify that the float field was updated for the first two models and
    # the char field was not updated for the first two. The char field,
    # however, should be '2' for the third model since it was created
    assert models.TestModel.objects.count() == 3
    for i, model_obj in enumerate(
        models.TestModel.objects.order_by('int_field')
    ):
        assert model_obj.int_field == i
        assert model_obj.char_field == '-1' if i < 2 else '2'
        assert model_obj.float_field == i  # almostequals


@pytest.mark.django_db
def test_upsert_some_updates_unique_timezone_field_update_float_field():
    """
    Tests the case when some updates were previously stored and the timezone
    field is used as a uniqueness constraint. Only updates the float field.
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in ['US/Eastern', 'US/Central']:
        ddf.G(
            models.TestUniqueTzModel,
            time_zone=i,
            char_field='-1',
            float_field=-1,
        )

    # Update using the int field as a uniqueness constraint. The first two
    # are updated while the third is created
    pgbulk.upsert(
        models.TestUniqueTzModel,
        [
            models.TestModel(
                time_zone=timezone('US/Eastern'), char_field='0', float_field=0
            ),
            models.TestModel(
                time_zone=timezone('US/Central'), char_field='1', float_field=1
            ),
            models.TestModel(
                time_zone=timezone('UTC'), char_field='2', float_field=2
            ),
        ],
        ['time_zone'],
        ['float_field'],
    )

    # Verify that the float field was updated for the first two models and
    # the char field was not updated for the first two. The char field,
    # however, should be '2' for the third model since it was created
    m1 = models.TestUniqueTzModel.objects.get(time_zone=timezone('US/Eastern'))
    assert m1.char_field == '-1'
    assert m1.float_field == 0  # almostequals

    m2 = models.TestUniqueTzModel.objects.get(time_zone=timezone('US/Central'))
    assert m2.char_field == '-1'
    assert m2.float_field == 1  # almostequals

    m3 = models.TestUniqueTzModel.objects.get(time_zone=timezone('UTC'))
    assert m3.char_field == '2'
    assert m3.float_field == 2  # almostequals


@pytest.mark.django_db
def test_upsert_some_updates_unique_int_char_field_update_float_field():
    """
    Tests the case when some updates were previously stored and the int and
    char fields are used as a uniqueness constraint. Only updates the float
    field.
    """
    # Create previously stored test models with a unique int and char field
    for i in range(2):
        ddf.G(models.TestModel, int_field=i, char_field=str(i), float_field=-1)

    # Update using the int field as a uniqueness constraint. The first two
    # are updated while the third is created
    pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=1, char_field='1', float_field=1),
            models.TestModel(int_field=2, char_field='2', float_field=2),
        ],
        ['int_field', 'char_field'],
        ['float_field'],
    )

    # Verify that the float field was updated for the first two models and
    # the char field was not updated for the first two. The char field,
    # however, should be '2' for the third model since it was created
    assert models.TestModel.objects.count() == 3
    for i, model_obj in enumerate(
        models.TestModel.objects.order_by('int_field')
    ):
        assert model_obj.int_field == i
        assert model_obj.char_field == str(i)
        assert model_obj.float_field == i  # almostequals


@pytest.mark.django_db
def test_upsert_no_updates_unique_int_char_field():
    """
    Tests the case when no updates were previously stored and the int and
    char fields are used as a uniqueness constraint. In this case, there
    is data previously stored, but the uniqueness constraints don't match.
    """
    # Create previously stored test models with a unique int field and -1 for
    # all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int and char field as a uniqueness constraint. All
    # three objects are created
    pgbulk.upsert(
        models.TestModel,
        [
            models.TestModel(int_field=3, char_field='0', float_field=0),
            models.TestModel(int_field=4, char_field='1', float_field=1),
            models.TestModel(int_field=5, char_field='2', float_field=2),
        ],
        ['int_field', 'char_field'],
        ['float_field'],
    )

    # Verify that no updates occured
    assert models.TestModel.objects.count() == 6
    assert models.TestModel.objects.filter(char_field='-1').count() == 3
    for i, model_obj in enumerate(
        models.TestModel.objects.filter(char_field='-1').order_by('int_field')
    ):
        assert model_obj.int_field == i
        assert model_obj.char_field == '-1'
        assert model_obj.float_field == -1  # almostequals
    assert models.TestModel.objects.exclude(char_field='-1').count() == 3
    for i, model_obj in enumerate(
        models.TestModel.objects.exclude(char_field='-1').order_by('int_field')
    ):
        assert model_obj.int_field == i + 3
        assert model_obj.char_field == str(i)
        assert model_obj.float_field == i  # almostequals


@pytest.mark.django_db
def test_upsert_some_updates_unique_int_char_field_queryset():
    """
    Tests the case when some updates were previously stored and a queryset
    is used on the bulk upsert.
    """
    # Create previously stored test models with a unique int field and -1
    # for all other fields
    for i in range(3):
        ddf.G(models.TestModel, int_field=i, char_field='-1', float_field=-1)

    # Update using the int field as a uniqueness constraint on a queryset.
    # Only one object should be updated.
    pgbulk.upsert(
        models.TestModel.objects.filter(int_field=0),
        [
            models.TestModel(int_field=0, char_field='0', float_field=0),
            models.TestModel(int_field=4, char_field='1', float_field=1),
            models.TestModel(int_field=5, char_field='2', float_field=2),
        ],
        ['int_field'],
        ['float_field'],
    )

    # Verify that two new objecs were created
    assert models.TestModel.objects.count() == 5
    assert models.TestModel.objects.filter(char_field='-1').count() == 3
    for i, model_obj in enumerate(
        models.TestModel.objects.filter(char_field='-1').order_by('int_field')
    ):
        assert model_obj.int_field == i
        assert model_obj.char_field == '-1'


@pytest.mark.django_db
def test_update_foreign_key_by_id():
    t_model = ddf.G(models.TestModel)
    t_fk_model = ddf.G(models.TestForeignKeyModel)
    t_fk_model.test_model = t_model
    pgbulk.update(models.TestForeignKeyModel, [t_fk_model], ['test_model_id'])
    assert models.TestForeignKeyModel.objects.get().test_model == t_model


@pytest.mark.django_db
def test_update_foreign_key_by_name():
    t_model = ddf.G(models.TestModel)
    t_fk_model = ddf.G(models.TestForeignKeyModel)
    t_fk_model.test_model = t_model
    pgbulk.update(models.TestForeignKeyModel, [t_fk_model], ['test_model'])
    assert models.TestForeignKeyModel.objects.get().test_model == t_model


@pytest.mark.django_db
def test_update_foreign_key_pk_using_id():
    """
    Tests a bulk update on a model that has a primary key to a foreign key.
    It uses the id of the pk in the update
    """
    t = ddf.G(models.TestPkForeignKey, char_field='hi')
    pgbulk.update(
        models.TestPkForeignKey,
        [models.TestPkForeignKey(my_key_id=t.my_key_id, char_field='hello')],
        ['char_field'],
    )
    assert models.TestPkForeignKey.objects.count() == 1
    assert models.TestPkForeignKey.objects.filter(
        char_field='hello', my_key=t.my_key
    ).exists()


@pytest.mark.django_db
def test_update_foreign_key_pk():
    """
    Tests a bulk update on a model that has a primary key to a foreign key.
    It uses the foreign key itself in the update
    """
    t = ddf.G(models.TestPkForeignKey, char_field='hi')
    pgbulk.update(
        models.TestPkForeignKey,
        [models.TestPkForeignKey(my_key=t.my_key, char_field='hello')],
        ['char_field'],
    )
    assert models.TestPkForeignKey.objects.count() == 1
    assert models.TestPkForeignKey.objects.filter(
        char_field='hello', my_key=t.my_key
    ).exists()


@pytest.mark.django_db
def test_update_char_pk():
    """
    Tests a bulk update on a model that has a primary key to a char field.
    """
    ddf.G(models.TestPkChar, char_field='hi', my_key='1')
    pgbulk.update(
        models.TestPkChar,
        [models.TestPkChar(my_key='1', char_field='hello')],
        ['char_field'],
    )
    assert models.TestPkChar.objects.count() == 1
    assert models.TestPkChar.objects.filter(
        char_field='hello', my_key='1'
    ).exists()


@pytest.mark.django_db
def test_update_none():
    """
    Tests when no values are provided to bulk update.
    """
    pgbulk.update(models.TestModel, [], [])


@pytest.mark.django_db
def test_update_no_fields_given():
    """
    Tests updating when no fields are given. All fields should be updated
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1, float_field=2)
    test_obj_2 = ddf.G(models.TestModel, int_field=2, float_field=3)
    test_obj_1.int_field = 7
    test_obj_1.float_field = 8
    test_obj_2.int_field = 9
    test_obj_2.float_field = 10

    pgbulk.update(models.TestModel, [test_obj_1, test_obj_2])

    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.int_field == 7
    assert test_obj_1.float_field == 8
    assert test_obj_2.int_field == 9
    assert test_obj_2.float_field == 10


@pytest.mark.django_db
def test_update_floats_to_null():
    """
    Tests updating a float field to a null field.
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1, float_field=2)
    test_obj_2 = ddf.G(models.TestModel, int_field=2, float_field=3)
    test_obj_1.float_field = None
    test_obj_2.float_field = None

    pgbulk.update(models.TestModel, [test_obj_1, test_obj_2], ['float_field'])

    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.float_field is None
    assert test_obj_2.float_field is None


@pytest.mark.django_db
def test_update_ints_to_null():
    """
    Tests updating an int field to a null field.
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1, float_field=2)
    test_obj_2 = ddf.G(models.TestModel, int_field=2, float_field=3)
    test_obj_1.int_field = None
    test_obj_2.int_field = None

    pgbulk.update(models.TestModel, [test_obj_1, test_obj_2], ['int_field'])

    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.int_field is None
    assert test_obj_2.int_field is None


@pytest.mark.django_db
def test_update_chars_to_null():
    """
    Tests updating a char field to a null field.
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1, char_field='2')
    test_obj_2 = ddf.G(models.TestModel, int_field=2, char_field='3')
    test_obj_1.char_field = None
    test_obj_2.char_field = None

    pgbulk.update(models.TestModel, [test_obj_1, test_obj_2], ['char_field'])

    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.char_field is None
    assert test_obj_2.char_field is None


@pytest.mark.django_db
def test_update_objs_no_fields_to_update():
    """
    Tests when objects are given to bulk update with no fields to update.
    Nothing should change in the objects.
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1)
    test_obj_2 = ddf.G(models.TestModel, int_field=2)
    # Change the int fields on the models
    test_obj_1.int_field = 3
    test_obj_2.int_field = 4
    # Do a bulk update with no update fields
    pgbulk.update(models.TestModel, [test_obj_1, test_obj_2], [])
    # The test objects int fields should be untouched
    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.int_field == 1
    assert test_obj_2.int_field == 2


@pytest.mark.django_db
def test_update_objs_one_field_to_update():
    """
    Tests when objects are given to bulk update with one field to update.
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1)
    test_obj_2 = ddf.G(models.TestModel, int_field=2)
    # Change the int fields on the models
    test_obj_1.int_field = 3
    test_obj_2.int_field = 4
    # Do a bulk update with the int fields
    pgbulk.update(models.TestModel, [test_obj_1, test_obj_2], ['int_field'])
    # The test objects int fields should be untouched
    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.int_field == 3
    assert test_obj_2.int_field == 4


@pytest.mark.django_db
def test_update_objs_one_field_to_update_ignore_other_field():
    """
    Tests when objects are given to bulk update with one field to update.
    This test changes another field not included in the update and verifies
    it is not updated.
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1, float_field=1.0)
    test_obj_2 = ddf.G(models.TestModel, int_field=2, float_field=2.0)
    # Change the int and float fields on the models
    test_obj_1.int_field = 3
    test_obj_2.int_field = 4
    test_obj_1.float_field = 3.0
    test_obj_2.float_field = 4.0
    # Do a bulk update with the int fields
    pgbulk.update(models.TestModel, [test_obj_1, test_obj_2], ['int_field'])
    # The test objects int fields should be untouched
    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.int_field == 3
    assert test_obj_2.int_field == 4
    # The float fields should not be updated
    assert test_obj_1.float_field == 1.0
    assert test_obj_2.float_field == 2.0


@pytest.mark.django_db
def test_update_objs_two_fields_to_update():
    """
    Tests when objects are given to bulk update with two fields to update.
    """
    test_obj_1 = ddf.G(models.TestModel, int_field=1, float_field=1.0)
    test_obj_2 = ddf.G(models.TestModel, int_field=2, float_field=2.0)
    # Change the int and float fields on the models
    test_obj_1.int_field = 3
    test_obj_2.int_field = 4
    test_obj_1.float_field = 3.0
    test_obj_2.float_field = 4.0
    # Do a bulk update with the int fields
    pgbulk.update(
        models.TestModel,
        [test_obj_1, test_obj_2],
        ['int_field', 'float_field'],
    )
    # The test objects int fields should be untouched
    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)
    assert test_obj_1.int_field == 3
    assert test_obj_2.int_field == 4
    # The float fields should be updated
    assert test_obj_1.float_field == 3.0
    assert test_obj_2.float_field == 4.0


@pytest.mark.django_db
def test_update_objects_with_custom_db_field_types():
    """
    Tests when objects are updated that have custom field types
    """
    test_obj_1 = ddf.G(
        models.TestModel,
        int_field=1,
        float_field=1.0,
        json_field={'test': 'test'},
        array_field=['one', 'two'],
    )
    test_obj_2 = ddf.G(
        models.TestModel,
        int_field=2,
        float_field=2.0,
        json_field={'test2': 'test2'},
        array_field=['three', 'four'],
    )

    # Change the fields on the models
    test_obj_1.json_field = {'test': 'updated'}
    test_obj_1.array_field = ['one', 'two', 'updated']

    test_obj_2.json_field = {'test2': 'updated'}
    test_obj_2.array_field = ['three', 'four', 'updated']

    # Do a bulk update with the int fields
    pgbulk.update(
        models.TestModel,
        [test_obj_1, test_obj_2],
        ['json_field', 'array_field'],
    )

    # Refetch the objects
    test_obj_1 = models.TestModel.objects.get(id=test_obj_1.id)
    test_obj_2 = models.TestModel.objects.get(id=test_obj_2.id)

    # Assert that the json field was updated
    assert test_obj_1.json_field == {'test': 'updated'}
    assert test_obj_2.json_field == {'test2': 'updated'}

    # Assert that the array field was updated
    assert test_obj_1.array_field, ['one', 'two' == 'updated']
    assert test_obj_2.array_field, ['three', 'four' == 'updated']
