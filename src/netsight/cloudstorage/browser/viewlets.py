# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Viewlets for CloudStorage
"""
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import ViewletBase
from ..interfaces import ICloudStorage

from netsight.cloudstorage import MessageFactory as _


class StatusViewlet(ViewletBase):
    """
    Viewlet mimicking the Plone "messages" framework, to display the current
    state of field data that would be uploaded to cloud storage
    """
    index = ViewPageTemplateFile('status_viewlet.pt')

    def __init__(self, context, request, view, manager=None):
        super(StatusViewlet, self).__init__(context, request, view,
                                            manager=None)
        self.adapter = ICloudStorage(self.context, None)

    def available(self):
        """
        Only render this viewlet if the object being viewed is able to be
        adapted and if it has valid fields

        :return: Whether to render this viewlet
        :rtype: bool
        """
        if self.adapter is None:
            return False
        return len(self.adapter.valid_fieldnames()) > 0

    def status_message(self):
        """
        Depending upon the status of the fields in the viewed object, differing
        messages will be displayed

        :return: The message to be displayed
        :rtype: str
        """
        if self.adapter.has_in_progress_uploads():
            return _(u'Uploading of file data to secure cloud storage for this'
                     u' item is currently in progress')
        elif self.adapter.has_uploaded_any_fields():
            return _(u'File data for this item is being served from '
                     u'secure cloud storage')
        else:
            return _(u'File data for this item can be uploaded to '
                     u'secure cloud storage')

    def upload_possible(self):
        """
        If the object has valid fileds and no uploads are in progress, nor are
        all the fields currently uploaded, then manual processing can be
        triggered

        :return: Whether manual processing can be triggered
        :rtype: bool
        """
        in_progress = self.adapter.has_in_progress_uploads()
        uploaded_all = self.adapter.has_uploaded_all_fields()
        if in_progress is False and \
           uploaded_all is False and \
           self.available() is True:
            return True
        return False

    def processing_url(self):
        """
        Generate the URL to trigger manual processing of fields on this object

        :return: The URL to trigger manual processing of fields on this object
        :rtype: str
        """
        return u'%s/@@manual-processing' % self.context.absolute_url()
