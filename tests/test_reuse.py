"""
Tests for the per-object lazy preparation and reuse of column values and
name lookups.

These tests use access counting rather than wall-clock timings: they assert
how many times the underlying rows and key mappings are actually visited when
the same column or row is read repeatedly.
"""
import pickle
import sys
import unittest
from decimal import Decimal

from agate import Table
from agate.data_types import Number, Text
from agate.mapped_sequence import MappedSequence
from agate.rows import Row
from agate.utils import _missing


class CountingRow(Row):
    """
    A row that counts integer (positional) reads of its values. Column value
    preparation goes through these reads, so the counter measures how many
    row visits a column requires.
    """
    accesses = 0

    def __getitem__(self, key):
        if type(key) is int:
            type(self).accesses += 1

        return super().__getitem__(key)


class CountingMappedSequence(MappedSequence):
    """
    A sequence that counts how often its name-to-index mapping is rebuilt.
    """
    builds = 0

    def _get_name_index(self):
        before = self._name_index
        result = super()._get_name_index()

        if before is not result:
            type(self).builds += 1

        return result


class TestColumnValueReuse(unittest.TestCase):
    def setUp(self):
        self.row_count = 1000
        self.rows = [tuple(range(4)) for _ in range(self.row_count)]
        self.column_names = ('one', 'two', 'three', 'four')
        self.column_types = [Number(), Number(), Number(), Number()]

        table = Table(self.rows, self.column_names, self.column_types)
        counting_rows = [CountingRow(row.values(), row.keys()) for row in table.rows]
        self.table = Table(counting_rows, self.column_names, self.column_types, _is_fork=True)

    def tearDown(self):
        CountingRow.accesses = 0

    def test_values_loaded_once_across_repeated_reads(self):
        column = self.table.columns['one']

        for _ in range(8):
            column.values()

        # Eight reads cost one pass over the rows, not eight passes.
        self.assertEqual(CountingRow.accesses, self.row_count)
        self.assertIs(column._memo_values, column.values())

    def test_index_and_name_access_reuse_loaded_values(self):
        column = self.table.columns['one']
        column.values()

        CountingRow.accesses = 0

        for i in range(0, self.row_count, 25):
            self.assertEqual(column[i], column.values()[i])

        self.assertEqual(CountingRow.accesses, 0)

    def test_derived_value_tuples_share_one_row_pass(self):
        column = self.table.columns['one']

        column.values_distinct()
        column.values_without_nulls()
        column.values_sorted()
        column.values_without_nulls_sorted()

        # All four derived views are built on the same prepared value tuple.
        self.assertEqual(CountingRow.accesses, self.row_count)

    def test_empty_column_is_not_recomputed(self):
        table = Table([], self.column_names, self.column_types)
        column = table.columns['one']

        first = column.values()
        second = column.values()

        self.assertEqual(first, ())
        # An empty result is a cached result, not a reason to prepare again.
        self.assertIs(first, second)
        self.assertIsNot(column._memo_values, _missing)

        self.assertEqual(column.values_without_nulls(), ())
        self.assertIs(column.values_without_nulls(), column.values_without_nulls())

    def test_caches_are_isolated_between_columns(self):
        first = self.table.columns['one']
        second = self.table.columns['two']

        first.values()

        self.assertIsNot(first._memo_values, _missing)
        self.assertIs(second._memo_values, _missing)

        CountingRow.accesses = 0
        second.values()
        self.assertEqual(CountingRow.accesses, self.row_count)

    def test_caches_are_isolated_between_tables(self):
        other = Table(self.rows, self.column_names, self.column_types)

        self.table.columns['one'].values()

        column = other.columns['one']
        self.assertIs(column._memo_values, _missing)

        CountingRow.accesses = 0
        column.values()
        self.assertEqual(CountingRow.accesses, 0)

    def test_forked_tables_prepare_their_own_columns(self):
        forked = self.table.where(lambda row: row['one'] > 5)

        # The fork gets new Column objects with no prepared values, even
        # though it reuses the same Row instances.
        self.assertIs(forked.columns['one']._memo_values, _missing)
        self.assertIsNot(forked.columns['one'], self.table.columns['one'])

        CountingRow.accesses = 0
        forked.columns['one'].values()
        self.assertEqual(CountingRow.accesses, len(forked.rows))

    def test_no_module_level_cache_accumulates(self):
        import agate.columns as columns_module
        import agate.mapped_sequence as mapped_module

        for module in (columns_module, mapped_module):
            for name, value in vars(module).items():
                if name.startswith('__'):
                    continue
                self.assertFalse(
                    isinstance(value, (dict, list, set)) and len(value) > 0,
                    f'{module.__name__}.{name} looks like a growing global cache'
                )

    def test_discarded_table_releases_its_caches(self):
        table = Table(self.rows, self.column_names, self.column_types)
        row = table.rows[0]
        row['one']

        prepared_lookup = row._name_index
        self.assertIn('one', prepared_lookup)
        refcount_with_table_alive = sys.getrefcount(prepared_lookup)

        del table, row

        # The prepared lookup was reachable only through the row's slot; once
        # the table and row are gone, dropping the local itself frees it.
        import gc
        gc.collect()
        self.assertEqual(sys.getrefcount(prepared_lookup), refcount_with_table_alive - 1)


class TestNameLookupReuse(unittest.TestCase):
    def setUp(self):
        self.keys = ('one', 'two', 'three', 'four')
        self.values = (1, 2, 3, 4)

    def tearDown(self):
        CountingMappedSequence.builds = 0

    def test_name_index_built_once_for_repeated_lookups(self):
        sequence = CountingMappedSequence(self.values, self.keys)

        for _ in range(10):
            self.assertEqual(sequence['two'], 2)
            self.assertEqual(sequence.get('four'), 4)

        self.assertEqual(CountingMappedSequence.builds, 1)

    def test_each_row_keeps_its_own_lookup(self):
        table = Table([
            (1, 2, 'a'),
            (3, 4, 'b')
        ], ('one', 'two', 'three'), [Number(), Number(), Text()])

        first = table.rows[0]
        second = table.rows[1]

        first['one']
        second['one']

        self.assertIsNot(first._name_index, second._name_index)
        self.assertEqual(first._name_index, second._name_index)

    def test_table_columns_and_rows_use_separate_lookups(self):
        table = Table([
            (1, 2, 'a')
        ], ('one', 'two', 'three'), [Number(), Number(), Text()], row_names=('r1',))

        table.columns['one']
        table.rows['r1']

        self.assertEqual(set(table.columns._name_index), {'one', 'two', 'three'})
        self.assertEqual(set(table.rows._name_index), {'r1'})

    def test_lookup_is_lazy(self):
        sequence = MappedSequence(self.values, self.keys)

        self.assertIs(sequence._name_index, _missing)

        # Index reads never need the name mapping.
        sequence[0]
        sequence.values()
        self.assertIs(sequence._name_index, _missing)

        sequence['one']
        self.assertIsNot(sequence._name_index, _missing)

    def test_mutable_external_keys_are_observed(self):
        keys = ['one', 'two', 'three', 'four']
        sequence = CountingMappedSequence(self.values, keys)

        self.assertEqual(sequence['two'], 2)
        self.assertEqual(CountingMappedSequence.builds, 1)

        # Repeated reads reuse the prepared mapping.
        sequence['three']
        self.assertEqual(CountingMappedSequence.builds, 1)

        # The caller mutates the key list it passed in; the current name
        # relationship must become visible, rebuilding the mapping once.
        keys[1] = 'renamed'
        self.assertEqual(sequence['renamed'], 2)
        self.assertEqual(CountingMappedSequence.builds, 2)

        with self.assertRaises(KeyError):
            sequence['two']

        # Afterwards reads are cached again.
        sequence['renamed']
        self.assertEqual(CountingMappedSequence.builds, 2)

    def test_tuple_key_replacement_is_observed(self):
        sequence = CountingMappedSequence(self.values, self.keys)
        sequence['one']

        # Replacing the key tuple (different identity and length) rebuilds.
        sequence._keys = ('one', 'two', 'three')
        with self.assertRaises(KeyError):
            sequence['four']
        self.assertEqual(CountingMappedSequence.builds, 2)

        sequence._keys = ('uno', 'dos', 'tres', 'cuatro')
        self.assertEqual(sequence['uno'], 1)
        self.assertEqual(CountingMappedSequence.builds, 3)

    def test_no_keys_raises_keyerror_without_caching(self):
        sequence = MappedSequence(self.values)

        with self.assertRaises(KeyError):
            sequence.dict()

        with self.assertRaises(KeyError):
            sequence['one']

        self.assertIs(sequence._name_index, _missing)


class TestReturnValueCompatibility(unittest.TestCase):
    def setUp(self):
        self.table = Table([
            (2, 2, 'a'),
            (None, 3, 'b'),
            (1, 4, 'c')
        ], ('one', 'two', 'three'), [Number(), Number(), Text()])

    def test_sorted_values_remain_lists(self):
        column = self.table.columns['one']

        self.assertIsInstance(column.values_sorted(), list)
        self.assertIsInstance(column.values_without_nulls_sorted(), list)

    def test_mutating_sorted_list_does_not_pollute_later_reads(self):
        column = self.table.columns['one']
        expected = column.values_sorted()

        returned = column.values_sorted()
        returned.reverse()
        returned.append('junk')

        self.assertEqual(column.values_sorted(), expected)

        # The stored cache itself is immutable.
        self.assertIsInstance(column._memo__values_sorted, tuple)

    def test_mutating_dict_does_not_pollute_sequence(self):
        row = self.table.rows[0]

        first = row.dict()
        first['one'] = 999
        first['new'] = 'x'

        second = row.dict()
        self.assertNotIn('new', second)
        self.assertEqual(second['one'], row.values()[0])
        self.assertIsNot(first, second)

        named = Table(
            [(1, 'a')], ('one', 'label'), [Number(), Text()], row_names=('r1',)
        )
        column_dict = named.columns['one'].dict()
        column_dict['r1'] = 999

        self.assertEqual(named.columns['one'].dict()['r1'], Decimal('1'))
        self.assertEqual(named.columns['one']['r1'], Decimal('1'))

    def test_tuple_return_values_retain_their_types(self):
        column = self.table.columns['one']

        self.assertIsInstance(column.values(), tuple)
        self.assertIsInstance(column.values_distinct(), tuple)
        self.assertIsInstance(column.values_without_nulls(), tuple)

        # Rows and the columns container are keyed, so items() works there
        # and stays a tuple. (Columns or rows without keys raise the same
        # TypeError for items() they always did.)
        named = self.table.rows[0]
        self.assertIsInstance(named.items(), tuple)
        self.assertIsInstance(self.table.columns.items(), tuple)

        named_rows = Table(
            [(1, 2)], ('one', 'two'), [Number(), Number()], row_names=('r1',)
        )
        self.assertIsInstance(named_rows.rows.items(), tuple)
        self.assertIsInstance(named_rows.columns['one'].items(), tuple)

    def test_duplicate_names_resolve_last_value(self):
        row = Row((1, 2, 3), ('name', 'name', 'other'))

        self.assertEqual(row['name'], 2)
        self.assertEqual(row.dict()['name'], 2)
        self.assertEqual(row.get('other'), 3)

    def test_null_ordering_is_unchanged(self):
        column = self.table.columns['one']

        self.assertEqual(
            column.values_sorted(),
            [Decimal('1'), Decimal('2'), None]
        )
        self.assertEqual(
            column.values_without_nulls_sorted(),
            [Decimal('1'), Decimal('2')]
        )

    def test_pickle_roundtrip_discards_lookup_state(self):
        row = self.table.rows[0]
        row['one']
        column = self.table.columns['one']
        column.values()
        column.values_sorted()

        restored_row = pickle.loads(pickle.dumps(row))
        restored_column = pickle.loads(pickle.dumps(column))

        self.assertIs(restored_row._name_index, _missing)
        self.assertIs(restored_column._memo_values, _missing)
        self.assertIs(restored_column._name_index, _missing)

        # Restored objects still behave correctly and lazily rebuild.
        self.assertEqual(restored_row['one'], row['one'])
        self.assertEqual(restored_column.values(), column.values())
        self.assertEqual(restored_column.values_sorted(), column.values_sorted())

    def test_pickle_then_rename_does_not_reuse_stale_lookup(self):
        sequence = MappedSequence((1, 2), ('one', 'two'))
        sequence['one']

        restored = pickle.loads(pickle.dumps(sequence))
        restored._keys = ('uno', 'dos')

        self.assertEqual(restored['uno'], 1)
        with self.assertRaises(KeyError):
            restored['one']

    def test_serialized_values_are_unchanged(self):
        import io
        import json

        csv_buffer = io.StringIO()
        self.table.to_csv(csv_buffer)
        csv_buffer.seek(0)
        restored = Table.from_csv(csv_buffer, column_types=[Number(), Number(), Text()])

        self.assertRowsEqual(restored.rows, self.table.rows)

        json_buffer = io.StringIO()
        self.table.to_json(json_buffer)
        payload = json.loads(json_buffer.getvalue())
        self.assertEqual([row['one'] for row in payload], [2, None, 1])

    def assertRowsEqual(self, actual, expected):
        self.assertEqual(
            [tuple(row.values()) for row in actual],
            [tuple(row.values()) for row in expected]
        )
