netsight.cloudstorage
=====================

Support for offloading Plone file data to the cloud.

This package provides two things:

* Offloading large files to
* Transcoding of video to web-compatible format

At the moment this is done using Amazon Web Services (S3 for cloudstorage, 
Elastic Transcoder for transcoding), but could potentially be expanded to support
other cloud services.

Requirements
============

Uploads are handled asynchronously by `Celery <http://docs.celeryproject.org>`_, for which you need to configure
a `supported broker <http://docs.celeryproject.org/en/latest/getting-started/brokers>`_

Configuration
=============

You will need to add the following to your buildout:

* `netsight.cloudstorage` egg into 'eggs'
* A part to build celery (e.g. using collective.recipe.celery)
* `broker_url` and `plone_url` variables to your zope instance

Example buildout config
-----------------------

::

   [buildout]
   ...

   [celery]
   recipe = collective.recipe.celery
   eggs =
        ${instance:eggs}
        netsight.cloudstorage
   broker-transport = redis
   broker-host = redis://localhost:6379/0
   result-backend = redis
   result-dburi = redis://localhost:6379/0
   imports = netsight.cloudstorage.tasks
   celeryd-logfile = ${buildout:directory}/var/log/celeryd.log
   celeryd-log-level = info
   celeryd-concurrency = 2

   [instance]
   ...
   zope-conf-additional =
        <product-config netsight.cloudstorage>
                broker_url ${celery:broker-host}
                plone_url http://localhost:8080
        </product-config>


Please note that `plone_url` is used by the celery working to read from and send events to Plone. If you are using Virtual Hosting, you will need to include your VH config in the variable e.g.:

::

    plone_url http://localhost:1234/VirtualHostBase/https/example.com:443/Plone/VirtualHostRoot/


