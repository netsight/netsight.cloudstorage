.. image:: https://travis-ci.org/netsight/netsight.cloudstorage.svg?branch=master
    :target: https://travis-ci.org/netsight/netsight.cloudstorage
    
netsight.cloudstorage
=====================

Support for (securely) offloading Plone file data to the cloud.

This package provides two things:

* Offloading large files to the cloud
* Transcoding of video to web-compatible format
* Doing so in a secure manner that doesn't bypass Plone's security model

At the moment this is done using `Amazon Web Services`_
(S3 for cloudstorage, Elastic Transcoder for transcoding),
but could potentially be expanded to support other cloud storage services.

File data is first stored in Plone, and then synced to the cloud. Subsequent
requests for the file data are redirected to a unique auto-expiring
cloud URL (which prevents the data from unauthorised access).

.. _`Amazon Web Services`:  http://aws.amazon.com

Requirements
============

Uploads are handled asynchronously by `Celery`_, for which you need to
configure a `supported broker`_.

.. _`Celery`: http://docs.celeryproject.org
.. _`supported broker`: http://docs.celeryproject.org/en/latest/getting-started/brokers

Buildout configuration
======================

You will need to add the following to your buildout:

* `netsight.cloudstorage` egg into 'eggs'
* A part to build celery (e.g. using collective.recipe.celery)
* `broker_url` and `plone_url` variables to your zope instance

Example buildout config
-----------------------

.. code:: ini

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

  plone_url http://localhost:8080/VirtualHostBase/http/www.example.com:80/Plone/VirtualHostRoot/

An example buildout configuration for redis is provided in case you want to configure
it using buildout and run with supervisor. Look at files `redis.cfg` and `redis.conf.tpl`
for more information.


AWS Configuration
=================

Installing the `netsight.cloudstorage` add-on in the control panel will give you
a 'CloudStorage Settings' option. You will need to provide:

* Your AWS Access Key
* Your AWS Secret Access Key
* S3 bucket name
  This is the name of the bucket where files will be uploaded.
  If it does not exist, it will be created for you when the first file is
  uploaded.
* Minimum file size
  Any files uploaded above this size will automatically be sent to the cloud.
  Smaller files can still be manually uploaded.

Example AWS Policy
------------------

Here is an example policy you can use to grant a specific user access to a specific S3 bucket:

.. code:: json

  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::netsight-cloudstorage-mybucket",
                "arn:aws:s3:::netsight-cloudstorage-mybucket/*"
            ]
        }
    ]
  }

For more details on AWS users and policies, see http://docs.aws.amazon.com/IAM/latest/UserGuide/access.html

How it works
============

The package registers an event subscribe that watches for new file field uploads.
If the size of the file data exceeds the 'minimum file size' set above, it
will register a celery task that asyncronously uploads the data to the cloud.

Once the upload is complete, celery will notify Plone, which generates an email
to the content creator.

Once the cloud copy is available, the package patches the 'download' methods so
that any requests for the file data result in a redirect to the cloud copy.
Each request generates an auto-expiring one-time URL to the cloud copy, ensuring
the security of the cloud data.

Transcoding
===========

Files with a 'video' mimetype are also sent through a transcoding pipeline if this
option is enabled in the control panel.

This transcoded version is stored separately, and must be manually requested
by passing 'transcoded=true' on the file download request e.g.

  http://myplonesite/folder/myfile/at_download/file?transcoded=true

Files are currently transcoded using the 'Generic 480p 16:9' preset (`1351620000001-000020`_)

To enable transcoding, you first need to create a specific S3 bucket to save the
transcoded files. This specific S3 bucket must be called like the one used to
store the files, but ended in "-transcoded". If you S3 bucket is called
"netsight-cloudstorage-plone-storage", you need to create a new bucket called
"netsight-cloudstorage-plone-storage-transcoded".

Then you need to create a transcoding pipeline. To do that, login to your AWS account,
go to Application Services -> Elastic Transcoder and create a new Pipeline. Choose a
name for the pipeline (you will have to set this name in the Control Panel), set
the default S3 bucket ("netsight-cloudstorage-plone-storage") as an input bucket and
set the new one ("netsight-cloudstorage-plone-storage-transcoded") as an ouput bucket
both for files and playlists, and also for thumbnails.


.. _`1351620000001-000020`: http://docs.aws.amazon.com/elastictranscoder/latest/developerguide/system-presets.html

TODO
====

* Support for other transcoding presets
* Support other cloud backends
