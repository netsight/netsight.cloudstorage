import logging
from zope.component import queryAdapter
from ZPublisher.HTTPRequest import FileUpload

from .interfaces import ICloudStorage

logger = logging.getLogger(__name__)

def content_saved(object, event):
    """
    When an object is saved check its fields to see if any can be uploaded to
    S3
    """
    adapter = queryAdapter(object, ICloudStorage)
    if adapter is None:
        return

    if not hasattr(object.REQUEST, 'form'):
        return

    # look for file upload items on the request
    for key, value in object.REQUEST.form.items():
        if isinstance(value, FileUpload):
            value.seek(0)
            if len(value.read()):
                logger.info(
                    'Found file fields on %s. Enqueing upload',
                    '/'.join(object.getPhysicalPath())
                )
                adapter.enqueue()
                return