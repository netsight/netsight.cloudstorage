# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
import logging
from uuid import uuid4

from BTrees.OOBTree import OOBTree
from Products.CMFCore.interfaces import IContentish
import transaction
from persistent.dict import PersistentDict
from zope.annotation import IAnnotations
from zope.component import adapts, getUtility
from zope.interface import implements

from netsight.cloudstorage.tasks import upload_to_s3, upload_callback
from .interfaces import ICloudStorage
from .config import BUCKET_NAME

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
            # Check field content type
            mimetype = field['mimetype']

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

            root_url = self.context.absolute_url()

            logger.debug('Queuing field %s to be uploaded' % field['name'])
            source_url = '%s/@@cloudstorage-retrieve' % root_url
            callback_url = '%s/@@cloudstorage-callback' % root_url
            bucket_name = 'netsight.cloudstorage.%s' % BUCKET_NAME
            upload_task = upload_to_s3.s(
                bucket_name,
                source_url,
                callback_url,
                field,
                security_token
            )
            upload_task.apply_async(link=upload_callback.s())

    def get_url(self, fieldname):
        """
        Get URL of fieldname from S3
        :return: URL on S3 of given field's content
        :rtype: str
        """
        return 'http://google.com'

