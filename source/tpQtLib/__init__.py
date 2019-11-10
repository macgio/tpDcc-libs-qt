#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpQtLib
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect

from tpPyUtils import importer
from tpQtLib.core import resource as resource_utils
from tpQtLib.resources import res

main = __import__('__main__')

# =================================================================================

logger = None
resource = None

# =================================================================================


class tpQtLibResource(resource_utils.Resource, object):
    RESOURCES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')


class tpQtLib(importer.Importer, object):
    def __init__(self):
        super(tpQtLib, self).__init__(module_name='tpQtLib')

    def get_module_path(self):
        """
        Returns path where tpQtLib module is stored
        :return: str
        """

        try:
            mod_dir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)
        except Exception:
            try:
                mod_dir = os.path.dirname(__file__)
            except Exception:
                try:
                    import tpQtLib
                    mod_dir = tpQtLib.__path__[0]
                except Exception:
                    return None

        return mod_dir

    def update_paths(self):
        """
        Adds path to system paths at startup
        """

        paths_to_update = [self.externals_path()]

        for p in paths_to_update:
            if os.path.exists(p) and p not in sys.path:
                sys.path.append(p)

    def externals_path(self):
        """
        Returns the paths where tpPyUtils externals packages are stored
        :return: str
        """

        return os.path.join(self.get_module_path(), 'externals')


def init(do_reload=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    """

    tpqtlib_importer = importer.init_importer(importer_class=tpQtLib, do_reload=False)
    tpqtlib_importer.update_paths()

    global logger
    global resource
    logger = tpqtlib_importer.logger
    resource = tpQtLibResource

    tpqtlib_importer.import_modules(skip_modules=['tpQtLib.externals'])
    tpqtlib_importer.import_packages(only_packages=True, skip_modules=['tpQtLib.externals'], order=['tpQtLib.core', 'tpQtLib.widgets'])
    if do_reload:
        tpqtlib_importer.reload_all()

    init_dcc(do_reload=do_reload)


def init_dcc(do_reload=False):
    """
    Checks DCC we are working on an initializes proper variables
    """

    if 'cmds' in main.__dict__:
        import tpMayaLib
        tpMayaLib.init_ui(do_reload=do_reload)
    elif 'MaxPlus' in main.__dict__:
        import tpMaxLib
        tpMaxLib.init_ui(do_reload=do_reload)
    elif 'hou' in main.__dict__:
        import tpHoudiniLib
        tpHoudiniLib.init_ui(do_reload=do_reload)
    elif 'nuke' in main.__dict__:
        raise NotImplementedError('Nuke is not a supported DCC yet!')
    else:
        global Dcc
        from tpDccLib.core import dcc
        Dcc = dcc.UnknownDCC
        logger.warning('No DCC found, using abstract one!')

    from tpDccLib.core import callbackmanager
    callbackmanager.CallbacksManager.initialize()


def register_class(cls_name, cls, is_unique=False):
    """
    Registers given class when loading modules
    :param cls_name: str, name of the class we want to register
    :param cls: class, class we want to register
    :param is_unique: bool, Whether if the class should be updated if new class is registered with the same name
    """

    if is_unique:
        if cls_name in sys.modules[__name__].__dict__:
            setattr(sys.modules[__name__], cls_name, getattr(sys.modules[__name__], cls_name))
    else:
        # print('>>> Registering class {} with value {}'.format(cls_name, cls))
        sys.modules[__name__].__dict__[cls_name] = cls
