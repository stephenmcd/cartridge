.. image:: https://secure.travis-ci.org/stephenmcd/cartridge.png?branch=master
   :target: http://travis-ci.org/#!/stephenmcd/cartridge

Created by `Stephen McDonald <http://twitter.com/stephen_mcd>`_

========
Overview
========

Cartridge is a shopping cart application built using the `Django`_
framework. It is `BSD licensed`_, and designed to provide a clean and
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
management platform, and therefore requires `Mezzanine`_ to be
installed. The integration of the two applications should occur
automatically by following the installation instructions below.

Installation
============

The easiest method is to install directly from PyPI using `pip`_ by
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

    ``createdb`` will also install some demo content, such as a contact
    form, image gallery and your shop's first product. If you'd like to
    omit this step, use the ``--nodata`` option with ``createdb``.

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

* Contributed code must be written in the existing style. For Python
  (and to a decent extent, JavaScript as well), this is as simple as
  following the `Django coding style`_ and (most importantly)
  `PEP 8`_. Front-end CSS should adhere to the
  `Bootstrap CSS guidelines`_.
* Contributions must be available on a separately named branch
  based on the latest version of the main branch.
* Run the tests before committing your changes. If your changes
  cause the tests to break, they won't be accepted.
* If you are adding new functionality, you must include basic tests
  and documentation.

Here's a quick start to hacking on Cartridge after forking it on
GitHub, by using the internal "project_template" as your current
project::

    $ git clone https://github.com/your-github-username/cartridge/
    $ cd cartridge
    $ git checkout -b your-new-branch-name
    $ cp cartridge/project_template/local_settings.py{.template,}
    $ python setup.py develop
    $ python cartridge/project_template/manage.py createdb --noinput
    $ python cartridge/project_template/manage.py runserver

    "hack hack hack"

    $ python setup.py test
    $ git commit -am "A message describing what you changed."
    $ git push origin your-new-branch-name


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

For all other Mezzanine support, the primary channel is the
`mezzanine-users`_ mailing list. Questions, comments, and all related
discussions take place here amongst knowledgeable members of the
community.

If you're certain you've come across a bug, then please use the
`GitHub issue tracker`_. It's crucial that enough information is
provided to reproduce the bug. This includes things such as the
Python stack trace generated by error pages, as well as other aspects
of the development environment used, such as operating system,
database, Python version, etc. If you're not sure you've found a
reproducable bug, then please try the mailing list first.

Finally, feel free to drop by the `#mezzanine IRC channel`_ on
`Freenode`_, for a chat!

Communications in all Mezzanine spaces are expected to conform
to the `Django Code of Conduct`_.

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
* `Justine & Katie's Bowtique <http://www.jnkbows.com>`_
* `The Art Rebellion <http://www.theartrebellion.com/>`_
* `Engineered Arts <https://www.engineeredarts.co.uk>`_
* `Lipman Art <https://lipmanart.com/>`_
* `ZHackers <https://www.zhackers.com>`_


.. _`Django`: http://djangoproject.com/
.. _`BSD licensed`: http://www.linfo.org/bsdlicense.html
.. _`Mezzanine live demo`: http://mezzanine.jupo.org/
.. _`Mezzanine`: http://mezzanine.jupo.org/
.. _`Mezzanine Project`: http://mezzanine.jupo.org/
.. _`pip`: http://www.pip-installer.org/
.. _`FAQ section of the Mezzanine documentation`: http://mezzanine.jupo.org/docs/frequently-asked-questions.html#how-can-i-add-mezzanine-to-an-existing-django-project
.. _`South`: http://south.aeracode.org/
.. _`Github`: http://github.com/stephenmcd/cartridge/
.. _`Bitbucket`: http://bitbucket.org/stephenmcd/cartridge/
.. _`mezzanine-users`: http://groups.google.com/group/mezzanine-users
.. _`Github issue tracker`: http://github.com/stephenmcd/cartridge/issues
.. _`Django coding style`: http://docs.djangoproject.com/en/dev/internals/contributing/#coding-style
.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
.. _`Bootstrap CSS guidelines`: https://github.com/twbs/bootstrap/blob/master/CONTRIBUTING.md#css
.. _`Django Code of Conduct`: https://www.djangoproject.com/conduct/
.. _`Transiflex`: https://www.transifex.com/projects/p/cartridge/
.. _`security@jupo.org`: mailto:security@jupo.org?subject=Mezzanine+Security+Issue
.. _`#mezzanine IRC channel`: irc://freenode.net/mezzanine
.. _`Freenode`: http://freenode.net
.. _`Django's internationalization`: https://docs.djangoproject.com/en/dev/topics/i18n/translation/
.. _`virtualenvwrapper`: http://www.doughellmann.com/projects/virtualenvwrapper
