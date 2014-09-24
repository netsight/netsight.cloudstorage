"""
Monkeypatch FileField and BlobField download methods to allow returning
cloud based URL
"""
from netsight.cloudstorage.interfaces import ICloudStorage


def file_field_download(self, instance, **kwargs):
    fieldname = self.getName()
    adapter = ICloudStorage(instance)
    url = adapter.get_url(fieldname)
    if url is not None:
        return instance.REQUEST.RESPONSE.redirect(url)
    return self._old_download(instance, **kwargs)
