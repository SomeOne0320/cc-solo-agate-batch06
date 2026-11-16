"""
This module contains the :class:`Column` class, which defines a "vertical"
array of tabular data. Whereas :class:`.Row` instances are independent of their
parent :class:`.Table`, columns depend on knowledge of both their position in
the parent (column name, data type) as well as the rows that contain their data.
"""

from agate.mapped_sequence import MappedSequence
from agate.utils import _missing, memoize, NullOrder


def null_handler(k):
    """
    Key method for sorting nulls correctly.
    """
    if k is None:
        return NullOrder()

    return k


class Column(MappedSequence):
    """
    Proxy access to column data. Instances of :class:`Column` should
    not be constructed directly. They are created by :class:`.Table`
    instances and are unique to them.

    Columns are implemented as subclass of :class:`.MappedSequence`. They
    deviate from the underlying implementation in that loading of their data
    is deferred until it is needed.

    :param name:
        The name of this column.
    :param data_type:
        An instance of :class:`.DataType`.
    :param rows:
        A :class:`.MappedSequence` that contains the :class:`.Row` instances
        containing the data for this column.
    :param row_names:
        An optional list of row names (keys) for this column.
    """
    __slots__ = [
        '_index', '_name', '_data_type', '_rows',
        '_memo_values',
        '_memo_values_distinct',
        '_memo_values_without_nulls',
        '_memo__values_sorted',
        '_memo__values_without_nulls_sorted'
    ]

    def __init__(self, index, name, data_type, rows, row_names=None):
        self._index = index
        self._name = name
        self._data_type = data_type
        self._rows = rows
        self._keys = row_names

        # Caches are per column. Nothing is shared with columns of other
        # tables, other columns of the same table, or columns of tables
        # forked from the same data; each Column instance prepares its own
        # data on first use.
        self._memo_values = _missing
        self._memo_values_distinct = _missing
        self._memo_values_without_nulls = _missing
        self._memo__values_sorted = _missing
        self._memo__values_without_nulls_sorted = _missing
        self._name_index = _missing
        self._name_index_signature = _missing

    def __getstate__(self):
        """
        Return state values to be pickled.

        This is necessary on Python2.7 when using :code:`__slots__`.

        Prepared values and lookup caches are not serialized, so a restored
        column rebuilds them lazily from its restored rows.
        """
        return {
            '_index': self._index,
            '_name': self._name,
            '_data_type': self._data_type,
            '_rows': self._rows,
            '_keys': self._keys
        }

    def __setstate__(self, data):
        """
        Restore pickled state.

        This is necessary on Python2.7 when using :code:`__slots__`.
        """
        self._index = data['_index']
        self._name = data['_name']
        self._data_type = data['_data_type']
        self._rows = data['_rows']
        self._keys = data['_keys']

        self._memo_values = _missing
        self._memo_values_distinct = _missing
        self._memo_values_without_nulls = _missing
        self._memo__values_sorted = _missing
        self._memo__values_without_nulls_sorted = _missing
        self._name_index = _missing
        self._name_index_signature = _missing

    @property
    def index(self):
        """
        This column's index.
        """
        return self._index

    @property
    def name(self):
        """
        This column's name.
        """
        return self._name

    @property
    def data_type(self):
        """
        This column's data type.
        """
        return self._data_type

    @memoize
    def values(self):
        """
        Get the values in this column, as a tuple.

        The rows backing this column are traversed once, the first time the
        values are requested. Every later read (including by index or name)
        reuses the prepared tuple instead of revisiting the rows, so reading a
        column eight times costs roughly one pass over the rows, not eight.
        """
        return tuple(row[self._index] for row in self._rows)

    @memoize
    def values_distinct(self):
        """
        Get the distinct values in this column, as a tuple.
        """
        return tuple(set(self.values()))

    @memoize
    def values_without_nulls(self):
        """
        Get the values in this column with any null values removed.
        """
        return tuple(d for d in self.values() if d is not None)

    def values_sorted(self):
        """
        Get the values in this column sorted.

        Sorting happens once; each call returns a fresh list so callers that
        mutate the result (for example by calling ``.reverse()``) cannot
        corrupt the cached ordering or later reads.
        """
        return list(self._values_sorted())

    @memoize
    def _values_sorted(self):
        return tuple(sorted(self.values(), key=null_handler))

    def values_without_nulls_sorted(self):
        """
        Get the values in this column with any null values removed and sorted.

        As with :meth:`values_sorted`, the sort is done once and every call
        returns a fresh list.
        """
        return list(self._values_without_nulls_sorted())

    @memoize
    def _values_without_nulls_sorted(self):
        return tuple(sorted(self.values_without_nulls(), key=null_handler))
