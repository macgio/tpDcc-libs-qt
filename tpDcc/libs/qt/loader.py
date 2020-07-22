#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpDcc.libs.qt
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect
import logging

from Qt.QtWidgets import *
from tpDcc.libs.qt import register
from tpDcc.libs.qt.core import window, dialog
from tpDcc.libs.qt.managers import inputs as inputs_manager, toolsets as toolsets_manager

# =================================================================================

PACKAGE = 'tpDcc.libs.qt'
main = __import__('__main__')

# =================================================================================


def init(dev=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    :param dev: bool, Whether artellapipe is initialized in dev mode or not
    """

    from tpDcc import register as dcc_register

    if dev:
        register.cleanup()

    logger = create_logger(dev=dev)

    register.register_class('logger', logger)

    # NOTE: We register all classes using tpDcc register (not tpDcc.libs.qt one).
    # We do it in this way to access those classes easily
    dcc_register.register_class('Window', window.MainWindow)
    dcc_register.register_class('Dialog', dialog.Dialog)
    dcc_register.register_class('OpenFileDialog', dialog.OpenFileDialog)
    dcc_register.register_class('SaveFileDialog', dialog.SaveFileDialog)
    dcc_register.register_class('SelectFolderDialog', dialog.SelectFolderDialog)
    dcc_register.register_class('NativeDialog', dialog.NativeDialog)
    dcc_register.register_class('InputsMgr', inputs_manager.InputsManagerSingleton)
    dcc_register.register_class('ToolsetsMgr', toolsets_manager.ToolsetsManagerSingleton)

    def init_dcc():
        """
        Checks DCC we are working on an initializes proper variables
        """

        dcc_loaded = False
        if 'cmds' in main.__dict__:
            from tpDcc.dccs.maya import loader as dcc_loader
            dcc_loaded = True
        elif 'MaxPlus' in main.__dict__:
            from tpDcc.dccs.max import loader as dcc_loader
            dcc_loaded = True
        elif 'hou' in main.__dict__:
            from tpDcc.dccs.houdini import loader as dcc_loader
            dcc_loaded = True
        elif 'nuke' in main.__dict__:
            from tpDcc.dccs.nuke import loader as dcc_loader
            dcc_loaded = True
        else:
            try:
                import unreal
                from tpDcc.dccs.unreal import loader as dcc_loader
                dcc_loaded = True
            except Exception as exc:
                pass

        if dcc_loaded:
            dcc_loader.init_ui()
        if not dcc_loaded:
            global Dcc
            from tpDcc.core import dcc
            Dcc = dcc.UnknownDCC
            logger.warning('No DCC found, using abstract one!')

    app = QApplication.instance() or QApplication(sys.argv)

    update_paths()
    register_resources()

    # skip_modules = ['{}.{}'.format(PACKAGE, name) for name in ['loader', 'externals']]
    # importer.init_importer(package=PACKAGE, skip_modules=skip_modules)

    init_dcc()


def get_module_path():
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
                import tpDcc.libs.qt
                mod_dir = tpDcc.libs.qt.__path__[0]
            except Exception:
                return None

    return mod_dir


def update_paths():
    """
    Adds path to system paths at startup
    """

    paths_to_update = [externals_path()]

    for p in paths_to_update:
        if os.path.exists(p) and p not in sys.path:
            sys.path.append(p)


def externals_path():
    """
    Returns the paths where tpPyUtils externals packages are stored
    :return: str
    """

    return os.path.join(get_module_path(), 'externals')


def create_logger(dev=False):
    """
    Returns logger of current module
    """

    logger_directory = os.path.normpath(os.path.join(os.path.expanduser('~'), 'tpDcc', 'logs'))
    if not os.path.isdir(logger_directory):
        os.makedirs(logger_directory)

    logging_config = os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))

    logging.config.fileConfig(logging_config, disable_existing_loggers=False)
    logger = logging.getLogger(PACKAGE.replace('.', '-'))
    if dev:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    return logger


def register_resources():
    """
    Registers tpDcc.libs.qt resources path
    """

    import tpDcc

    resources_manager = tpDcc.ResourcesMgr()
    resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    resources_manager.register_resource(resources_path, key='tpDcc-libs-qt')
