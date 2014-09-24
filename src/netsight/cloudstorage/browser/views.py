import logging

from Products.Five import BrowserView
from plone import api

from ..interfaces import ICloudStorage

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
        adapter = ICloudStorage(self.context)
        logger.info('Celery says %s has been uploaded', fieldname)
        adapter.mark_as_cloud_available(fieldname)

        if not adapter.has_uploaded_all_files():
            return

        creator = api.user.get(self.context.Creator())
        creator_email = creator.getProperty('email')
        subject = 'Files for %s have been uploaded' % self.context.Title()
        body ="""The files of %s at %s have been uploaded to cloud storage.

From now on when someone views this content, the large files will be served up from cloud storage
""" % (self.context.Title(), self.context.absolute_url())
        api.portal.send_email(
            recipient=creator_email,
            subject=subject,
            body=body,
        )


class ProcessCloudStorage(BrowserView):
    def manual_processing(self):
        """
        View to manually trigger processing
        """
        adapter = ICloudStorage(self.context)
        adapter.enqueue(enforce_file_size=False)
        # TODO: Redirect to self.context.absolute_url()
