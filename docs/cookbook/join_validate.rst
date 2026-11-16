==============
Validate joins
==============

By default, :meth:`.Table.join` will happily join a key that appears multiple
times in either table. Each matching pair produces its own output row. That is
correct for a many-to-many relationship, but for something like an order table
and a customer table it usually means there is unexpected duplicate data: the
same order gets repeated once per duplicate customer, and any totals computed
from the joined table are inflated.

Pass the ``validate`` argument to declare the relationship you expect. The
join will check the keys and raise a :exc:`ValueError` before any result is
generated if the data doesn't fit.

Choosing a convention
=====================

There are four conventions, describing whether each side's key may repeat:

==================================  =========================  =========================
``validate``                        Left key                   Right key
==================================  =========================  =========================
``'one_to_one'``                    unique                     unique
``'one_to_many'``                   unique                     may repeat
``'many_to_one'``                   may repeat                 unique
``'many_to_many'``                  may repeat                 may repeat
==================================  =========================  =========================

Read the name from left to right: ``'one_to_many'`` means one row on the left
matches many rows on the right, so the left key must be unique.

* ``'one_to_one'``: two rows in either table may never share a key. Use it
  when both tables are keyed by a unique identifier, such as an order ID
  matched to a shipment ID.
* ``'many_to_one'``: many left rows may share a key, but each right key must
  be unique. This is the common "foreign key" case, such as many orders
  pointing at one customer. It is the convention that catches a duplicated
  customer record.
* ``'one_to_many'``: the reverse, one left row fanning out to many right rows.
  Each left key must be unique.
* ``'many_to_many'``: both sides may repeat. This is the default behavior
  expressed explicitly; it never raises. Use it when a many-to-many
  relationship is intentional, to make that clear to readers.

If you are unsure, ``'many_to_one'`` and ``'one_to_one'`` are the ones that
usually catch mistakes.

Example
=======

Suppose each order should belong to exactly one customer. A duplicated
customer record would silently repeat the order:

.. code-block:: python

    orders = Table(...)       # order_id, customer_id, total
    customers = Table(...)    # customer_id, name

    joined = orders.join(customers, 'customer_id', 'customer_id')
    # The duplicated customer causes each of their orders to appear twice,
    # doubling their total.

Declaring the relationship makes the bad data fail loudly instead:

.. code-block:: python

    joined = orders.join(
        customers, 'customer_id', 'customer_id', validate='many_to_one'
    )
    # ValueError: Join validation "many_to_one" failed:
    #   the right key contains duplicate values (for example, 42).

What is checked
===============

The check covers every row of both input tables, not only the rows that
ultimately match. A duplicate key therefore cannot slip through just because
one of the duplicates has no counterpart in the other table, and the result
does not depend on :code:`inner`, :code:`full_outer` or
:code:`require_match`.

The same rules apply however the keys are defined: single columns, sequences
of columns (the combination must be unique, not each column individually),
row-number joins, and key functions. Key functions are called only once: the
same values are used for validation and for the join, so a function with a
counter or a one-shot read is safe.

Null values follow the join's normal matching rules. For example, a single
``None`` key is fine, but two ``None`` keys are duplicates, including when
``None`` appears in a composite key.

Allowing duplicates is not the same as deduplicating. With
:code:`many_to_one` or :code:`many_to_many`, legal repeated matches still
produce every combination of rows, exactly as they would without
:code:`validate`.

The ``validate`` check is independent of the other join options: column
selection with :code:`columns`, suffixing of identically named columns, empty
tables and full outer joins all behave as before. The input tables, their
column types and row names, and the order of the returned rows are unchanged.

If ``validate`` is omitted, no validation is performed and joins behave
exactly as they did before this option existed.
