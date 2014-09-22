# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
import logging
from uuid import uuid4

from BTrees.OOBTree import OOBTree
from Products.CMFCore.interfaces import IContentish
import transaction
from netsight.cloudstorage.utils import get_value_from_config, \
    get_value_from_registry
from persistent.dict import PersistentDict
from zope.annotation import IAnnotations
from zope.component import adapts, getUtility
from zope.interface import implements

from boto.s3.key import Key
from boto.s3.connection import S3Connection

from .tasks import upload_to_s3, upload_callback
from .interfaces import ICloudStorage
from .config import BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

logger = logging.getLogger("netsight.cloudstorage")
DATA_KEY = 'cloudstorage_data'
port = get_value_from_config('instance_port')


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

    def _getFields(self):
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
                    })
        else:
            from plone.dexterity.interfaces import IDexterityFTI
            from plone.namedfile.interfaces import INamedBlobFile
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
                })

        return result

    def valid_fieldnames(self):
        return [x['name'] for x in self._getFields()]

    def get_data_for(self, fieldname):
        field = self.context.getField(fieldname)
        if field is not None:
            return field.get(self.context)
        else:
            return getattr(self.context, fieldname).data

    def security_token_for(self, fieldname):
        storage = self._getStorage()
        return storage['in_progress'].get(fieldname, None)

    def mark_as_cloud_available(self, fieldname):
        storage = self._getStorage()
        storage['in_progress'].pop(fieldname)
        storage['cloud_available'][fieldname] = True

    def enqueue(self):
        """ Dispatch any relevant file fields off to Celery """

        logger.info('enqueue called for %s' % self.context.absolute_url())

        for field in self._getFields():
            min_size = get_value_from_registry('min_file_size')
            if field['size'] < min_size * 1024 * 1024:
                logger.info('File on field %s is too small (< %sMB)',
                             field['name'],
                             min_size)
                continue
            # TODO: Find and define "valid formats"
            # if mimetype not in VALID_FORMATS:
            #     continue

            in_progress = self._getStorage()['in_progress']
            # unique token for this job
            security_token = uuid4().hex
            in_progress[field['name']] = security_token
            # make sure storage token is stored before
            # job goes on queue
            transaction.commit()

            path = '/'.join(self.context.getPhysicalPath())
            root_url = 'http://localhost:%s/%s' % (port, path)

            logger.debug('Queuing field %s to be uploaded' % field['name'])
            source_url = '%s/@@cloudstorage-retrieve' % root_url
            callback_url = '%s/@@cloudstorage-callback' % root_url
            bucket_name = 'netsight-cloudstorage-%s' % get_value_from_registry(
                'bucket_name'
            )
            aws_key = 1
            aws_secret_key = 1
            upload_task = upload_to_s3.s(
                bucket_name,
                source_url,
                callback_url,
                field,
                security_token,
                aws_key,
                aws_secret_key
            )
            upload_task.apply_async(link=upload_callback.s())

    def get_url(self, fieldname):
        """
        Get URL of fieldname from S3
        :return: URL on S3 of given field's content
        :rtype: str
        """
        storage = self._getStorage()
        if fieldname in storage['cloud_available'].keys():
            s3 = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            bucket_name = 'netsight.cloudstorage.%s' % BUCKET_NAME
            bucket = s3.lookup(bucket_name)
            if bucket is None:
                logger.warn('Bucket %s does not exist', bucket_name)
                return None
            key = Key(bucket)
            key.key = '%s-%s' % (fieldname, self.context.UID())
            return key.generate_url(60)
        else:
            logger.warn('Field %s is not yet available in cloudstorage',
                        fieldname)
        return None

