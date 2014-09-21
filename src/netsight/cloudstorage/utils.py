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
    our_config = product_config['netsight.cloudstorage']
    retval = our_config.get(key, None)
    if retval is None:
        raise ConfigurationError('Unable to locate %s. Have you added it to '
                                 'buildout?', key)
    return retval


def get_value_from_registry(key):
    registry = getUtility(IRegistry)
    return registry.get('my.package.%s' % key, None)
