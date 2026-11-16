"""
This module contains the :class:`MappedSequence` class that forms the foundation
for agate's :class:`.Row` and :class:`.Column` as well as for named sequences of
rows and columns.
"""

from collections import OrderedDict
from collections.abc import Sequence

from agate.utils import _missing


class MappedSequence(Sequence):
    """
    A generic container for immutable data that can be accessed either by
    numeric index or by key. This is similar to an
    :class:`collections.OrderedDict` except that the keys are optional and
    iteration over it returns the values instead of keys.

    This is the base class for both :class:`.Column` and :class:`.Row`.

    :param values:
        A sequence of values.
    :param keys:
        A sequence of keys.
    """
    __slots__ = ['_values', '_keys', '_name_index', '_name_index_signature']

    def __init__(self, values, keys=None):
        self._values = tuple(values)
        self._keys = keys

        # Lazily prepared name -> index lookup. Built on the first key-based
        # access instead of up front, so sequences that are only read by index
        # pay nothing. It lives on the object itself, so lookups prepared for
        # one row/column can never leak into another one.
        self._name_index = _missing
        self._name_index_signature = _missing

    def __getstate__(self):
        """
        Return state values to be pickled.

        This is necessary on Python2.7 when using :code:`__slots__`.

        Lookup caches are deliberately not serialized: after restoring, the
        object must derive any name lookup from its restored ``_keys`` rather
        than reuse a mapping built before the state was captured.
        """
        return {
            '_values': self._values,
            '_keys': self._keys
        }

    def __setstate__(self, data):
        """
        Restore pickled state.

        This is necessary on Python2.7 when using :code:`__slots__`.
        """
        self._values = data['_values']
        self._keys = data['_keys']
        self._name_index = _missing
        self._name_index_signature = _missing

    def _get_name_index(self):
        """
        Return a mapping of each key to the index of its last occurrence,
        preparing it only the first time it is needed.

        The index is rebuilt if the externally supplied key sequence has been
        replaced or mutated since the last preparation. Tuple keys (the kind
        agate itself produces) take an identity-and-length fast path; other
        sequences are compared by value, which still avoids rebuilding the
        full mapping on repeated reads of the same row.
        """
        keys = self._keys

        if keys is None:
            raise KeyError

        if isinstance(keys, tuple):
            signature = (id(keys), len(keys))
        else:
            signature = tuple(keys)

        if self._name_index is not _missing and self._name_index_signature == signature:
            return self._name_index

        name_index = {}

        for i, key in enumerate(keys):
            # Last occurrence wins, matching OrderedDict(zip(keys, values))
            # when keys are duplicated.
            name_index[key] = i

        self._name_index = name_index
        self._name_index_signature = signature

        return name_index

    def __unicode__(self):
        """
        Print a unicode sample of the contents of this sequence.
        """
        sample = ', '.join(repr(d) for d in self.values()[:5])

        if len(self) > 5:
            sample = '%s, ...' % sample

        return f'<agate.{type(self).__name__}: ({sample})>'

    def __str__(self):
        """
        Print an ascii sample of the contents of this sequence.
        """
        return str(self.__unicode__())

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        """
        Retrieve values from this array by index, slice or key.
        """
        if isinstance(key, slice):
            indices = range(*key.indices(len(self)))
            values = self.values()
            return tuple(values[i] for i in indices)
        # Note: can't use isinstance because bool is a subclass of int
        elif type(key) is int:
            return self.values()[key]
        return self.values()[self._get_name_index()[key]]

    def __setitem__(self, key, value):
        """
        Set values by index, which we want to fail loudly.
        """
        raise TypeError('Rows and columns can not be modified directly. You probably need to compute a new column.')

    def __iter__(self):
        """
        Iterate over values.
        """
        return iter(self.values())

    def __len__(self):
        return len(self.values())

    def __eq__(self, other):
        """
        Equality test with other sequences.
        """
        if not isinstance(other, Sequence):
            return False

        return self.values() == tuple(other)

    def __ne__(self, other):
        """
        Inequality test with other sequences.
        """
        return not self.__eq__(other)

    def __contains__(self, value):
        return self.values().__contains__(value)

    def keys(self):
        """
        Equivalent to :meth:`collections.OrderedDict.keys`.
        """
        return self._keys

    def values(self):
        """
        Equivalent to :meth:`collections.OrderedDict.values`.
        """
        return self._values

    def items(self):
        """
        Equivalent to :meth:`collections.OrderedDict.items`.
        """
        return tuple(zip(self.keys(), self.values()))

    def get(self, key, default=None):
        """
        Equivalent to :meth:`collections.OrderedDict.get`.
        """
        try:
            return self.values()[self._get_name_index()[key]]
        except KeyError:
            if default:
                return default
            return None

    def dict(self):
        """
        Retrieve the contents of this sequence as an
        :class:`collections.OrderedDict`.

        A fresh :class:`collections.OrderedDict` is returned on every call so
        that callers can modify it without polluting later reads or the
        underlying sequence.
        """
        if self.keys() is None:
            raise KeyError

        return OrderedDict(self.items())
