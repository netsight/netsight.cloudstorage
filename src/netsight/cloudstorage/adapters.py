# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
The adapters for CloudStorage
"""
import logging
from uuid import uuid4

from BTrees.OOBTree import OOBTree
from Products.CMFCore.interfaces import IContentish
import transaction
from celery import group
from netsight.cloudstorage.utils import get_value_from_config
from netsight.cloudstorage.utils import get_value_from_registry
from persistent.dict import PersistentDict
from zope.annotation import IAnnotations
from zope.component import adapts, getUtility
from zope.interface import implements

from boto.s3.connection import S3Connection

from .tasks import upload_to_s3
from .tasks import upload_callback
from .tasks import transcode_video
from .tasks import transcode_callback
from .interfaces import ICloudStorage

logger = logging.getLogger("netsight.cloudstorage")
DATA_KEY = 'cloudstorage_data'


class CloudStorage(object):
    """
    Adapter to provide facility to upload (large) files in content to cloud
    storage.

    :param context: the content object to be adapted
    """
    implements(ICloudStorage)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def _getStorage(self):
        annotations = IAnnotations(self.context)
        if DATA_KEY not in annotations:
            storage = OOBTree()
            annotations[DATA_KEY] = storage
            storage['cloud_available'] = PersistentDict()
            storage['in_progress'] = PersistentDict()
        return annotations[DATA_KEY]

    def _getFields(self, ignore_empty=True):
        """ Get an iterable of the file-like fields for context """
        result = []

        unwrapped = self.context.aq_base

        if hasattr(unwrapped, 'Schema'):
            schema = unwrapped.Schema()
            for field in schema.fields():
                if field.type in ['file', 'blob']:
                    result.append({
                        'name': field.getName(),
                        'context_uid': self.context.UID(),
                        'mimetype': field.getContentType(self.context),
                        'size': field.get_size(self.context),
                        'filename': field.getFilename(self.context),
                    })
        else:
            try:
                from plone.dexterity.interfaces import IDexterityFTI
                from plone.namedfile.interfaces import INamedBlobFile
            except ImportError:
                return result

            # could be dexterity
            schema = getUtility(IDexterityFTI,
                                name=unwrapped.portal_type).lookupSchema()
            for name in (schema or []):
                field = getattr(unwrapped, name)
                if not INamedBlobFile.providedBy(field):
                    continue
                result.append({
                    'name': name,
                    'context_uid': self.context.UID(),
                    'mimetype': field.contentType,
                    'size': field.size,
                    'filename': field.filename,
                })

        if ignore_empty:
            result = [x for x in result if x['size'] > 0]

        return result

    def _get_s3_connection(self):
        """Set up an S3 connection using the registry settings"""
        aws_key = get_value_from_registry('aws_access_key')
        aws_secret_key = get_value_from_registry('aws_secret_access_key')
        return S3Connection(aws_key, aws_secret_key)

    def _get_bucket(self, postfix=None):
        """Look up the a bucket set in the registry"""
        s3 = self._get_s3_connection()
        bucket_name = 'netsight-cloudstorage-{reg_value}'.format(
            reg_value=get_value_from_registry('bucket_name')
        )
        if postfix:
            bucket_name += postfix
        bucket = s3.lookup(bucket_name)
        if bucket is None:
            logger.warn('Bucket does not exist %s', bucket_name)
        return bucket

    def _get_transcoded_bucket(self):
        """Look up the transcoded bucket set in the registry"""
        return self._get_bucket(postfix='-transcoded')

    def field_info(self, fieldname):
        """
        Look up the field data for a single field

        :param fieldname: Name of the field to lookup
        """
        fields = self._getFields()
        for info in fields:
            if fieldname == info['name']:
                return info

    def valid_fieldnames(self):
        """
        Get a list of the fieldnames on the adapted object

        :return: list of fieldnames
        :rtype: list
        """
        return [x['name'] for x in self._getFields()]

    def has_in_progress_uploads(self):
        """
        Check if the adapted object has any fields that are currently being
        uploaded

        :return: whether adapted object has uplaods in progress
        :rtype: bool
        """
        storage = self._getStorage()
        return len(storage['in_progress'].keys()) > 0

    def has_uploaded_all_fields(self):
        """
        Check if the adapted object has uploaded all its fields

        :return: whether all the fields on the adapted object have been
                 uploaded
        :rtype: bool
        """
        storage = self._getStorage()
        return (set(self.valid_fieldnames()) ==
                set(storage['cloud_available'].keys()))

    def has_uploaded_any_fields(self):
        """
        Check if the adapted object has uploaded any fields

        :return: whether any of the fields on the adapted object have been
                 uploaded
        :rtype: bool
        """
        storage = self._getStorage()
        return len(storage['cloud_available']) > 0

    def get_data_for(self, fieldname):
        """
        Return the data stored within the field

        :param fieldname: name of the field on the adapter object
        :return: the byte data contained in the given field
        :rtype: str
        """

        if hasattr(self.context, 'getField'):
            field = self.context.getField(fieldname)
            if field is not None:
                return field.get(self.context)

        return getattr(self.context, fieldname).data

    def security_token_for(self, fieldname):
        """
        Get the generated security token for the given field, for use by
        callbacks

        :param fieldname: the name of the field on the adapted object
        :return: the security token
        :rtype: str
        """
        storage = self._getStorage()
        return storage['in_progress'].get(fieldname, None)

    def mark_as_cloud_available(self, fieldname):
        """
        Once an upload has completed this method should be called to mark the
        field as uploaded to cloud storage on the annotation storage of the
        adapted object

        :param fieldname: name of the field on the adapted object to mark as
                          uploaded
        """
        storage = self._getStorage()
        storage['in_progress'].pop(fieldname)
        storage['cloud_available'][fieldname] = True
        transaction.commit()

    def remove_from_in_progress(self, fieldname):
        """
        If upload fails, this method should be called to remove the field from
        the inprogress anontation

        :param fieldname: name of the field on the adapted object
        """
        storage = self._getStorage()
        storage['in_progress'].pop(fieldname)
        transaction.commit()

    def has_transcoded_version(self, fieldname):
        """
        Is there a trancoded version of the given field (video) available?

        :param fieldname: name of the field on the adapted object
        :return: whether a transcoded version of the field exists in cloud
                 storage
        :rtype: bool
        """
        bucket = self._get_transcoded_bucket()
        if bucket is None:
            return
        return bucket.get_key(
            '%s-%s' % (fieldname, self.context.UID())
        ) is not None

    def delete_from_cloud(self):
        cloud_available = self._getStorage()['cloud_available']

        if not cloud_available:
            return

        normal_bucket = self._get_bucket()
        transcoded_bucket = self._get_transcoded_bucket()
        all_buckets = filter(None, [normal_bucket, transcoded_bucket])

        for bucket in all_buckets:
            for fieldname in cloud_available:
                key = bucket.get_key(
                    '%s-%s' % (fieldname, self.context.UID())
                )
                if key is not None:
                    logger.info(
                        'Removing item from cloud storage: %s (%s)' % (
                            self.context.absolute_url(),
                            fieldname))
                    key.delete()

        cloud_available.clear()

    def enqueue(self, enforce_file_size=True):
        """
        Dispatch any relevant file fields off to Celery

        :param enforce_file_size: Allow manually uploading files smaller than
                                  the configured minimum
        :type enforce_file_size: bool
        """
        logger.info('Enqueue called for %s' % self.context.absolute_url())
        in_progress = self._getStorage()['in_progress']
        cloud_available = self._getStorage()['cloud_available']

        for field in self._getFields():
            if not field['size'] > 0:
                # Ignore empty fields
                continue

            # Remove existing cloud info, assuming file data has changed
            if field['name'] in cloud_available:
                del cloud_available[field['name']]

            min_size = get_value_from_registry('min_file_size')
            if field['size'] < min_size * 1024 * 1024 and enforce_file_size:
                logger.info('Field %s on %s is too small (< %sMB)',
                            field['name'],
                            self.context.absolute_url(),
                            min_size)
                continue

            # unique token for this job
            security_token = uuid4().hex
            in_progress[field['name']] = security_token
            # make sure storage token is stored before
            # job goes on queue
            transaction.commit()

            path = '/'.join(self.context.getPhysicalPath())
            plone_url = get_value_from_config('plone_url')
            root_url = '%s/%s' % (plone_url, path)

            logger.info('Queuing field %s on %s to be uploaded', field['name'],
                        self.context.absolute_url())
            source_url = '%s/@@cloudstorage-retrieve' % root_url
            callback_url = '%s/@@cloudstorage-callback' % root_url
            errorback_url = '%s/@@cloudstorage-error' % root_url
            bucket_name = 'netsight-cloudstorage-%s' % get_value_from_registry(
                'bucket_name'
            )
            aws_key = get_value_from_registry('aws_access_key')
            aws_secret_key = get_value_from_registry('aws_secret_access_key')
            pipeline_name = get_value_from_registry('pipeline_name')
            upload_task = upload_to_s3.s(
                bucket_name=bucket_name,
                source_url=source_url,
                callback_url=callback_url,
                errorback_url=errorback_url,
                field=field,
                security_token=security_token,
                aws_key=aws_key,
                aws_secret_key=aws_secret_key,
                pipeline_name=pipeline_name,
            )
            logger.info('File mimetype: %s', field['mimetype'])
            transcoding_enabled = get_value_from_registry(
                'transcoding_enabled'
            )
            if transcoding_enabled and field['mimetype'].startswith('video'):
                links = group(upload_callback.s(),
                              transcode_video.s(),
                              transcode_callback.s())
            else:
                links = group(upload_callback.s())
            upload_task.link(links)
            upload_task.apply_async()

    def get_url(self, fieldname, transcoded=False, expiry_seconds=60):
        """
        Get URL of fieldname from S3

        :param fieldname: Name of the field on the adapted object
        :type fieldname: str
        :param transcoded: Whether or not to attempt to get a transcoded
                           version of a video
        :return: URL on S3 of given field's content
        :rtype: str
        """
        storage = self._getStorage()
        if fieldname not in storage['cloud_available']:
            logger.warn('%s on %s not available in the cloud', fieldname,
                        self.context.absolute_url())
            return None
        fieldinfo = self.field_info(fieldname)
        if not fieldinfo:
            logger.error('Field info for %s missing from context %s', fieldname,
                         self.context.absolute_url())
            return
        bucket_name = 'netsight-cloudstorage-%s' % get_value_from_registry(
            'bucket_name'
        )
        s3 = self._get_s3_connection()
        response_headers = {}
        key = None
        if transcoded:
            transcoded_bucket_name = '%s-transcoded' % bucket_name
            bucket = s3.lookup(transcoded_bucket_name)
            if bucket is not None:
                # Check if it is available in the transcoded bucket
                key = bucket.get_key(
                    '%s-%s' % (fieldname, self.context.UID())
                )
            else:
                logger.warn('Transcode bucket does not exist %s',
                            transcoded_bucket_name)
        if key is None:
            bucket = s3.lookup(bucket_name)
            if bucket is not None:
                key = bucket.get_key(
                    '%s-%s' % (fieldname, self.context.UID())
                )
                if key is None:
                    logger.error('File not found: %s on %s', fieldname,
                                 self.context.absolute_url())
                    return
            else:
                logger.error('Bucket %s does not exist', bucket_name)
                return
            if not transcoded:
                response_headers = {
                    'response-content-disposition':
                        'attachment; filename="%s"' % fieldinfo['filename'],
                    'response-content-type': fieldinfo['mimetype']
                }
        return key.generate_url(expiry_seconds, response_headers=response_headers)
