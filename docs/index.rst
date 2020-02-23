.. udebs documentation master file, created by
   sphinx-quickstart on Tue Feb 18 20:12:01 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Udebs Api
=========

.. toctree::
    :maxdepth: 2

Instance
--------

.. autoclass:: udebs.instance.Instance
   :members:
   :exclude-members: getEntity, controlMove, testFuture, getMap

Standard
--------

.. autoclass:: udebs.interpret.standard
    :members:

Utilities
---------

.. automodule:: udebs.loadxml
    :members:

.. automodule:: udebs.utilities
    :members: alternate, lookup, placeholder, Player, Timer

.. automodule:: udebs.interpret
    :members: importModule, importFunction

Errors
------

.. autoexception:: udebs.instance.UndefinedSelectorError
.. autoexception:: udebs.interpret.UdebsExecutionError
.. autoexception:: udebs.interpret.UdebsSyntaxError
