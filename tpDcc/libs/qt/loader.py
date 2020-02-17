#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpQtLib
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect
import logging

main = __import__('__main__')


def init(do_reload=False, dev=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    :param dev: bool, Whether artellapipe is initialized in dev mode or not
    """

    from tpDcc.libs.python import importer
    from tpDcc.libs.qt import register
    from tpDcc.libs.qt.core import resource as resource_utils

    logger = create_logger()

    class tpQtLibResource(resource_utils.Resource, object):
        RESOURCES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')

    class tpQtLib(importer.Importer, object):
        def __init__(self, *args, **kwargs):
            super(tpQtLib, self).__init__(module_name='tpDcc-libs-qt', *args, **kwargs)

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

    def init_dcc(do_reload=False):
        """
        Checks DCC we are working on an initializes proper variables
        """

        if 'cmds' in main.__dict__:
            from tpDcc.dcc.maya import loader
            loader.init_ui(do_reload=do_reload)
        elif 'MaxPlus' in main.__dict__:
            from tpDcc.dcc.max import loader
            loader.init_ui(do_reload=do_reload)
        elif 'hou' in main.__dict__:
            from tpDcc.dcc.houdini import loader
            loader.init_ui(do_reload=do_reload)
        elif 'nuke' in main.__dict__:
            from tpDcc.dcc.nuke import loader
        else:
            global Dcc
            from tpDcc.core import dcc
            Dcc = dcc.UnknownDCC
            logger.warning('No DCC found, using abstract one!')

        from tpDcc.managers import callbackmanager
        callbackmanager.CallbacksManager.initialize()

    tpqtlib_importer = importer.init_importer(importer_class=tpQtLib, do_reload=False)
    tpqtlib_importer.update_paths()

    register.register_class('resource', tpQtLibResource)

    tpqtlib_importer.import_modules(skip_modules=['tpQtLib.externals'])
    tpqtlib_importer.import_packages(only_packages=True, skip_modules=['tpQtLib.externals'],
                                     order=['tpQtLib.core', 'tpQtLib.widgets'])
    if do_reload:
        tpqtlib_importer.reload_all()

    init_dcc(do_reload=do_reload)


def create_logger():
    """
    Returns logger of current module
    """

    logging.config.fileConfig(get_logging_config(), disable_existing_loggers=False)
    logger = logging.getLogger('tpDcc-libs-qt')

    return logger


def create_logger_directory():
    """
    Creates artellapipe logger directory
    """

    tppyutils_logger_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), 'tpQtLib', 'logs'))
    if not os.path.isdir(tppyutils_logger_dir):
        os.makedirs(tppyutils_logger_dir)


def get_logging_config():
    """
    Returns logging configuration file path
    :return: str
    """

    create_logger_directory()

    return os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))
