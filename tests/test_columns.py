import pickle
import unittest
from decimal import Decimal

from agate import Table
from agate.data_types import Number, Text
from agate.utils import _missing


class TestColumn(unittest.TestCase):
    def setUp(self):
        self.rows = (
            (1, 2, 'a'),
            (2, 3, 'b'),
            (None, 4, 'c')
        )

        self.number_type = Number()
        self.text_type = Text()

        self.column_names = ['one', 'two', 'three']
        self.column_types = [self.number_type, self.number_type, self.text_type]

        self.table = Table(self.rows, self.column_names, self.column_types)

    def test_index(self):
        self.assertEqual(self.table.columns['one'].index, 0)
        self.assertEqual(self.table.columns['two'].index, 1)
        self.assertEqual(self.table.columns['three'].index, 2)

    def test_name(self):
        self.assertEqual(self.table.columns['one'].name, 'one')

    def test_data_type(self):
        self.assertIs(self.table.columns['one'].data_type, self.number_type)

    def test_pickleable(self):
        pickle.dumps(self.table.columns['one'])

    def test_row_names(self):
        table = Table(self.rows, self.column_names, self.column_types, row_names='three')
        column = table.columns['one']

        self.assertSequenceEqual(column._keys, ['a', 'b', 'c'])
        self.assertEqual(column['b'], 2)

    def test_keys(self):
        table = Table(self.rows, self.column_names, self.column_types, row_names='three')

        self.assertIs(self.table.columns['one'].keys(), None)
        self.assertSequenceEqual(table.columns['one'].keys(), ['a', 'b', 'c'])

    def test_values(self):
        self.assertSequenceEqual(
            self.table.columns['one'].values(),
            [Decimal('1'), Decimal('2'), None]
        )

    def test_values_distinct(self):
        rows = (
            (1, 2),
            (2, 3),
            (None, 3)
        )

        table = Table(rows, ('one', 'two'), [self.number_type, self.number_type])
        self.assertSequenceEqual(
            table.columns['two'].values_distinct(),
            [Decimal('2'), Decimal('3')]
        )

    def test_items(self):
        table = Table(self.rows, self.column_names, self.column_types, row_names='three')

        self.assertSequenceEqual(table.columns['one'].items(), [
            ('a', Decimal('1')),
            ('b', Decimal('2')),
            ('c', None)
        ])

    def test_dict(self):
        table = Table(self.rows, self.column_names, self.column_types, row_names='three')

        self.assertDictEqual(table.columns['one'].dict(), {
            'a': Decimal('1'),
            'b': Decimal('2'),
            'c': None
        })

    def test_values_without_nulls(self):
        self.assertSequenceEqual(
            self.table.columns['one'].values_without_nulls(),
            [Decimal('1'), Decimal('2')]
        )

    def test_values_sorted(self):
        rows = (
            (2, 2, 'a'),
            (None, 3, 'b'),
            (1, 4, 'c')
        )

        table = Table(rows, self.column_names, self.column_types)

        self.assertSequenceEqual(
            table.columns['one'].values_sorted(),
            [Decimal('1'), Decimal('2'), None]
        )

    def test_values_without_nulls_sorted(self):
        rows = (
            (2, 2, 'a'),
            (None, 3, 'b'),
            (1, 4, 'c')
        )

        table = Table(rows, self.column_names, self.column_types)

        self.assertSequenceEqual(
            table.columns['one'].values_without_nulls_sorted(),
            [Decimal('1'), Decimal('2')]
        )

    def test_values_are_prepared_once_and_reused(self):
        column = self.table.columns['one']

        first = column.values()
        second = column.values()

        self.assertIs(first, second)
        self.assertIs(column._memo_values, first)

    def test_index_access_reuses_prepared_values(self):
        column = self.table.columns['one']
        values = column.values()

        for i in range(len(values)):
            self.assertEqual(column[i], values[i])

        self.assertIs(column.values(), values)

    def test_empty_column_caches_empty_results(self):
        table = Table([], self.column_names, self.column_types)
        column = table.columns['one']

        self.assertEqual(column.values(), ())
        self.assertIs(column.values(), column.values())
        self.assertEqual(column.values_without_nulls(), ())
        self.assertIs(
            column.values_without_nulls(),
            column.values_without_nulls()
        )

    def test_columns_keep_separate_caches(self):
        first = self.table.columns['one']
        second = self.table.columns['two']

        first.values()

        self.assertIsNot(first._memo_values, _missing)
        self.assertIs(second._memo_values, _missing)

    def test_sorted_values_return_fresh_lists(self):
        column = self.table.columns['one']
        expected = column.values_sorted()

        self.assertIsInstance(expected, list)

        returned = column.values_sorted()
        returned.reverse()
        returned.append('junk')

        self.assertEqual(column.values_sorted(), expected)
        self.assertIsInstance(column._memo__values_sorted, tuple)

        without_nulls = column.values_without_nulls_sorted()
        without_nulls.append('junk')

        self.assertEqual(
            column.values_without_nulls_sorted(),
            [Decimal('1'), Decimal('2')]
        )

    def test_pickle_clears_prepared_values(self):
        column = self.table.columns['one']
        column.values()
        column.values_sorted()

        restored = pickle.loads(pickle.dumps(column))

        self.assertIs(restored._memo_values, _missing)
        self.assertIs(restored._memo__values_sorted, _missing)
        self.assertIs(restored._name_index, _missing)

        self.assertSequenceEqual(restored.values(), column.values())
        self.assertSequenceEqual(restored.values_sorted(), column.values_sorted())

    def test_pickle_keeps_name_access_working(self):
        table = Table(self.rows, self.column_names, self.column_types, row_names='three')
        column = table.columns['one']
        self.assertEqual(column['b'], Decimal('2'))

        restored = pickle.loads(pickle.dumps(column))

        self.assertEqual(restored['b'], Decimal('2'))
        self.assertSequenceEqual(restored.dict(), column.dict())
