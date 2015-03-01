# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Interfaces for CloudStorage
"""
from zope import schema
from zope.interface import Interface


class IProductLayer(Interface):
    """ A layer specific to netsight.cloudstorage """


class ICloudStorage(Interface):
    """ Marker interface for CloudStorage adapter """


class ICloudStorageSettings(Interface):
    """
    Cloud Storage settings interface
    """
    aws_access_key = schema.TextLine(title=u'AWS Access Key')
    aws_secret_access_key = schema.TextLine(title=u'AWS Secret Access Key')
    bucket_name = schema.TextLine(title=u'S3 bucket name')
    min_file_size = schema.Int(
        title=u'Minimum file size(MB)',
        description=u'This is the file size above which file field contents '
                    u'will be automatically uploaded to cloud storage to avoid'
                    u' being served from Plone',
        default=10
    )
    transcoding_enabled = schema.Bool(
        title=u'Video transcoding enabled?',
        description=u'Whether or not files with "video" mimetype will be '
                    u'transcoded using Elastic Transcoder ',
        default=True
    )
    pipeline_name = schema.TextLine(
        title=u'Elastic transcoder pipeline name',
        description=u'The name of the pipeline that will be created in AWS to '
                    u'manage transcoding jobs. (Limit 30 characters)',
        max_length=30,
        required=False
    )
    email_notifications = schema.Bool(
        title=u'Send email notifications',
        description=u'Whether or not email notifications are sent when certain'
                    u' tasks complete. For example once an upload has '
                    u'finished.',
        default=True
    )
