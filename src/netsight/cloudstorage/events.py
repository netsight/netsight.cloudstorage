# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Events specific to the Cloud Storage egg
"""
from zope.interface import implements
from zope.interface import Interface
from zope.interface import Attribute
from netsight.cloudstorage import MessageFactory as _


class IUploadComplete(Interface):
    """
    Interface for UploadComplete Event
    """
    context = Attribute(_(u'The object which the uploaded field is on'))
    fieldname = Attribute(_(u'The name of the field on context'))


class ITranscodeComplete(Interface):
    """
    Interface for TranscodeComplete event
    """
    context = Attribute(_(u'The object which the transcoded video is on'))
    fieldname = Attribute(_(u'The name of the field on context'))


class IUploadFailed(Interface):
    """
    Interface for UploadFailed event
    """
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
