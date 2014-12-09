# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Views for Cloud Storage
"""
import logging

from Products.Five import BrowserView
from plone import api
from zope.event import notify

from ..interfaces import ICloudStorage
from netsight.cloudstorage.events import UploadComplete
from netsight.cloudstorage.events import TranscodeComplete

logger = logging.getLogger('netsight.cloudstorage')


class CloudStorageProcessing(BrowserView):
    """
    Browser view to allow celery to interact with Plone
    """
    def _valid_request(self):
        fieldname = self.request.get('identifier')
        adapter = ICloudStorage(self.context)
        if fieldname not in adapter.valid_fieldnames():
            logger.error('Retrieve got invalid identifier: %s on %s',
                         fieldname,
                         self.context.absolute_url())
            return False
        token = self.request.get('security_token')
        if token != adapter.security_token_for(fieldname):
            logger.error('Retrieve got incorrect security token for %s on %s',
                         fieldname,
                         self.context.absolute_url())
            return False
        return True

    def retrieve(self):
        """
        View used by Celery to get the file data of the field specified in the
        request to be uploaded to cloud storage

        :return: the byte data stored in the field passed in the request
        :rtype: str
        """
        if not self._valid_request():
            self.request.response.setStatus(403)
            return 'Error'
        fieldname = self.request.get('identifier')
        logger.debug('Returning data to celery for %s on %s',
                     fieldname,
                     self.context.absolute_url(),)
        adapter = ICloudStorage(self.context)
        # prevent the data being themed (as this would break it)
        self.request.response.setHeader('X-Theme-Disabled', 'True')
        return adapter.get_data_for(fieldname)

    def callback(self):
        """
        Callback view to allow Celery to alert Plone of the state of uploading
        or transcoding

        :return: If unable to validate, return an error and 403 status
        :rtype: HTTPResponse
        """
        if not self._valid_request():
            self.request.response.setStatus(403)
            return 'Error'
        fieldname = self.request.get('identifier')
        activity = self.request.get('activity')
        if activity == 'upload':
            notify(UploadComplete(self.context, fieldname))
        elif activity == 'transcode':
            notify(TranscodeComplete(self.context, fieldname))
        else:
            logger.error('Unknown activity callback from Celery: %s', activity)
        self.request.response.setStatus(200)
        logger.info('%s on %s marked as uploaded', fieldname, self.context.absolute_url())
        return 'Success'

    def error_callback(self):
        """
        Callback view if there was an error
        """
        if not self._valid_request():
            self.request.response.setStatus(403)
            return 'Error'
        fieldname = self.request.get('identifier')
        adapter = ICloudStorage(self.context)
        logger.warn('Celery encountered and error whilst trying to upload %s on'
                    ' %s . See Celery logs for more details.',
                    fieldname,
                    self.context.absolute_url())
        adapter.remove_from_in_progress(fieldname)


class ProcessCloudStorage(BrowserView):
    """
    Browser view for Plone for interacting with Cloud Storage
    """
    def manual_processing(self):
        """
        View to manually trigger processing
        """
        adapter = ICloudStorage(self.context)
        adapter.enqueue(enforce_file_size=False)
        api.portal.show_message(message='Upload initiated',
                                request=self.request)
        referer = self.request.get("HTTP_REFERER", "").strip()
        if not referer:
            referer = self.context.absolute_url()
        return self.request.response.redirect(referer)

    def has_cloudstorage(self):
        """
        Does this item have cloudstorage-stored data?
        """
        adapter = ICloudStorage(self.context)
        return adapter.has_uploaded_all_fields()
