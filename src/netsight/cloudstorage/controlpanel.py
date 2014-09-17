from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from my.package.interfaces import IZooSettings
from plone.z3cform import layout
from z3c.form import form


class CloudStorageControlPanelForm(RegistryEditForm):
    form.extends(RegistryEditForm)
    schema = IZooSettings


CloudStorageControlPanelView = layout.wrap_form(
    CloudStorageControlPanelForm,
    ControlPanelFormWrapper
)
CloudStorageControlPanelView.label = u"CloudStorage settings"