def uninstall(portal, reinstall=False):
    if not reinstall:
        from logging import getLogger
        logger = getLogger('netsight.cloudstorage.extensions.install.uninstall')

        setup_tool = portal.portal_setup
        setup_tool.runAllImportStepsFromProfile('profile-netsight.cloudstorage:uninstall')
        logger.info("Uninstall done")
