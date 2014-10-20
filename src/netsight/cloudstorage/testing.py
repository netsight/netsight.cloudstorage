# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from plone.testing import z2

from zope.configuration import xmlconfig


class NetsightcloudstorageLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import netsight.cloudstorage
        xmlconfig.file(
            'configure.zcml',
            netsight.cloudstorage,
            context=configurationContext
        )

        # Install products that use an old-style initialize() function
        # z2.installProduct(app, 'Products.PloneFormGen')

#    def tearDownZope(self, app):
#        # Uninstall products installed above
#        z2.uninstallProduct(app, 'Products.PloneFormGen')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'netsight.cloudstorage:default')

NETSIGHT_CLOUDSTORAGE_FIXTURE = NetsightcloudstorageLayer()
NETSIGHT_CLOUDSTORAGE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(NETSIGHT_CLOUDSTORAGE_FIXTURE,),
    name="NetsightcloudstorageLayer:Integration"
)
NETSIGHT_CLOUDSTORAGE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(NETSIGHT_CLOUDSTORAGE_FIXTURE, z2.ZSERVER_FIXTURE),
    name="NetsightcloudstorageLayer:Functional"
)
