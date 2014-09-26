from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import ViewletBase
from ..interfaces import ICloudStorage

from netsight.cloudstorage import MessageFactory as _


class StatusViewlet(ViewletBase):

    index = ViewPageTemplateFile('status_viewlet.pt')

    def __init__(self, context, request, view, manager=None):
        super(StatusViewlet, self).__init__(context, request, view,
                                            manager=None)
        self.adapter = ICloudStorage(self.context, None)

    def available(self):
        if self.adapter is None:
            return False
        return len(self.adapter.valid_fieldnames()) > 0

    def status_message(self):
        if self.adapter.has_in_progress_uploads():
            return _(u'File data for this item is currently being uploaded '
                     u'to secure cloud storage')
        elif self.adapter.has_uploaded_all_fields():
            return _(u'File data for this item is being served from '
                     u'secure cloud storage')
        else:
            return _(u'File data for this item can be uploaded to '
                     u'secure cloud storage')

    def upload_possible(self):
        in_progress = self.adapter.has_in_progress_uploads()
        uploaded_all = self.adapter.has_uploaded_all_fields()
        if in_progress is False and \
           uploaded_all is False and \
           self.available() is True:
            return True
        return False

    def processing_url(self):
        return u'%s/@@manual-processing' % self.context.absolute_url()
