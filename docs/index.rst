.. udebs documentation master file, created by
   sphinx-quickstart on Tue Feb 18 20:12:01 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Udebs Api
=========

.. toctree::
    :maxdepth: 2

    index.rst

Instance
--------

.. autoclass:: udebs.instance.Instance
   :members:
   :exclude-members: testFuture

Standard
--------

.. autoclass:: udebs.interpret.standard
    :members:

Utilities
---------

.. automodule:: udebs.loadxml
    :members:

.. automodule:: udebs.utilities
    :members:

.. automodule:: udebs.interpret
    :members: importModule, importFunction

Errors
------

.. automodule:: udebs.errors
    :members: