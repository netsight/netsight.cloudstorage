from zope.interface import implements
from zope.interface import Interface
from zope.interface import Attribute
from netsight.cloudstorage import MessageFactory as _


class IUploadComplete(Interface):

    context = Attribute(_(u'The object which the uploaded field is on'))
    fieldname = Attribute(_(u'The name of the field on context'))


class ITranscodeComplete(Interface):

    context = Attribute(_(u'The object which the transcoded video is on'))
    fieldname = Attribute(_(u'The name of the field on context'))


class IUploadFailed(Interface):

    context = Attribute(_(u'The object which the uploaded field is on'))
    fieldname = Attribute(_(u'The name of the field on context'))


class UploadComplete(object):
    """
    Event to be fired when a cloud storage upload completes
    """
    implements(IUploadComplete)

    def __init__(self, context, fieldname):
        self.context = context
        self.fieldname = fieldname


class TranscodeComplete(object):
    """
    Event to be fired when a video in cloud storage has been transcoded
    """
    implements(ITranscodeComplete)

    def __init__(self, context, fieldname):
        self.context = context
        self.fieldname = fieldname


class UploadFailed(object):
    """
    Event to be fired when a an upload fails
    """
    implements(IUploadFailed)

    def __init__(self, context, fieldname):
        self.context = context
        self.fieldname = fieldname
