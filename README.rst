.. image:: https://secure.travis-ci.org/stephenmcd/cartridge.png?branch=master
   :target: http://travis-ci.org/#!/stephenmcd/cartridge

Created by `Stephen McDonald <http://twitter.com/stephen_mcd>`_

========
Overview
========

Cartridge is a shopping cart application built using the `Django`_
framework. It is `BSD licensed`_ and designed to provide a clean and
simple base for developing e-commerce websites. It purposely does not
include every conceivable feature of an e-commerce website; instead,
Cartridge focuses on providing core features common to most e-commerce
websites.

This specific focus stems from the idea that every e-commerce website
is different, is tailored to the particular business and products at
hand, and should therefore be as easy to customize as possible.
Cartridge achieves this goal with a code-base that is as simple as
possible and implements only the core features of an e-commerce
website.

Cartridge extends the `Mezzanine`_ content management platform. A live
demo of Cartridge can be found by visiting the `Mezzanine live demo`_.

Features
========

  * Hierarchical categories
  * Easily configurable product options (colours, sizes, etc.)
  * Hooks for tax/shipping calculations and payment gateways
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
  * Authenticated customer accounts with transaction history

Dependencies
============

Cartridge is designed as a plugin for the `Mezzanine`_ content
management platform and, as such, requires `Mezzanine`_ to be
installed. The integration of the two applications should occur
automatically by following the installation instructions below.

Installation
============

The easiest method is to install directly from pypi using `pip`_ by
running the command below, which will also install the required
dependencies mentioned above::

    $ pip install -U cartridge

Otherwise, you can download Cartridge and install it directly from source::

    $ python setup.py install

Once installed, the command ``mezzanine-project`` can be used to
create a new Mezzanine project, with Cartridge installed, in similar
fashion to ``django-admin.py``::

    $ mezzanine-project -a cartridge project_name
    $ cd project_name
    $ python manage.py createdb --noinput
    $ python manage.py runserver

Here we specify the ``-a`` switch for the ``mezzanine-project`` command,
which tells it to use an alternative package (cartridge) for the project
template to use. Both Mezzanine and Cartridge contain a project template
package containing the ``settings.py`` and ``urls.py`` modules for an
initial project. If you'd like to add Cartridge to an existing Mezzanine
or Django project, you'll need to manually configure these yourself. See
the `FAQ section of the Mezzanine documentation`_ for more information.

.. note::

    The ``createdb`` is a shortcut for using Django's ``syncdb``
    command and setting the initial migration state for `South`_. You
    can alternatively use ``syncdb`` and ``migrate`` if preferred.
    South is automatically added to INSTALLED_APPS if the
    ``USE_SOUTH`` setting is set to ``True``.

You should then be able to browse to http://127.0.0.1:8000/admin/ and
log in using the default account (``username: admin, password:
default``). If you'd like to specify a different username and password
during set up, simply exclude the ``--noinput`` option included above
when running ``createdb``.

Contributing
============

Cartridge is an open source project managed using both the Git and
Mercurial version control systems. These repositories are hosted on
both `GitHub`_ and `Bitbucket`_ respectively, so contributing is as
easy as forking the project on either of these sites and committing
back your enhancements.

Please note the following guidelines for contributing:

  * Contributed code must be written in the existing style. This is
    as simple as following the `Django coding style`_ and (most
    importantly) `PEP 8`_.
  * Contributions must be available on a separately named branch
    based on the latest version of the main branch.
  * Run the tests before committing your changes. If your changes
    cause the tests to break, they won't be accepted.
  * If you are adding new functionality, you must include basic tests
    and documentation.

If you want to do development with Cartridge, here's a quick way to set
up a development environment and run the Cartridge unit tests, using
`virtualenvwrapper`_ to set up a virtualenv::

    $ mkvirtualenv cartridge
    $ workon cartridge
    $ pip install -e git://github.com/stephenmcd/mezzanine.git#egg=mezzanine
    $ pip install pep8 pyflakes
    $ git clone https://github.com/stephenmcd/cartridge
    $ cd cartridge
    $ python setup.py develop
    $ cp cartridge/project_template/local_settings.py.template cartridge/project_template/local_settings.py
    $ ./cartridge/project_template/manage.py test shop


Language Translations
=====================

Cartridge makes full use of translation strings, which allow Cartridge
to be translated into multiple languages using `Django's
internationalization`_ methodology. Translations are managed on the
`Transiflex`_ website but can also be submitted via `GitHub`_ or
`Bitbucket`_. Consult the documentation for `Django's
internationalization`_ methodology for more information on creating
translations and using them.

Donating
========

If you would like to make a donation to continue development of
Cartridge, you can do so via the `Mezzanine Project`_ website.

Support
=======

To report a security issue, please send an email privately to
`security@jupo.org`_. This gives us a chance to fix the issue and
create an official release prior to the issue being made
public.

For general questions or comments, please join the `mezzanine-users`_
mailing list. To report a bug or other type of issue, please use the
`GitHub issue tracker`_. And feel free to drop by the `#mezzanine
IRC channel`_ on `Freenode`_, for a chat.

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
  * `Manai Glitter <https://manai.co.uk>`_
  * `Tactical Bags <http://tacticalbags.ru>`_
  * `Charles Koll Jewelry <http://charleskoll.com>`_
  * `Puraforce Remedies <http://puraforceremedies.com/>`_
  * `Adrenaline <http://www.adrln.com/>`_
  * `The Peculiar Store <http://thepeculiarstore.com>`_
  * `KisanHub <http://www.kisanhub.com/>`_
  * `Kegbot <http://kegbot.org>`_
  * `Amblitec <http://www.amblitec.com>`_
  * `ZigZag Bags <http://www.zigzagbags.com.au>`_


.. _`Django`: http://djangoproject.com/
.. _`BSD licensed`: http://www.linfo.org/bsdlicense.html
.. _`Mezzanine live demo`: http://mezzanine.jupo.org/
.. _`Mezzanine`: http://mezzanine.jupo.org/
.. _`Mezzanine Project`: http://mezzanine.jupo.org/
.. _`pip`: http://www.pip-installer.org/
.. _`FAQ section of the Mezzanine documentation`: http://mezzanine.jupo.org/docs/frequently-asked-questions.html#how-can-i-add-mezzanine-to-an-existing-django-project
.. _`setuptools`: http://pypi.python.org/pypi/setuptools
.. _`South`: http://south.aeracode.org/
.. _`Github`: http://github.com/stephenmcd/cartridge/
.. _`Bitbucket`: http://bitbucket.org/stephenmcd/cartridge/
.. _`mezzanine-users`: http://groups.google.com/group/mezzanine-users
.. _`Github issue tracker`: http://github.com/stephenmcd/cartridge/issues
.. _`Django coding style`: http://docs.djangoproject.com/en/dev/internals/contributing/#coding-style
.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
.. _`Transiflex`: https://www.transifex.net/projects/p/mezzanine/
.. _`security@jupo.org`: mailto:security@jupo.org?subject=Mezzanine+Security+Issue
.. _`#mezzanine IRC channel`: irc://freenode.net/mezzanine
.. _`Freenode`: http://freenode.net
.. _`Django's internationalization`: https://docs.djangoproject.com/en/dev/topics/i18n/translation/
.. _`virtualenvwrapper`: http://www.doughellmann.com/projects/virtualenvwrapper
