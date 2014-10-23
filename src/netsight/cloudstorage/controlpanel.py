# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Definition of Plone Control Panel settings for CloudStorage
"""
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.z3cform import layout
from z3c.form import form

from .interfaces import ICloudStorageSettings


class CloudStorageControlPanelForm(RegistryEditForm):
    """
    CloudStorage settings form
    """
    form.extends(RegistryEditForm)
    schema = ICloudStorageSettings


CloudStorageControlPanelView = layout.wrap_form(
    CloudStorageControlPanelForm,
    ControlPanelFormWrapper
)
CloudStorageControlPanelView.label = u"CloudStorage settings"