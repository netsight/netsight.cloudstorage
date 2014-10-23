# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Monkeypatch FileField and BlobField download methods to allow returning
cloud based URL
"""
from netsight.cloudstorage.interfaces import ICloudStorage


def file_field_download(self, instance, *args, **kwargs):
    fieldname = self.getName()
    get_transcoded = bool(instance.REQUEST.get('transcoded', False))
    adapter = ICloudStorage(instance)
    url = adapter.get_url(fieldname, get_transcoded)
    if url is not None:
        return instance.REQUEST.RESPONSE.redirect(url)
    return self._old_download(instance, **kwargs)
