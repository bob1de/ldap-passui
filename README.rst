LDAP PassUI
===========

This project was inspired by `the work of Jacob Jirutka
<https://github.com/jirutka/ldap-passwd-webui>`_.

The aim of this project is to provide a simple web form for users to
be able to conveniently change their password stored in LDAP or Active
Directory (Samba 4 AD). The password change is done with the LDAP
Password Modify Extended Operation, hence your LDAP server can hash it
with whatever algorithm you configured there.

It's built with Bottle, a WSGI micro web-framework for Python.

Compared to the original project linked above, it provides:

* Configurable password policies, validated both server-side and live
  in JavaScript while typing
* Freely configurable, dynamic bind DN's and search filters
* Configuration via YAML file, including configuration validation.
* A lightweight Docker image based on Alpine Linux for easy deployment


Installation
------------

Docker
~~~~~~

Included with this repository, there is both a ``Dockerfile`` and a
``docker-compose.yaml`` to get it up and running in no time.

The build is based on the minimalist Alpine Linux, bundled with uWSGI
to serve the application. The image is just about 65 MiB in size.

The only steps needed are:

::

    cp config.yaml.example config.yaml
    # adjust the configuration as required
    docker-compose up -d --build
    # access it on http://localhost:8080

You can change the settings in ``docker-compose.yaml`` and ``uwsgi.yaml``
to suit your needs. It does also run nicely on a swarm.


Manually
~~~~~~~~

Python 3.x is required. Testing was done with Python 3.5 and 3.6.

Just install the dependencies.

::

    pip install -r requirements.txt

Read the next sections to learn how to run it.


Configuration
-------------

Configuration is read from the file ``config.yaml.example``. You may
change the location using the environment variable ``CONFIG_FILE``.
Take `config.yaml.example <config.yaml.example>`_ as a starting point
and adapt it to your needs.

If you have Active Directory (or Samba 4 AD), then you *must* use
encrypted connections (i.e. LDAPS or STARTTLS). AD doesn’t allow
changing passwordsvia unencrypted connections


Run it
------

There are multiple ways for running it:

* with the built-in default WSGI server based on wsgiref
* under a production WSGI] server like uWSGI


Run with the built-in server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

   Don't do this in production environments.

Simply execute the ``app.py``:

::

    python3 app.py

Then you can access the app on ``http://localhost:8080``. The port and
host may be changed in the configuration file.


Run with uWSGI
~~~~~~~~~~~~~~

This is also what the provided Docker image uses. I won't explain
all available options for running uWSGI. Simply adapt the `uwsgi.yaml
<uwsgi.yaml>`_ file to your needs and run it.

::

    uwsgi --yaml uwsgi.yaml

There are plenty of resources out on the internet on how to configure
uWSGI and maybe a load-balancer like nginx or haproxy in front.
