import decimal
import enum
import json
import unittest
import uuid

from djrm.core import checks, exceptions, serializers, validators
from djrm.core.exceptions import FieldError
from djrm.core.management import call_command
from djrm.db import IntegrityError, connection, models
from djrm.db.models.expressions import Exists, F, OuterRef, RawSQL, Value
from djrm.db.models.functions import Cast, JSONObject, Upper
from djrm.test import TransactionTestCase, override_settings, skipUnlessDBFeature
from djrm.test.utils import isolate_apps
from djrm.utils import timezone

from . import PostgreSQLSimpleTestCase, PostgreSQLTestCase
from .models import (
    ArrayEnumModel,
    ArrayFieldSubclass,
    CharArrayModel,
    DateTimeArrayModel,
    IntegerArrayModel,
    NestedIntegerArrayModel,
    NullableIntegerArrayModel,
    OtherTypesArrayModel,
    PostgreSQLModel,
    Tag,
    WithSizeArrayModel,
)

try:
    from djrm.contrib.postgres.aggregates import ArrayAgg
    from djrm.contrib.postgres.expressions import ArraySubquery
    from djrm.contrib.postgres.fields import ArrayField
    from djrm.contrib.postgres.fields.array import IndexTransform, SliceTransform
    from djrm.db.backends.postgresql.psycopg_any import NumericRange
except ImportError:
    pass


@isolate_apps("postgres_tests")
class BasicTests(PostgreSQLSimpleTestCase):
    def test_get_field_display(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(
                models.CharField(max_length=16),
                choices=[
                    ["Media", [(["vinyl", "cd"], "Audio")]],
                    (("mp3", "mp4"), "Digital"),
                ],
            )

        tests = (
            (["vinyl", "cd"], "Audio"),
            (("mp3", "mp4"), "Digital"),
            (("a", "b"), "('a', 'b')"),
            (["c", "d"], "['c', 'd']"),
        )
        for value, display in tests:
            with self.subTest(value=value, display=display):
                instance = MyModel(field=value)
                self.assertEqual(instance.get_field_display(), display)

    def test_get_field_display_nested_array(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(
                ArrayField(models.CharField(max_length=16)),
                choices=[
                    [
                        "Media",
                        [([["vinyl", "cd"], ("x",)], "Audio")],
                    ],
                    ((["mp3"], ("mp4",)), "Digital"),
                ],
            )

        tests = (
            ([["vinyl", "cd"], ("x",)], "Audio"),
            ((["mp3"], ("mp4",)), "Digital"),
            ((("a", "b"), ("c",)), "(('a', 'b'), ('c',))"),
            ([["a", "b"], ["c"]], "[['a', 'b'], ['c']]"),
        )
        for value, display in tests:
            with self.subTest(value=value, display=display):
                instance = MyModel(field=value)
                self.assertEqual(instance.get_field_display(), display)


class TestSaveLoad(PostgreSQLTestCase):
    def test_integer(self):
        instance = IntegerArrayModel(field=[1, 2, 3])
        instance.save()
        loaded = IntegerArrayModel.objects.get()
        self.assertEqual(instance.field, loaded.field)

    def test_char(self):
        instance = CharArrayModel(field=["hello", "goodbye"])
        instance.save()
        loaded = CharArrayModel.objects.get()
        self.assertEqual(instance.field, loaded.field)

    def test_dates(self):
        instance = DateTimeArrayModel(
            datetimes=[timezone.now()],
            dates=[timezone.now().date()],
            times=[timezone.now().time()],
        )
        instance.save()
        loaded = DateTimeArrayModel.objects.get()
        self.assertEqual(instance.datetimes, loaded.datetimes)
        self.assertEqual(instance.dates, loaded.dates)
        self.assertEqual(instance.times, loaded.times)

    def test_tuples(self):
        instance = IntegerArrayModel(field=(1,))
        instance.save()
        loaded = IntegerArrayModel.objects.get()
        self.assertSequenceEqual(instance.field, loaded.field)

    def test_integers_passed_as_strings(self):
        # This checks that get_prep_value is deferred properly
        instance = IntegerArrayModel(field=["1"])
        instance.save()
        loaded = IntegerArrayModel.objects.get()
        self.assertEqual(loaded.field, [1])

    def test_default_null(self):
        instance = NullableIntegerArrayModel()
        instance.save()
        loaded = NullableIntegerArrayModel.objects.get(pk=instance.pk)
        self.assertIsNone(loaded.field)
        self.assertEqual(instance.field, loaded.field)

    def test_null_handling(self):
        instance = NullableIntegerArrayModel(field=None)
        instance.save()
        loaded = NullableIntegerArrayModel.objects.get()
        self.assertEqual(instance.field, loaded.field)

        instance = IntegerArrayModel(field=None)
        with self.assertRaises(IntegrityError):
            instance.save()

    def test_nested(self):
        instance = NestedIntegerArrayModel(field=[[1, 2], [3, 4]])
        instance.save()
        loaded = NestedIntegerArrayModel.objects.get()
        self.assertEqual(instance.field, loaded.field)

    def test_other_array_types(self):
        instance = OtherTypesArrayModel(
            ips=["192.168.0.1", "::1"],
            uuids=[uuid.uuid4()],
            decimals=[decimal.Decimal(1.25), 1.75],
            tags=[Tag(1), Tag(2), Tag(3)],
            json=[{"a": 1}, {"b": 2}],
            int_ranges=[NumericRange(10, 20), NumericRange(30, 40)],
            bigint_ranges=[
                NumericRange(7000000000, 10000000000),
                NumericRange(50000000000, 70000000000),
            ],
        )
        instance.save()
        loaded = OtherTypesArrayModel.objects.get()
        self.assertEqual(instance.ips, loaded.ips)
        self.assertEqual(instance.uuids, loaded.uuids)
        self.assertEqual(instance.decimals, loaded.decimals)
        self.assertEqual(instance.tags, loaded.tags)
        self.assertEqual(instance.json, loaded.json)
        self.assertEqual(instance.int_ranges, loaded.int_ranges)
        self.assertEqual(instance.bigint_ranges, loaded.bigint_ranges)

    def test_null_from_db_value_handling(self):
        instance = OtherTypesArrayModel.objects.create(
            ips=["192.168.0.1", "::1"],
            uuids=[uuid.uuid4()],
            decimals=[decimal.Decimal(1.25), 1.75],
            tags=None,
        )
        instance.refresh_from_db()
        self.assertIsNone(instance.tags)
        self.assertEqual(instance.json, [])
        self.assertIsNone(instance.int_ranges)
        self.assertIsNone(instance.bigint_ranges)

    def test_model_set_on_base_field(self):
        instance = IntegerArrayModel()
        field = instance._meta.get_field("field")
        self.assertEqual(field.model, IntegerArrayModel)
        self.assertEqual(field.base_field.model, IntegerArrayModel)

    def test_nested_nullable_base_field(self):
        instance = NullableIntegerArrayModel.objects.create(
            field_nested=[[None, None], [None, None]],
        )
        self.assertEqual(instance.field_nested, [[None, None], [None, None]])


class TestQuerying(PostgreSQLTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.objs = NullableIntegerArrayModel.objects.bulk_create(
            [
                NullableIntegerArrayModel(order=1, field=[1]),
                NullableIntegerArrayModel(order=2, field=[2]),
                NullableIntegerArrayModel(order=3, field=[2, 3]),
                NullableIntegerArrayModel(order=4, field=[20, 30, 40]),
                NullableIntegerArrayModel(order=5, field=None),
            ]
        )

    def test_bulk_create_with_sized_arrayfield(self):
        objs = WithSizeArrayModel.objects.bulk_create(
            [
                WithSizeArrayModel(field=[1, 2]),
                WithSizeArrayModel(field=[3, 4]),
            ]
        )
        self.assertEqual(objs[0].field, [1, 2])
        self.assertEqual(objs[1].field, [3, 4])

    def test_empty_list(self):
        NullableIntegerArrayModel.objects.create(field=[])
        obj = (
            NullableIntegerArrayModel.objects.annotate(
                empty_array=models.Value([], output_field=ArrayField(models.IntegerField())),
            )
            .filter(field=models.F("empty_array"))
            .get()
        )
        self.assertEqual(obj.field, [])
        self.assertEqual(obj.empty_array, [])

    def test_exact(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__exact=[1]), self.objs[:1]
        )

    def test_exact_null_only_array(self):
        obj = NullableIntegerArrayModel.objects.create(field=[None], field_nested=[None, None])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__exact=[None]), [obj]
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field_nested__exact=[None, None]),
            [obj],
        )

    def test_exact_null_only_nested_array(self):
        obj1 = NullableIntegerArrayModel.objects.create(field_nested=[[None, None]])
        obj2 = NullableIntegerArrayModel.objects.create(
            field_nested=[[None, None], [None, None]],
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field_nested__exact=[[None, None]],
            ),
            [obj1],
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field_nested__exact=[[None, None], [None, None]],
            ),
            [obj2],
        )

    def test_exact_with_expression(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__exact=[Value(1)]),
            self.objs[:1],
        )

    def test_exact_charfield(self):
        instance = CharArrayModel.objects.create(field=["text"])
        self.assertSequenceEqual(CharArrayModel.objects.filter(field=["text"]), [instance])

    def test_exact_nested(self):
        instance = NestedIntegerArrayModel.objects.create(field=[[1, 2], [3, 4]])
        self.assertSequenceEqual(
            NestedIntegerArrayModel.objects.filter(field=[[1, 2], [3, 4]]), [instance]
        )

    def test_isnull(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__isnull=True), self.objs[-1:]
        )

    def test_gt(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__gt=[0]), self.objs[:4]
        )

    def test_lt(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__lt=[2]), self.objs[:1]
        )

    def test_in(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__in=[[1], [2]]),
            self.objs[:2],
        )

    def test_in_subquery(self):
        IntegerArrayModel.objects.create(field=[2, 3])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field__in=IntegerArrayModel.objects.values_list("field", flat=True)
            ),
            self.objs[2:3],
        )

    @unittest.expectedFailure
    def test_in_including_F_object(self):
        # This test asserts that Array objects passed to filters can be
        # constructed to contain F objects. This currently doesn't work as the
        # psycopg mogrify method that generates the ARRAY() syntax is
        # expecting literals, not column references (#27095).
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__in=[[models.F("id")]]),
            self.objs[:2],
        )

    def test_in_as_F_object(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__in=[models.F("field")]),
            self.objs[:4],
        )

    def test_contained_by(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__contained_by=[1, 2]),
            self.objs[:2],
        )

    def test_contained_by_including_F_object(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__contained_by=[models.F("order"), 2]),
            self.objs[:3],
        )

    def test_contains(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__contains=[2]),
            self.objs[1:3],
        )

    def test_contains_subquery(self):
        IntegerArrayModel.objects.create(field=[2, 3])
        inner_qs = IntegerArrayModel.objects.values_list("field", flat=True)
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__contains=inner_qs[:1]),
            self.objs[2:3],
        )
        inner_qs = IntegerArrayModel.objects.filter(field__contains=OuterRef("field"))
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(Exists(inner_qs)),
            self.objs[1:3],
        )

    def test_contains_including_expression(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field__contains=[2, Value(6) / Value(2)],
            ),
            self.objs[2:3],
        )

    def test_icontains(self):
        # Using the __icontains lookup with ArrayField is inefficient.
        instance = CharArrayModel.objects.create(field=["FoO"])
        self.assertSequenceEqual(CharArrayModel.objects.filter(field__icontains="foo"), [instance])

    def test_contains_charfield(self):
        # Regression for #22907
        self.assertSequenceEqual(CharArrayModel.objects.filter(field__contains=["text"]), [])

    def test_contained_by_charfield(self):
        self.assertSequenceEqual(CharArrayModel.objects.filter(field__contained_by=["text"]), [])

    def test_overlap_charfield(self):
        self.assertSequenceEqual(CharArrayModel.objects.filter(field__overlap=["text"]), [])

    def test_overlap_charfield_including_expression(self):
        obj_1 = CharArrayModel.objects.create(field=["TEXT", "lower text"])
        obj_2 = CharArrayModel.objects.create(field=["lower text", "TEXT"])
        CharArrayModel.objects.create(field=["lower text", "text"])
        self.assertSequenceEqual(
            CharArrayModel.objects.filter(
                field__overlap=[
                    Upper(Value("text")),
                    "other",
                ]
            ),
            [obj_1, obj_2],
        )

    def test_overlap_values(self):
        qs = NullableIntegerArrayModel.objects.filter(order__lt=3)
        self.assertCountEqual(
            NullableIntegerArrayModel.objects.filter(
                field__overlap=qs.values_list("field"),
            ),
            self.objs[:3],
        )
        self.assertCountEqual(
            NullableIntegerArrayModel.objects.filter(
                field__overlap=qs.values("field"),
            ),
            self.objs[:3],
        )

    def test_lookups_autofield_array(self):
        qs = (
            NullableIntegerArrayModel.objects.filter(
                field__0__isnull=False,
            )
            .values("field__0")
            .annotate(
                arrayagg=ArrayAgg("id"),
            )
            .order_by("field__0")
        )
        tests = (
            ("contained_by", [self.objs[1].pk, self.objs[2].pk, 0], [2]),
            ("contains", [self.objs[2].pk], [2]),
            ("exact", [self.objs[3].pk], [20]),
            ("overlap", [self.objs[1].pk, self.objs[3].pk], [2, 20]),
        )
        for lookup, value, expected in tests:
            with self.subTest(lookup=lookup):
                self.assertSequenceEqual(
                    qs.filter(
                        **{"arrayagg__" + lookup: value},
                    ).values_list("field__0", flat=True),
                    expected,
                )

    @skipUnlessDBFeature("allows_group_by_select_index")
    def test_group_by_order_by_select_index(self):
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(
                NullableIntegerArrayModel.objects.filter(
                    field__0__isnull=False,
                )
                .values("field__0")
                .annotate(arrayagg=ArrayAgg("id"))
                .order_by("field__0"),
                [
                    {"field__0": 1, "arrayagg": [self.objs[0].pk]},
                    {"field__0": 2, "arrayagg": [self.objs[1].pk, self.objs[2].pk]},
                    {"field__0": 20, "arrayagg": [self.objs[3].pk]},
                ],
            )
        sql = ctx[0]["sql"]
        self.assertIn("GROUP BY 1", sql)
        self.assertIn("ORDER BY 1", sql)

    def test_order_by_arrayagg_index(self):
        qs = (
            NullableIntegerArrayModel.objects.values("order")
            .annotate(ids=ArrayAgg("id"))
            .order_by("-ids__0")
        )
        self.assertQuerySetEqual(
            qs, [{"order": obj.order, "ids": [obj.id]} for obj in reversed(self.objs)]
        )

    def test_index(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0=2), self.objs[1:3]
        )

    def test_index_chained(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0__lt=3), self.objs[0:3]
        )

    def test_index_nested(self):
        instance = NestedIntegerArrayModel.objects.create(field=[[1, 2], [3, 4]])
        self.assertSequenceEqual(NestedIntegerArrayModel.objects.filter(field__0__0=1), [instance])

    @unittest.expectedFailure
    def test_index_used_on_nested_data(self):
        instance = NestedIntegerArrayModel.objects.create(field=[[1, 2], [3, 4]])
        self.assertSequenceEqual(
            NestedIntegerArrayModel.objects.filter(field__0=[1, 2]), [instance]
        )

    def test_index_transform_expression(self):
        expr = RawSQL("string_to_array(%s, ';')", ["1;2"])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field__0=Cast(
                    IndexTransform(1, models.IntegerField, expr),
                    output_field=models.IntegerField(),
                ),
            ),
            self.objs[:1],
        )

    def test_index_annotation(self):
        qs = NullableIntegerArrayModel.objects.annotate(second=models.F("field__1"))
        self.assertCountEqual(
            qs.values_list("second", flat=True),
            [None, None, None, 3, 30],
        )

    def test_overlap(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__overlap=[1, 2]),
            self.objs[0:3],
        )

    def test_len(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__len__lte=2), self.objs[0:3]
        )

    def test_len_empty_array(self):
        obj = NullableIntegerArrayModel.objects.create(field=[])
        self.assertSequenceEqual(NullableIntegerArrayModel.objects.filter(field__len=0), [obj])

    def test_slice(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0_1=[2]), self.objs[1:3]
        )

        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0_2=[2, 3]), self.objs[2:3]
        )

    def test_order_by_index(self):
        more_objs = (
            NullableIntegerArrayModel.objects.create(field=[1, 637]),
            NullableIntegerArrayModel.objects.create(field=[2, 1]),
            NullableIntegerArrayModel.objects.create(field=[3, -98123]),
            NullableIntegerArrayModel.objects.create(field=[4, 2]),
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.order_by("field__1"),
            [
                more_objs[2],
                more_objs[1],
                more_objs[3],
                self.objs[2],
                self.objs[3],
                more_objs[0],
                self.objs[4],
                self.objs[1],
                self.objs[0],
            ],
        )

    @unittest.expectedFailure
    def test_slice_nested(self):
        instance = NestedIntegerArrayModel.objects.create(field=[[1, 2], [3, 4]])
        self.assertSequenceEqual(
            NestedIntegerArrayModel.objects.filter(field__0__0_1=[1]), [instance]
        )

    def test_slice_transform_expression(self):
        expr = RawSQL("string_to_array(%s, ';')", ["9;2;3"])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0_2=SliceTransform(2, 3, expr)),
            self.objs[2:3],
        )

    def test_slice_annotation(self):
        qs = NullableIntegerArrayModel.objects.annotate(
            first_two=models.F("field__0_2"),
        )
        self.assertCountEqual(
            qs.values_list("first_two", flat=True),
            [None, [1], [2], [2, 3], [20, 30]],
        )

    def test_slicing_of_f_expressions(self):
        tests = [
            (F("field")[:2], [1, 2]),
            (F("field")[2:], [3, 4]),
            (F("field")[1:3], [2, 3]),
            (F("field")[3], [4]),
            (F("field")[:3][1:], [2, 3]),  # Nested slicing.
            (F("field")[:3][1], [2]),  # Slice then index.
        ]
        for expression, expected in tests:
            with self.subTest(expression=expression, expected=expected):
                instance = IntegerArrayModel.objects.create(field=[1, 2, 3, 4])
                instance.field = expression
                instance.save()
                instance.refresh_from_db()
                self.assertEqual(instance.field, expected)

    def test_slicing_of_f_expressions_with_annotate(self):
        IntegerArrayModel.objects.create(field=[1, 2, 3])
        annotated = IntegerArrayModel.objects.annotate(
            first_two=F("field")[:2],
            after_two=F("field")[2:],
            random_two=F("field")[1:3],
        ).get()
        self.assertEqual(annotated.first_two, [1, 2])
        self.assertEqual(annotated.after_two, [3])
        self.assertEqual(annotated.random_two, [2, 3])

    def test_slicing_of_f_expressions_with_len(self):
        queryset = NullableIntegerArrayModel.objects.annotate(subarray=F("field")[:1]).filter(
            field__len=F("subarray__len")
        )
        self.assertSequenceEqual(queryset, self.objs[:2])

    def test_usage_in_subquery(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                id__in=NullableIntegerArrayModel.objects.filter(field__len=3)
            ),
            [self.objs[3]],
        )

    def test_enum_lookup(self):
        class TestEnum(enum.Enum):
            VALUE_1 = "value_1"

        instance = ArrayEnumModel.objects.create(array_of_enums=[TestEnum.VALUE_1])
        self.assertSequenceEqual(
            ArrayEnumModel.objects.filter(array_of_enums__contains=[TestEnum.VALUE_1]),
            [instance],
        )

    def test_unsupported_lookup(self):
        msg = "Unsupported lookup '0_bar' for ArrayField or join on the field not permitted."
        with self.assertRaisesMessage(FieldError, msg):
            list(NullableIntegerArrayModel.objects.filter(field__0_bar=[2]))

        msg = "Unsupported lookup '0bar' for ArrayField or join on the field not permitted."
        with self.assertRaisesMessage(FieldError, msg):
            list(NullableIntegerArrayModel.objects.filter(field__0bar=[2]))

    def test_grouping_by_annotations_with_array_field_param(self):
        value = models.Value([1], output_field=ArrayField(models.IntegerField()))
        self.assertEqual(
            NullableIntegerArrayModel.objects.annotate(
                array_length=models.Func(
                    value,
                    1,
                    function="ARRAY_LENGTH",
                    output_field=models.IntegerField(),
                ),
            )
            .values("array_length")
            .annotate(
                count=models.Count("pk"),
            )
            .get()["array_length"],
            1,
        )

    def test_filter_by_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.filter(
            field__len=models.OuterRef("field__len"),
        ).values("field")
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.alias(
                same_sized_fields=ArraySubquery(inner_qs),
            ).filter(same_sized_fields__len__gt=1),
            self.objs[0:2],
        )

    def test_annotated_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.exclude(pk=models.OuterRef("pk")).values(
            "order"
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.annotate(
                sibling_ids=ArraySubquery(inner_qs),
            )
            .get(order=1)
            .sibling_ids,
            [2, 3, 4, 5],
        )

    def test_group_by_with_annotated_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.exclude(pk=models.OuterRef("pk")).values(
            "order"
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.annotate(
                sibling_ids=ArraySubquery(inner_qs),
                sibling_count=models.Max("sibling_ids__len"),
            ).values_list("sibling_count", flat=True),
            [len(self.objs) - 1] * len(self.objs),
        )

    def test_annotated_ordered_array_subquery(self):
        inner_qs = NullableIntegerArrayModel.objects.order_by("-order").values("order")
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.annotate(
                ids=ArraySubquery(inner_qs),
            )
            .first()
            .ids,
            [5, 4, 3, 2, 1],
        )

    def test_annotated_array_subquery_with_json_objects(self):
        inner_qs = NullableIntegerArrayModel.objects.exclude(pk=models.OuterRef("pk")).values(
            json=JSONObject(order="order", field="field")
        )
        siblings_json = (
            NullableIntegerArrayModel.objects.annotate(
                siblings_json=ArraySubquery(inner_qs),
            )
            .values_list("siblings_json", flat=True)
            .get(order=1)
        )
        self.assertSequenceEqual(
            siblings_json,
            [
                {"field": [2], "order": 2},
                {"field": [2, 3], "order": 3},
                {"field": [20, 30, 40], "order": 4},
                {"field": None, "order": 5},
            ],
        )


class TestDateTimeExactQuerying(PostgreSQLTestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.datetimes = [now]
        cls.dates = [now.date()]
        cls.times = [now.time()]
        cls.objs = [
            DateTimeArrayModel.objects.create(
                datetimes=cls.datetimes, dates=cls.dates, times=cls.times
            ),
        ]

    def test_exact_datetimes(self):
        self.assertSequenceEqual(
            DateTimeArrayModel.objects.filter(datetimes=self.datetimes), self.objs
        )

    def test_exact_dates(self):
        self.assertSequenceEqual(DateTimeArrayModel.objects.filter(dates=self.dates), self.objs)

    def test_exact_times(self):
        self.assertSequenceEqual(DateTimeArrayModel.objects.filter(times=self.times), self.objs)


class TestOtherTypesExactQuerying(PostgreSQLTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ips = ["192.168.0.1", "::1"]
        cls.uuids = [uuid.uuid4()]
        cls.decimals = [decimal.Decimal(1.25), 1.75]
        cls.tags = [Tag(1), Tag(2), Tag(3)]
        cls.objs = [
            OtherTypesArrayModel.objects.create(
                ips=cls.ips,
                uuids=cls.uuids,
                decimals=cls.decimals,
                tags=cls.tags,
            )
        ]

    def test_exact_ip_addresses(self):
        self.assertSequenceEqual(OtherTypesArrayModel.objects.filter(ips=self.ips), self.objs)

    def test_exact_uuids(self):
        self.assertSequenceEqual(OtherTypesArrayModel.objects.filter(uuids=self.uuids), self.objs)

    def test_exact_decimals(self):
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(decimals=self.decimals), self.objs
        )

    def test_exact_tags(self):
        self.assertSequenceEqual(OtherTypesArrayModel.objects.filter(tags=self.tags), self.objs)


@isolate_apps("postgres_tests")
class TestChecks(PostgreSQLSimpleTestCase):
    def test_field_checks(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.CharField(max_length=-1))

        model = MyModel()
        errors = model.check()
        self.assertEqual(len(errors), 1)
        # The inner CharField has a non-positive max_length.
        self.assertEqual(errors[0].id, "postgres.E001")
        self.assertIn("max_length", errors[0].msg)

    def test_invalid_base_fields(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.ManyToManyField("postgres_tests.IntegerArrayModel"))

        model = MyModel()
        errors = model.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "postgres.E002")

    def test_invalid_default(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.IntegerField(), default=[])

        model = MyModel()
        self.assertEqual(
            model.check(),
            [
                checks.Warning(
                    msg=(
                        "ArrayField default should be a callable instead of an "
                        "instance so that it's not shared between all field "
                        "instances."
                    ),
                    hint="Use a callable instead, e.g., use `list` instead of `[]`.",
                    obj=MyModel._meta.get_field("field"),
                    id="fields.E010",
                )
            ],
        )

    def test_valid_default(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.IntegerField(), default=list)

        model = MyModel()
        self.assertEqual(model.check(), [])

    def test_valid_default_none(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.IntegerField(), default=None)

        model = MyModel()
        self.assertEqual(model.check(), [])

    def test_nested_field_checks(self):
        """
        Nested ArrayFields are permitted.
        """

        class MyModel(PostgreSQLModel):
            field = ArrayField(ArrayField(models.CharField(max_length=-1)))

        model = MyModel()
        errors = model.check()
        self.assertEqual(len(errors), 1)
        # The inner CharField has a non-positive max_length.
        self.assertEqual(errors[0].id, "postgres.E001")
        self.assertIn("max_length", errors[0].msg)

    def test_choices_tuple_list(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(
                models.CharField(max_length=16),
                choices=[
                    [
                        "Media",
                        [(["vinyl", "cd"], "Audio"), (("vhs", "dvd"), "Video")],
                    ],
                    (["mp3", "mp4"], "Digital"),
                ],
            )

        self.assertEqual(MyModel._meta.get_field("field").check(), [])


@unittest.skipUnless(connection.vendor == "postgresql", "PostgreSQL specific tests")
class TestMigrations(TransactionTestCase):
    available_apps = ["postgres_tests"]

    def test_deconstruct(self):
        field = ArrayField(models.IntegerField())
        name, path, args, kwargs = field.deconstruct()
        new = ArrayField(*args, **kwargs)
        self.assertEqual(type(new.base_field), type(field.base_field))
        self.assertIsNot(new.base_field, field.base_field)

    def test_deconstruct_with_size(self):
        field = ArrayField(models.IntegerField(), size=3)
        name, path, args, kwargs = field.deconstruct()
        new = ArrayField(*args, **kwargs)
        self.assertEqual(new.size, field.size)

    def test_deconstruct_args(self):
        field = ArrayField(models.CharField(max_length=20))
        name, path, args, kwargs = field.deconstruct()
        new = ArrayField(*args, **kwargs)
        self.assertEqual(new.base_field.max_length, field.base_field.max_length)

    def test_subclass_deconstruct(self):
        field = ArrayField(models.IntegerField())
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "djrm.contrib.postgres.fields.ArrayField")

        field = ArrayFieldSubclass()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "postgres_tests.models.ArrayFieldSubclass")

    @override_settings(
        MIGRATION_MODULES={
            "postgres_tests": "postgres_tests.array_default_migrations",
        }
    )
    def test_adding_field_with_default(self):
        # See #22962
        table_name = "postgres_tests_integerarraydefaultmodel"
        with connection.cursor() as cursor:
            self.assertNotIn(table_name, connection.introspection.table_names(cursor))
        call_command("migrate", "postgres_tests", verbosity=0)
        with connection.cursor() as cursor:
            self.assertIn(table_name, connection.introspection.table_names(cursor))
        call_command("migrate", "postgres_tests", "zero", verbosity=0)
        with connection.cursor() as cursor:
            self.assertNotIn(table_name, connection.introspection.table_names(cursor))

    @override_settings(
        MIGRATION_MODULES={
            "postgres_tests": "postgres_tests.array_index_migrations",
        }
    )
    def test_adding_arrayfield_with_index(self):
        """
        ArrayField shouldn't have varchar_patterns_ops or text_patterns_ops indexes.
        """
        table_name = "postgres_tests_chartextarrayindexmodel"
        call_command("migrate", "postgres_tests", verbosity=0)
        with connection.cursor() as cursor:
            like_constraint_columns_list = [
                v["columns"]
                for k, v in list(
                    connection.introspection.get_constraints(cursor, table_name).items()
                )
                if k.endswith("_like")
            ]
            # Only the CharField should have a LIKE index.
        self.assertEqual(like_constraint_columns_list, [["char2"]])
        # All fields should have regular indexes.
        with connection.cursor() as cursor:
            indexes = [
                c["columns"][0]
                for c in connection.introspection.get_constraints(cursor, table_name).values()
                if c["index"] and len(c["columns"]) == 1
            ]
        self.assertIn("char", indexes)
        self.assertIn("char2", indexes)
        self.assertIn("text", indexes)
        call_command("migrate", "postgres_tests", "zero", verbosity=0)
        with connection.cursor() as cursor:
            self.assertNotIn(table_name, connection.introspection.table_names(cursor))


class TestSerialization(PostgreSQLSimpleTestCase):
    test_data = (
        '[{"fields": {"field": "[\\"1\\", \\"2\\", null]"}, '
        '"model": "postgres_tests.integerarraymodel", "pk": null}]'
    )

    def test_dumping(self):
        instance = IntegerArrayModel(field=[1, 2, None])
        data = serializers.serialize("json", [instance])
        self.assertEqual(json.loads(data), json.loads(self.test_data))

    def test_loading(self):
        instance = list(serializers.deserialize("json", self.test_data))[0].object
        self.assertEqual(instance.field, [1, 2, None])


class TestStringSerialization(PostgreSQLSimpleTestCase):
    field_values = [["Django", "Python", None], ["Джанго", "פייתון", None, "król"]]

    @staticmethod
    def create_json_data(array_field_value):
        fields = {"field": json.dumps(array_field_value, ensure_ascii=False)}
        return json.dumps(
            [{"model": "postgres_tests.chararraymodel", "pk": None, "fields": fields}]
        )

    def test_encode(self):
        for field_value in self.field_values:
            with self.subTest(field_value=field_value):
                instance = CharArrayModel(field=field_value)
                data = serializers.serialize("json", [instance])
                json_data = self.create_json_data(field_value)
                self.assertEqual(json.loads(data), json.loads(json_data))

    def test_decode(self):
        for field_value in self.field_values:
            with self.subTest(field_value=field_value):
                json_data = self.create_json_data(field_value)
                instance = list(serializers.deserialize("json", json_data))[0].object
                self.assertEqual(instance.field, field_value)


class TestValidation(PostgreSQLSimpleTestCase):
    def test_unbounded(self):
        field = ArrayField(models.IntegerField())
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean([1, None], None)
        self.assertEqual(cm.exception.code, "item_invalid")
        self.assertEqual(
            cm.exception.message % cm.exception.params,
            "Item 2 in the array did not validate: This field cannot be null.",
        )

    def test_blank_true(self):
        field = ArrayField(models.IntegerField(blank=True, null=True))
        # This should not raise a validation error
        field.clean([1, None], None)

    def test_with_size(self):
        field = ArrayField(models.IntegerField(), size=3)
        field.clean([1, 2, 3], None)
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean([1, 2, 3, 4], None)
        self.assertEqual(
            cm.exception.messages[0],
            "List contains 4 items, it should contain no more than 3.",
        )

    def test_with_size_singular(self):
        field = ArrayField(models.IntegerField(), size=1)
        field.clean([1], None)
        msg = "List contains 2 items, it should contain no more than 1."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean([1, 2], None)

    def test_nested_array_mismatch(self):
        field = ArrayField(ArrayField(models.IntegerField()))
        field.clean([[1, 2], [3, 4]], None)
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean([[1, 2], [3, 4, 5]], None)
        self.assertEqual(cm.exception.code, "nested_array_mismatch")
        self.assertEqual(cm.exception.messages[0], "Nested arrays must have the same length.")

    def test_with_base_field_error_params(self):
        field = ArrayField(models.CharField(max_length=2))
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean(["abc"], None)
        self.assertEqual(len(cm.exception.error_list), 1)
        exception = cm.exception.error_list[0]
        self.assertEqual(
            exception.message,
            "Item 1 in the array did not validate: Ensure this value has at most 2 "
            "characters (it has 3).",
        )
        self.assertEqual(exception.code, "item_invalid")
        self.assertEqual(
            exception.params,
            {"nth": 1, "value": "abc", "limit_value": 2, "show_value": 3},
        )

    def test_with_validators(self):
        field = ArrayField(models.IntegerField(validators=[validators.MinValueValidator(1)]))
        field.clean([1, 2], None)
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean([0], None)
        self.assertEqual(len(cm.exception.error_list), 1)
        exception = cm.exception.error_list[0]
        self.assertEqual(
            exception.message,
            "Item 1 in the array did not validate: Ensure this value is greater than "
            "or equal to 1.",
        )
        self.assertEqual(exception.code, "item_invalid")
        self.assertEqual(
            exception.params, {"nth": 1, "value": 0, "limit_value": 1, "show_value": 0}
        )
