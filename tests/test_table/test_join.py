from agate import Table
from agate.data_types import Number, Text
from agate.testcase import AgateTestCase


class TestJoin(AgateTestCase):
    def setUp(self):
        self.left_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (None, 2, 'c')
        )

        self.right_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (None, 2, 'c')
        )

        self.number_type = Number()
        self.text_type = Text()

        self.left_column_names = ['one', 'two', 'three']
        self.right_column_names = ['four', 'five', 'six']
        self.column_types = [self.number_type, self.number_type, self.text_type]

        self.left = Table(self.left_rows, self.left_column_names, self.column_types)
        self.right = Table(self.right_rows, self.right_column_names, self.column_types)

    def test_join(self):
        new_table = self.left.join(self.right, 'one', 'four')

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (2, 3, 'b', 3, 'b'),
            (None, 2, 'c', 2, 'c')
        ])

    def test_join_column_indicies(self):
        new_table = self.left.join(self.right, 0, 0)

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (2, 3, 'b', 3, 'b'),
            (None, 2, 'c', 2, 'c')
        ])

    def test_join_match_multiple(self):
        left_rows = (
            (1, 4, 'a'),
            (2, 3, 'b')
        )

        right_rows = (
            (1, 1, 'a'),
            (1, 2, 'a'),
            (2, 2, 'b')
        )

        left = Table(left_rows, self.left_column_names, self.column_types)
        right = Table(right_rows, self.right_column_names, self.column_types)
        new_table = left.join(right, 'one', 'five')

        self.assertIsNot(new_table, left)
        self.assertIsNot(new_table, right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 'a'),
            (2, 3, 'b', 1, 'a'),
            (2, 3, 'b', 2, 'b')
        ])

    def test_join2(self):
        new_table = self.left.join(self.right, 'one', 'five')

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', None, None),
            (2, 3, 'b', None, 'c'),
            (None, 2, 'c', None, None)
        ])

    def test_join_same_column_name(self):
        right_column_names = ['four', 'one', 'six']

        right = Table(self.right_rows, right_column_names, self.column_types)

        new_table = self.left.join(right, 'one')

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', None, None),
            (2, 3, 'b', None, 'c'),
            (None, 2, 'c', None, None)
        ])

    def test_join_multiple_columns(self):
        new_table = self.left.join(
            self.right,
            ['two', 'three'],
            ['five', 'six']
        )

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number])
        self.assertRows(new_table, [
            (1, 4, 'a', 1),
            (2, 3, 'b', 2),
            (None, 2, 'c', None)
        ])

    def test_join_multiple_column_indices(self):
        new_table = self.left.join(self.right, [1, 2], [1, 2])

        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number])
        self.assertRows(new_table, [
            (1, 4, 'a', 1),
            (2, 3, 'b', 2),
            (None, 2, 'c', None)
        ])

    def test_join_identical_columns(self):
        right = Table([(1, 1, 'a'), (2, 2, 'b')], self.right_column_names, self.column_types)
        new_table = self.left.join(right, 'one', 'five')

        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 'a'),
            (2, 3, 'b', 2, 'b'),
            (None, 2, 'c', None, None)
        ])

    def test_join_func(self):
        new_table = self.left.join(
            self.right,
            lambda left: '%i%s' % (left['two'], left['three']),
            lambda right: '%i%s' % (right['five'], right['six'])
        )

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', 2, 3, 'b'),
            (None, 2, 'c', None, 2, 'c')
        ])

    def test_join_column_does_not_exist(self):
        with self.assertRaises(KeyError):
            self.left.join(self.right, 'one', 'seven')

    def test_inner_join(self):
        new_table = self.left.join(self.right, 'one', 'four', inner=True)

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (2, 3, 'b', 3, 'b'),
            (None, 2, 'c', 2, 'c')
        ])

    def test_inner_join2(self):
        new_table = self.left.join(self.right, 'one', 'five', inner=True)

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (2, 3, 'b', None, 'c')
        ])

    def test_inner_join_same_column_name(self):
        right_column_names = ['four', 'one', 'six']

        right = Table(self.right_rows, right_column_names, self.column_types)

        new_table = self.left.join(right, 'one', inner=True)

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (2, 3, 'b', None, 'c')
        ])

    def test_inner_join_func(self):
        new_table = self.left.join(
            self.right,
            lambda left: '%i%s' % (left['two'], left['three']),
            lambda right: '%i%s' % (right['five'], right['six']),
            inner=True
        )

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a')
        ])

    def test_join_with_row_names(self):
        left = Table(self.left_rows, self.left_column_names, self.column_types, row_names='three')
        new_table = left.join(self.right, 'one', 'four')

        self.assertRowNames(new_table, ('a', 'b', 'c'))

    def test_join_require_match(self):
        with self.assertRaises(ValueError):
            self.left.join(self.right, 'one', 'five', require_match=True)

        with self.assertRaises(ValueError):
            self.left.join(self.right, 'one', 'five', require_match=True)

        self.left.join(self.right, 'one', 'four', require_match=True)

    def test_join_multiple_columns_require_match(self):
        right = Table([(1, 4, 'a')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError):
            self.left.join(right, ['two', 'three'], ['five', 'six'], require_match=True)

    def test_join_columns_kwarg(self):
        new_table = self.left.join(self.right, 'one', 'four', columns=['six'])

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 'a'),
            (2, 3, 'b', 'b'),
            (None, 2, 'c', 'c')
        ])

    def test_join_columns_kwarg_right_key(self):
        new_table = self.left.join(self.right, 'one', 'four', columns=['four', 'six'])

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 'a'),
            (2, 3, 'b', 2, 'b'),
            (None, 2, 'c', None, 'c')
        ])

    def test_join_rows_are_tuples(self):
        new_table = self.left.join(self.right, 'one', 'four', columns=['four', 'six'])

        self.assertIsInstance(new_table.rows[0].values(), tuple)

    def test_full_outer(self):
        left_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (3, 2, 'c')
        )

        right_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (4, 2, 'c')
        )

        left = Table(left_rows, self.left_column_names, self.column_types)
        right = Table(right_rows, self.right_column_names, self.column_types)

        new_table = left.join(right, 'one', 'four', full_outer=True)

        self.assertIsNot(new_table, left)
        self.assertIsNot(new_table, right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', 2, 3, 'b'),
            (3, 2, 'c', None, None, None),
            (None, None, None, 4, 2, 'c')
        ])

    def test_full_outer_key_list(self):
        left_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (3, 2, 'c')
        )

        right_rows = (
            (1, 4, 'a'),
            (2, 3, 'b'),
            (4, 2, 'c')
        )

        left = Table(left_rows, self.left_column_names, self.column_types)
        right = Table(right_rows, self.right_column_names, self.column_types)

        new_table = left.join(right, ['one'], ['four'], full_outer=True)

        self.assertIsNot(new_table, left)
        self.assertIsNot(new_table, right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', 2, 3, 'b'),
            (3, 2, 'c', None, None, None),
            (None, None, None, 4, 2, 'c')
        ])

    def test_join_by_row_number(self):
        new_table = self.left.join(self.right, full_outer=True)

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', 2, 3, 'b'),
            (None, 2, 'c', None, 2, 'c')
        ])

    def test_join_by_row_number_short_right(self):
        right_rows = self.right_rows + ((7, 9, 'z'),)
        right = Table(right_rows, self.right_column_names, self.column_types)

        new_table = self.left.join(right, full_outer=True)

        self.assertIsNot(new_table, self.left)
        self.assertIsNot(new_table, right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', 2, 3, 'b'),
            (None, 2, 'c', None, 2, 'c'),
            (None, None, None, 7, 9, 'z')
        ])

    def test_join_by_row_number_short_left(self):
        left_rows = self.left_rows + ((7, 9, 'z'),)
        left = Table(left_rows, self.left_column_names, self.column_types)

        new_table = left.join(self.right, full_outer=True)

        self.assertIsNot(new_table, left)
        self.assertIsNot(new_table, self.right)
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'four', 'five', 'six'])
        self.assertColumnTypes(new_table, [Number, Number, Text, Number, Number, Text])
        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', 2, 3, 'b'),
            (None, 2, 'c', None, 2, 'c'),
            (7, 9, 'z', None, None, None)
        ])

    def test_join_validate_default(self):
        # Existing behavior: duplicates are allowed with no validate.
        new_table = self.left.join(self.right, 'one', 'four')

        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (2, 3, 'b', 3, 'b'),
            (None, 2, 'c', 2, 'c')
        ])

    def test_join_validate_one_to_one(self):
        new_table = self.left.join(self.right, 'one', 'four', validate='one_to_one')

        self.assertColumnNames(new_table, ['one', 'two', 'three', 'five', 'six'])
        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (2, 3, 'b', 3, 'b'),
            (None, 2, 'c', 2, 'c')
        ])

    def test_join_validate_one_to_one_duplicate_left(self):
        left = Table([(1, 4, 'a'), (1, 5, 'b'), (2, 6, 'c')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (2, 5, 'b')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            left.join(right, 'one', 'four', validate='one_to_one')

        self.assertIn('left', str(context.exception))

    def test_join_validate_one_to_one_duplicate_right(self):
        right = Table([(1, 4, 'a'), (1, 5, 'b'), (2, 6, 'c')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            self.left.join(right, 'one', 'four', validate='one_to_one')

        self.assertIn('right', str(context.exception))

    def test_join_validate_one_to_one_duplicates_both_sides(self):
        left = Table([(1, 4, 'a'), (1, 5, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (1, 5, 'b')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            left.join(right, 'one', 'four', validate='one_to_one')

        message = str(context.exception)
        self.assertIn('left', message)
        self.assertIn('right', message)

    def test_join_validate_one_to_many(self):
        left = Table([(1, 4, 'a'), (2, 3, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (1, 5, 'b'), (2, 6, 'c')], self.right_column_names, self.column_types)

        new_table = left.join(right, 'one', 'four', validate='one_to_many')

        # Duplicates on the right are preserved, not deduplicated.
        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (1, 4, 'a', 5, 'b'),
            (2, 3, 'b', 6, 'c')
        ])

    def test_join_validate_one_to_many_duplicate_left(self):
        left = Table([(1, 4, 'a'), (1, 5, 'b')], self.left_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            left.join(self.right, 'one', 'four', validate='one_to_many')

        self.assertIn('left', str(context.exception))

    def test_join_validate_many_to_one(self):
        left = Table([(1, 4, 'a'), (1, 5, 'b'), (2, 6, 'c')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (2, 5, 'b')], self.right_column_names, self.column_types)

        new_table = left.join(right, 'one', 'four', validate='many_to_one')

        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (1, 5, 'b', 4, 'a'),
            (2, 6, 'c', 5, 'b')
        ])

    def test_join_validate_many_to_one_duplicate_right(self):
        right = Table([(1, 4, 'a'), (1, 5, 'b')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            self.left.join(right, 'one', 'four', validate='many_to_one')

        self.assertIn('right', str(context.exception))

    def test_join_validate_many_to_many(self):
        left = Table([(1, 4, 'a'), (1, 5, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (1, 5, 'b')], self.right_column_names, self.column_types)

        new_table = left.join(right, 'one', 'four', validate='many_to_many')

        # Every combination of matching rows is kept.
        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (1, 4, 'a', 5, 'b'),
            (1, 5, 'b', 4, 'a'),
            (1, 5, 'b', 5, 'b')
        ])

    def test_join_validate_unknown(self):
        with self.assertRaises(ValueError):
            self.left.join(self.right, 'one', 'four', validate='many_to_some')

    def test_join_validate_duplicate_without_match(self):
        # A duplicate left key that doesn't match any right key must still fail.
        left = Table([(1, 4, 'a'), (1, 5, 'b')], self.left_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            left.join(self.right, 'one', 'five', inner=True, validate='one_to_many')

        self.assertIn('left', str(context.exception))

    def test_join_validate_duplicate_right_without_match(self):
        # A duplicate right key that no left key matches must still fail.
        right = Table([(99, 4, 'a'), (99, 5, 'b')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            self.left.join(right, 'one', 'four', inner=True, validate='many_to_one')

        self.assertIn('right', str(context.exception))

    def test_join_validate_duplicate_null(self):
        # Null values follow the usual matching rules: the second None is a duplicate.
        left = Table([(None, 4, 'a'), (None, 5, 'b')], self.left_column_names, self.column_types)

        with self.assertRaises(ValueError):
            left.join(self.right, 'one', 'four', validate='one_to_many')

    def test_join_validate_null_matches(self):
        # A single null matches under the usual rules.
        new_table = self.left.join(self.right, 'one', 'four', validate='one_to_one')

        self.assertEqual(len(new_table.rows), 3)
        self.assertEqual(new_table.rows[2]['five'], 2)

    def test_join_validate_composite_columns(self):
        left = Table([(1, 4, 'a'), (1, 4, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (2, 3, 'b')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            left.join(right, ['one', 'two'], ['four', 'five'], validate='one_to_many')

        self.assertIn('left', str(context.exception))

        # Different combinations are unique.
        left = Table([(1, 4, 'a'), (1, 5, 'b')], self.left_column_names, self.column_types)
        new_table = left.join(right, ['one', 'two'], ['four', 'five'], validate='one_to_one')
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'six'])
        self.assertRows(new_table, [
            (1, 4, 'a', 'a'),
            (1, 5, 'b', None)
        ])

    def test_join_validate_composite_null(self):
        # Nulls in a composite key follow the usual matching rules.
        left = Table([(1, None, 'a'), (1, None, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, None, 'a'), (2, None, 'b')], self.right_column_names, self.column_types)

        with self.assertRaises(ValueError) as context:
            left.join(right, ['one', 'two'], ['four', 'five'], validate='one_to_many')

        self.assertIn('left', str(context.exception))

        left = Table([(1, None, 'a'), (2, 3, 'b')], self.left_column_names, self.column_types)
        new_table = left.join(right, ['one', 'two'], ['four', 'five'], validate='one_to_one')
        self.assertColumnNames(new_table, ['one', 'two', 'three', 'six'])
        self.assertRows(new_table, [
            (1, None, 'a', 'a'),
            (2, 3, 'b', None)
        ])

    def test_join_validate_function_called_once(self):
        calls = {'left': 0, 'right': 0}

        def left_key(row):
            calls['left'] += 1
            return row['one']

        def right_key(row):
            calls['right'] += 1
            return row['four']

        self.left.join(self.right, left_key, right_key, validate='one_to_one')

        self.assertEqual(calls, {'left': 3, 'right': 3})

    def test_join_validate_function_duplicates(self):
        with self.assertRaises(ValueError):
            self.left.join(
                self.right,
                lambda left: 1,
                lambda right: 1,
                validate='one_to_one'
            )

    def test_join_validate_by_row_number(self):
        left = Table([(1, 4, 'a'), (2, 3, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (2, 3, 'b')], self.right_column_names, self.column_types)

        new_table = left.join(right, validate='one_to_one')

        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', 2, 3, 'b')
        ])

    def test_join_validate_by_row_number_unmatched_rows(self):
        # Row numbers are always unique, and left rows beyond the right
        # table's length still count as unique keys.
        left = Table([(1, 4, 'a'), (2, 3, 'b'), (3, 2, 'c')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a')], self.right_column_names, self.column_types)

        new_table = left.join(right, validate='many_to_one')

        self.assertEqual(len(new_table.rows), 3)

    def test_join_validate_empty_tables(self):
        empty = Table([], self.right_column_names, self.column_types)

        new_table = self.left.join(empty, 'one', 'four', validate='one_to_one')
        self.assertRows(new_table, [
            (1, 4, 'a', None, None),
            (2, 3, 'b', None, None),
            (None, 2, 'c', None, None)
        ])

        empty_left = Table([], self.left_column_names, self.column_types)
        new_table = empty_left.join(self.right, 'one', 'four', validate='one_to_one')
        self.assertEqual(len(new_table.rows), 0)

    def test_join_validate_columns_kwarg(self):
        right = Table([(1, 4, 'a'), (2, 5, 'b')], self.right_column_names, self.column_types)
        new_table = self.left.join(right, 'one', 'four', columns=['six'], validate='one_to_one')

        self.assertColumnNames(new_table, ['one', 'two', 'three', 'six'])
        self.assertRows(new_table, [
            (1, 4, 'a', 'a'),
            (2, 3, 'b', 'b'),
            (None, 2, 'c', None)
        ])

    def test_join_validate_same_column_name(self):
        right = Table(self.right_rows, ['four', 'one', 'six'], self.column_types)
        new_table = self.left.join(right, 'one', 'four', validate='one_to_one')

        self.assertColumnNames(new_table, ['one', 'two', 'three', 'one2', 'six'])
        self.assertRows(new_table, [
            (1, 4, 'a', 4, 'a'),
            (2, 3, 'b', 3, 'b'),
            (None, 2, 'c', 2, 'c')
        ])

    def test_join_validate_full_outer(self):
        left = Table([(1, 4, 'a'), (2, 3, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (3, 5, 'b')], self.right_column_names, self.column_types)

        new_table = left.join(right, 'one', 'four', full_outer=True, validate='one_to_one')

        self.assertRows(new_table, [
            (1, 4, 'a', 1, 4, 'a'),
            (2, 3, 'b', None, None, None),
            (None, None, None, 3, 5, 'b')
        ])

    def test_join_validate_require_match(self):
        left = Table([(1, 4, 'a'), (2, 3, 'b')], self.left_column_names, self.column_types)
        right = Table([(1, 4, 'a'), (2, 5, 'b')], self.right_column_names, self.column_types)

        new_table = left.join(right, 'one', 'four', require_match=True, validate='one_to_one')
        self.assertEqual(len(new_table.rows), 2)

        with self.assertRaises(ValueError):
            left.join(right, 'one', 'five', require_match=True, validate='one_to_one')

    def test_join_validate_inputs_unchanged(self):
        left = Table(self.left_rows, self.left_column_names, self.column_types, row_names='three')
        right = Table(self.right_rows, self.right_column_names, self.column_types)

        new_table = left.join(right, 'one', 'four', validate='one_to_one')

        self.assertIsNot(new_table, left)
        self.assertIsNot(new_table, right)
        self.assertRows(left, self.left_rows)
        self.assertRows(right, self.right_rows)
        self.assertRowNames(left, ('a', 'b', 'c'))
        self.assertRowNames(new_table, ('a', 'b', 'c'))
        self.assertColumnNames(left, self.left_column_names)
        self.assertColumnNames(right, self.right_column_names)
