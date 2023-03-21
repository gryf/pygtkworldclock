pyGTKWorldClock
===============

This is simple world clock application written in Python and Cairo.

Requirement
-----------

- Python3
- PyCairo
- PyGObject (GTK3)

Configuration
-------------

See `example.yaml`_ for reference. Basically config file is a YAML file, which
contain a definition of timezone and the label, which in the end maps as python
dictionary:

.. code:: python

   {'tz': 'string of timezone'
    'label': 'string of some label'}

For example, single clock can be represended as:

.. code:: yaml

   ---
   -
     tz: UTC
     label: The real world clock

which would have an effect:

.. image:: /images/single.png
   :alt: single clock

Note, that it have to be a list in YAML format (line started with ``-``)
followed by a definition of key-value of timezone and a label. Analogically,
several clocks (let's take an example of US timezones) can be vertically
arranged by providing a *list* of *key-values*:

.. code:: yaml

   ---
   -
     tz: US/Hawaii
     label: Honolulu, Hawaii, US
   -
     tz: US/Alaska
     label: Anchorage, Alaska, US
   -
     tz: US/Pacific
     label: Portland, Oregon, US
   -
     tz: US/Mountain
     label: Salt Lake City, Utah, US
   -
     tz: US/Central
     label: Austin, Texas, US
   -
     tz: US/Eastern
     label: New York, US

and the result:

.. image:: /images/vertical.png
   :alt: single clock

Same in horizontal arrangement:

.. code:: yaml

   ---
   -
     -
       tz: US/Hawaii
       label: Honolulu, Hawaii, US
     -
       tz: US/Alaska
       label: Anchorage, Alaska, US
     -
       tz: US/Pacific
       label: Portland, Oregon, US
     -
       tz: US/Mountain
       label: Salt Lake City, Utah, US
     -
       tz: US/Central
       label: Austin, Texas, US
     -
       tz: US/Eastern
       label: New York, US

obviously the result would be:

.. image:: /images/horizontal.png
   :alt: single clock

And finally the same in two rows, three columns:

.. code:: yaml

   ---
   -
     -
       tz: US/Hawaii
       label: Honolulu, Hawaii, US
     -
       tz: US/Alaska
       label: Anchorage, Alaska, US
     -
       tz: US/Pacific
       label: Portland, Oregon, US
   -
     -
       tz: US/Mountain
       label: Salt Lake City, Utah, US
     -
       tz: US/Central
       label: Austin, Texas, US
     -
       tz: US/Eastern
       label: New York, US

which will look like that:

.. image:: /images/grid.png
   :alt: single clock

You can experiment to get the layout of your choice.

License
-------

This software is licensed under 3-clause BSD license. See LICENSE file for
details.

.. _example.yaml: example.yaml
