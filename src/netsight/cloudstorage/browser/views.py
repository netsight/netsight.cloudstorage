import logging

from Products.Five import BrowserView
from plone import api
from zope.event import notify

from ..interfaces import ICloudStorage
from netsight.cloudstorage.events import UploadComplete
from netsight.cloudstorage.events import TranscodeComplete

logger = logging.getLogger('netsight.cloudstorage')


class CloudStorageProcessing(BrowserView):
    def valid_request(self):
        fieldname = self.request.get('identifier')
        adapter = ICloudStorage(self.context)
        if fieldname not in adapter.valid_fieldnames():
            logger.error('Retrieve got invalid identifier: %s', fieldname)
            return False
        token = self.request.get('security_token')
        if token != adapter.security_token_for(fieldname):
            logger.error('Retrieve got incorrect security token')
            return False
        return True

    def retrieve(self):
        if not self.valid_request():
            self.request.response.setStatus(403)
            return 'Error'
        fieldname = self.request.get('identifier')
        logger.debug('Returning data to celery for: %s (%s)',
                     '/'.join(self.context.getPhysicalPath()), fieldname)
        adapter = ICloudStorage(self.context)
        # prevent the data being themed (as this would break it)
        self.request.response.setHeader('X-Theme-Disabled', 'True')
        return adapter.get_data_for(fieldname)

    def callback(self):
        # TODO: Change this to fire an event and register handlers
        if not self.valid_request():
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

    def error_callback(self):
        """
        Callback view if there was an error
        """
        if not self.valid_request():
            self.request.response.setStatus(403)
            return 'Error'
        fieldname = self.request.get('identifier')
        adapter = ICloudStorage(self.context)
        logger.warn('Celery encountered and error whilst trying to upload %s. '
                    'See Celery logs for more details.', fieldname)
        adapter.remove_from_in_progress(fieldname)


class ProcessCloudStorage(BrowserView):
    def manual_processing(self):
        """
        View to manually trigger processing
        """
        adapter = ICloudStorage(self.context)
        adapter.enqueue(enforce_file_size=False)
        api.portal.show_message(message='Upload initiated',
                                request=self.request)
        return self.request.response.redirect(self.context.absolute_url())
