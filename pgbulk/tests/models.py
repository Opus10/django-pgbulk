from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.db import models
from timezone_field import TimeZoneField


class TestModel(models.Model):
    """
    A model for testing manager utils.
    """

    int_field = models.IntegerField(null=True, unique=True)
    char_field = models.CharField(max_length=128, null=True)
    float_field = models.FloatField(null=True)
    json_field = JSONField(default=dict)
    array_field = ArrayField(models.CharField(max_length=128), default=list)
    time_zone = TimeZoneField(default='UTC')

    class Meta:
        unique_together = ('int_field', 'char_field')


class TestUniqueTzModel(models.Model):
    """
    A model for testing manager utils with a timezone field as the uniqueness
    constraint.
    """

    int_field = models.IntegerField(null=True, unique=True)
    char_field = models.CharField(max_length=128, null=True)
    float_field = models.FloatField(null=True)
    time_zone = TimeZoneField(unique=True)

    class Meta:
        unique_together = ('int_field', 'char_field')


class TestAutoDateTimeModel(models.Model):
    """
    A model to test that upserts work with auto_now and auto_now_add
    """

    int_field = models.IntegerField(unique=True)
    auto_now_field = models.DateTimeField(auto_now=True)
    auto_now_add_field = models.DateTimeField(auto_now_add=True)


class TestForeignKeyModel(models.Model):
    """
    A test model that has a foreign key.
    """

    int_field = models.IntegerField()
    test_model = models.ForeignKey(TestModel, on_delete=models.CASCADE)


class TestPkForeignKey(models.Model):
    """
    A test model with a primary key thats a foreign key to another model.
    """

    my_key = models.ForeignKey(
        TestModel, primary_key=True, on_delete=models.CASCADE
    )
    char_field = models.CharField(max_length=128, null=True)


class TestPkChar(models.Model):
    """
    A test model with a primary key that is a char field.
    """

    my_key = models.CharField(max_length=128, primary_key=True)
    char_field = models.CharField(max_length=128, null=True)
