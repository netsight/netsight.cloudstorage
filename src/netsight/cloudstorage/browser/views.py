import logging

from Products.Five import BrowserView
from netsight.cloudstorage.interfaces import ICloudStorage
from netsight.cloudstorage.tasks import test_task

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
        if not self.valid_request():
            self.request.response.setStatus(403)
            return 'Error'
        fieldname = self.request.get('identifier')
        adapter = ICloudStorage(self.context)
        logger.info('Celery says %s has been uploaded', fieldname)
        adapter.mark_as_cloud_available(fieldname)


class ProcessCloudStorage(BrowserView):
    def manual_processing(self):
        """
        View to manually trigger processing
        """
        adapter = ICloudStorage(self.context)
        adapter.enqueue()

    def test_celery(self):
        test_task.apply_async()