# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
from zope import schema
from zope.interface import Interface


class ICloudStorage(Interface):
    """ Marker interface for CloudStorage adapter """


class ICloudStorageSettings(Interface):

    aws_access_key = schema.TextLine(title=u'AWS Access Key')
    aws_secret_acces_key = schema.TextLine(title=u'AWS Secret Access Key')
    bucket_name = schema.TextLine(title=u'S3 bucket name')
    min_file_size = schema.Int(
        title=u'Minimum file size(MB)',
        description=u'This is the file size above which file field contents '
                    u'will be automatically uploaded to cloud storage to avoid'
                    u' being served from Plone')
