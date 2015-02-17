from plone.namedfile.browser import Download as Base
from netsight.cloudstorage.interfaces import ICloudStorage


class Download(Base):
    def __call__(self):
        instance = self.context
        fieldname = self.fieldname
        get_transcoded = bool(self.request.get('transcoded', False))
        adapter = ICloudStorage(instance)
        url = adapter.get_url(fieldname, get_transcoded)
        if url is not None:
            return self.request.response.redirect(url)

        return super(Download, self).__call__()
