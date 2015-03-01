from Products.CMFCore.utils import getToolByName


PROFILE_ID = 'profile-netsight.cloudstorage:default'


def upgrade_to_0002(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('netsight.cloudstorage.upgrades.0001_0002')

    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'browserlayer')
    logger.info('Browserlayer installed')
    setup.runImportStepFromProfile(PROFILE_ID, 'plone.app.registry')
    logger.info('Registry settings reloaded')
