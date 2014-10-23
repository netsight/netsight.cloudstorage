# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Helper util
"""
from App.config import getConfiguration
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from .exceptions import ConfigurationError


def get_value_from_config(key):
    main_config = getConfiguration()
    product_config = getattr(main_config, 'product_config', None)
    if product_config is None:
        raise ConfigurationError(
            'Unable to locate product-config. Have you added it to buildout?')
    our_config = product_config.get('netsight.cloudstorage', None)
    if our_config is None:
        raise ConfigurationError(
            'Unable to locate netsight.cloudstorage. Have you added it to '
            'buildout?')
    retval = our_config.get(key, None)
    if retval is None:
        raise ConfigurationError('Unable to locate %s. Have you added it to '
                                 'buildout?', key)
    return retval


def get_value_from_registry(key):
    registry = getUtility(IRegistry)
    return registry.get(
        'netsight.cloudstorage.interfaces.ICloudStorageSettings.%s' % key,
        None
    )
