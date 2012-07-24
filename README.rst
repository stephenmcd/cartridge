.. image:: https://secure.travis-ci.org/stephenmcd/cartridge.png?branch=master

Created by `Stephen McDonald <http://twitter.com/stephen_mcd>`_

========
Overview
========

Cartridge is a shopping cart application built using the `Django`_ framework.
It is `BSD licensed`_ and designed to provide a clean and simple
base for developing e-commerce websites. It purposely does not include every
conceivable feature of an e-commerce website; instead, Cartridge focuses on providing core features common to most
e-commerce website.

This specific focus stems from the idea that every e-commerce website is
different, is tailored to the particular business and products at hand, and
should therefore be as easy to customize as possible. Cartridge achieves
this goal with a code-base that is as simple as possible and implements only the core features of an
e-commerce site.

Cartridge extends the `Mezzanine`_ content management platform. A live
demo of Cartridge can be found by visiting the `Mezzanine live demo`_.

Features
========

  * Hierarchical categories
  * Easily configurable product options (colours, sizes, etc.)
  * Hooks for shipping calculations and payment gateways
  * Sale pricing
  * Promotional discount codes
  * PDF invoice generation (for packing slips)
  * Stock control
  * Product popularity
  * Thumbnail generation
  * Built-in test suite
  * Separation of presentation (no embedded markup)
  * Smart categories (by price range, colour, etc)
  * Registered or anonymous checkout
  * Configurable number of checkout steps
  * Denormalised data for accessiblilty and performance

Dependencies
============

Cartridge is designed as a plugin for the `Mezzanine`_ content management
platform and, as such, requires `Mezzanine`_ to be installed. The integration
of the two applications should occur automatically by following the
installation instructions below.

Installation
============

The easiest method is to install directly from pypi using `pip`_ or
`setuptools`_ by running the respective command below, which will also
attempt to install the dependencies mentioned above::

    $ pip install -U cartridge

or::

    $ easy_install -U cartridge

Otherwise, you can download Cartridge and install it directly from source::

    $ python setup.py install

Once installed, the command ``mezzanine-project`` should be available via
Mezzanine, which can be used for creating a new Cartridge project in a
similar fashion to ``django-admin.py``::

    $ mezzanine-project -a cartridge project_name

You can then run your project with the usual Django steps::

    $ cd project_name
    $ python manage.py createdb --noinput
    $ python manage.py runserver

The ``createdb`` command performs the same task as Django's ``syncdb`` command
and also sets the initial migration state for `South`_. If you'd like to
specify a username and password during set up, simply exclude the
``--noinput`` option included above when running ``createdb``.

You should then be able to browse to http://127.0.0.1:8000/admin/ and log
in using the default account (``username: admin, password: default``) or the
credentials specified during ``createdb``.

Contributing
============

Cartridge is an open source project managed using both Git and
Mercurial version control systems. These repositories are hosted on both
`Github`_ and `Bitbucket`_, so contributing is as easy as
forking the project on either of these sites and committing back your
enhancements.

Please note the following points around contributing:

  * Contributed code must be written in the existing style. This is as simple as following the `Django coding style`_ and, most importantly, `PEP 8`_.
  * Run the tests before committing your changes. If your changes cause the tests to break, they won't be accepted.
  * If you add new functionality, you must include basic tests and documentation.

Donating
========

If you would like to make a donation to continue development of the
project, you can do so via the `Mezzanine`_ website.

Support
=======

For general questions or comments, please join the
`mezzanine-users`_ mailing list. To report a bug or other type of issue,
please use the `Github issue tracker`_.

Sites Using Cartridge
=====================

  * `Ripe Maternity <http://www.ripematernity.com>`_
  * `Cotton On <http://shop.cottonon.com>`_
  * `Coopers Store <http://store.coopers.com.au>`_
  * `Sheer Ethic <http://sheerethic.com>`_
  * `tindie.com <http://tindie.com>`_
  * `Ross A. Laird <http://rosslaird.com/shop>`_
  * `Pink Twig <http://www.pinktwig.ca/shop>`_
  * `Parfume Planet <http://parfumeplanet.com>`_
  * `Life is Good <http://lifeisgoodforall.co.uk/>`_
  * `Brooklyn Navy Yard <http://bldg92.org/>`_
  * `Cotton On Asia <http://asia.cottonon.com/>`_

.. _`Django`: http://djangoproject.com/
.. _`BSD licensed`: http://www.linfo.org/bsdlicense.html
.. _`Mezzanine live demo`: http://mezzanine.jupo.org/
.. _`pip`: http://www.pip-installer.org/
.. _`setuptools`: http://pypi.python.org/pypi/setuptools
.. _`Mezzanine`: http://mezzanine.jupo.org/
.. _`South`: http://south.aeracode.org/
.. _`Github`: http://github.com/stephenmcd/cartridge/
.. _`Bitbucket`: http://bitbucket.org/stephenmcd/cartridge/
.. _`mezzanine-users`: http://groups.google.com/group/mezzanine-users
.. _`Github issue tracker`: http://github.com/stephenmcd/cartridge/issues
.. _`Django coding style`: http://docs.djangoproject.com/en/dev/internals/contributing/#coding-style
.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/

