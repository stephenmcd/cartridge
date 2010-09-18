========
Overview
========

Cartridge is a shopping cart application built using the `Django`_ framework. 
It is `BSD licensed`_ and designed to provide you with a clean and simple 
base for developing e-commerce websites. It purposely does not include every 
conceivable feature an e-commerce website could potentially use, instead 
focusing on providing only the core features that are common to every 
e-commerce website. 

This specific focus stems from the idea that every e-commerce website is 
different, tailoring to the particular business and products at hand, and 
should therefore be as easy as possible to customize. Cartridge achieves 
this goal with a code-base that implements only the core features of an 
e-commerce site, therefore remaining as simple as possible.

Features
========

  * Hierarchical categories
  * Easily configurable product options (colours, sizes, etc.)
  * Hooks for shipping calculations and payment gateway
  * Sale pricing
  * Stock management
  * Product popularity
  * Thumbnail generation
  * Built-in test suite
  * Separation of presentation (no embedded markup)
  * Smart categories (by price range, colour, etc)
  * Configurable nunber of checkout steps
  * Denormalised data for accessiblilty and performance

Dependencies
============

Cartridge is designed as a plugin for the `Mezzanine`_ content management 
platform.

Installation
============

Assuming you have `setuptools`_ installed, the easiest method is to install 
directly from pypi by running the following command, which will also attempt 
to install the dependencies mentioned above::

    $ easy_install -U cartridge

Otherwise you can download Cartridge and install it directly from source::

    $ python setup.py install
    
Once installed, the command ``mezzanine-project`` should be available via 
Mezzanine, which can be used for creating a new Cartridge project in a 
similar fashion to ``django-admin.py``::

    $ mezzanine-project -a cartridge project_name

You can then run your project with the usual Django steps::

    $ cd project_name
    $ python manage.py syncdb
    $ python manage.py runserver

Contributing
============

Cartridge is an open source project that is managed using both Git and 
Mercurial version control systems. These repositories are hosted on both 
`Github`_ and `Bitbucket`_ respectively, so contributing is as easy as 
forking the project on either of these sites and committing back your 
enhancements. 

Support
=======

For general questions or comments, please join the 
`mezzanine-users`_ mailing list. To report a bug or other type of issue, 
please use the `Github issue tracker`_.

.. _`Django`: http://djangoproject.com/
.. _`BSD licensed`: http://www.linfo.org/bsdlicense.html
.. _`setuptools`: http://pypi.python.org/pypi/setuptools
.. _`Mezzanine`: http://mezzanine.jupo.org/
.. _`Github`: http://github.com/stephenmcd/cartridge/
.. _`Bitbucket`: http://bitbucket.org/stephenmcd/cartridge/
.. _`mezzanine-users`: http://groups.google.com/group/mezzanine-users
.. _`Github issue tracker`: http://github.com/stephenmcd/cartridge/issues
