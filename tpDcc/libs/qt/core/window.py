#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for custom PySide/PyQt windows
"""

from __future__ import print_function, division, absolute_import

import os
import uuid
from collections import defaultdict

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import appdirs

from tpDcc.libs import qt
import tpDcc as tp
from tpDcc import register
from tpDcc.libs.python import path, folder
from tpDcc.libs.qt.core import qtutils, base, animation, color, theme, statusbar, dragger, settings as qt_settings


class WindowContents(QFrame, object):
    """
    Widget that defines the core contents of frameless window
    Can be used to custom CSS for frameless windows contents
    """

    def __init__(self, parent=None):
        super(WindowContents, self).__init__(parent=parent)


class MainWindow(QMainWindow, object):
    """
    Main class to create windows
    """

    closed = Signal()
    dockChanged = Signal(object)
    windowResizedFinished = Signal()
    framelessChanged = Signal(object)
    windowReady = Signal()
    clearedInstance = Signal()

    WindowName = 'New Window'

    STATUS_BAR_WIDGET = statusbar.StatusWidget
    DRAGGER_CLASS = dragger.WindowDragger

    _WINDOW_INSTANCES = dict()

    def __init__(self, parent=None, **kwargs):
        main_window = tp.Dcc.get_main_window()
        if parent is None:
            parent = main_window

        self._setup_resizers()

        window_id = kwargs.get('id', None)
        self._preference_widgets_classes = list()
        self._theme = None
        self._docks = list()
        self._toolbars = dict()
        self._has_main_menu = False
        self._dpi = kwargs.get('dpi', 1.0)
        self._transparent = kwargs.get('transparent', False)
        self._fixed_size = kwargs.get('fixed_size', False)
        self._show_status_bar = kwargs.pop('show_statusbar', True)
        self._init_menubar = kwargs.pop('init_menubar', False)
        self._frameless = kwargs.get('frameless', True)
        self._settings = kwargs.pop('settings', None)
        self._prefs_settings = kwargs.pop('preferences_settings', None)
        auto_load = kwargs.get('auto_load', True)
        self._init_width = kwargs.get('width', 600)
        self._init_height = kwargs.get('height', 800)
        self._dockable = getattr(self, 'WindowDockable', False)
        self._was_docked = False
        self._window_loaded = False
        self._window_closed = False
        self._enable_save_position = True
        self._initial_pos_override = None
        self._signals = defaultdict(list)
        self._force_disable_saving = False
        self._current_docked = None

        if not hasattr(self, 'WindowId'):
            if window_id:
                self.WindowId = window_id
            else:
                self._force_disable_saving = True
                self.WindowId = uuid.uuid4()

        super(MainWindow, self).__init__(parent=parent)

        self.setObjectName(str(self.WindowId))

        self.resize(self._init_width, self._init_height)
        self.center(self._init_width, self._init_height)

        self.load_settings()

        self.ui()
        self.setup_signals()

        if auto_load:
            self.load_theme()

        self.set_frameless(self._frameless)
        if not self._frameless:
            self.set_resizer_active(False)

        # We set the window title after setting window frameless mode
        self.setWindowTitle(kwargs.get('title', self.WindowName))

        MainWindow._WINDOW_INSTANCES[self.WindowId] = {
            'window': self
        }

        self.windowReady.connect(lambda: setattr(self, '_window_loaded', True))

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def widget(self):
        """
        Returns widget
        """

        return self._widget

    @property
    def frameless(self):
        """
        Returns whether this window can be frameless or not
        :return: bool
        """

        return self._frameless

    @frameless.setter
    def frameless(self, flag):
        """
        Sets whether or not this window can be frameless
        :param flag: bool
        """

        self._frameless = flag

    # ============================================================================================================
    # CLASS METHODS
    # ============================================================================================================

    @classmethod
    def instance(cls, parent=None, **kwargs):
        pass

    @classmethod
    def clear_window_instance(cls, window_id):
        """
        Closes the last class instance
        :param window_id:
        :return:
        """

        inst = cls._WINDOW_INSTANCES.pop(window_id, None)
        if inst is not None:
            try:
                inst['window'].clearedInstance.emit()
            except RuntimeError as exc:
                tp.logger.error('Error while clearing window instance: {} | {}'.format(window_id, exc))

        return inst

    @classmethod
    def clear_window_instances(cls):
        """
        Closes every loaded window
        """

        for window_id in tuple(cls._WINDOW_INSTANCES):
            cls.clear_window_instance(window_id)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def menuBar(self):
        return self._menubar

    def showEvent(self, event):
        if self.docked() != self._current_docked:
            self._current_docked = self.docked()
            self.dockChanged.emit(self._current_docked)

        super(MainWindow, self).showEvent(event)

    def closeEvent(self, event):
        self._window_closed = True
        self.save_settings()
        self.unregister_callbacks()
        self.clear_window_instance(self.WindowId)
        self.closed.emit()
        self.setParent(None)
        self.deleteLater()
        return super(MainWindow, self).closeEvent(event)

    def setWindowIcon(self, icon):
        if self.is_frameless():
            self._dragger.set_icon(icon)
        super(MainWindow, self).setWindowIcon(icon)

    def setWindowTitle(self, title):
        if self.is_frameless():
            self._dragger.set_title(title)
        super(MainWindow, self).setWindowTitle(title)

    def addDockWidget(self, area, dock_widget, orientation=Qt.Horizontal, tabify=True):
        """
        Overrides base QMainWindow addDockWidet function
        :param QDockWidgetArea area: area where dock will be added
        :param QDockWidget dock_widget: dock widget to add
        :param Qt.Orientation orientation: orientation fo the dock widget
        :param bool tabify: Whether or not dock widget can be tabbed
        """

        self._docks.append(dock_widget)
        if self._has_main_menu:
            self._view_menu.addAction(dock_widget.toggleViewAction())

        if tabify:
            for current_dock in self._docks:
                if self.dockWidgetArea(current_dock) == area:
                    self.tabifyDockWidget(current_dock, dock_widget)
                    dock_widget.setVisible(True)
                    dock_widget.setFocus()
                    dock_widget.raise_()
                    return

        super(MainWindow, self).addDockWidget(area, dock_widget, orientation)

    def show(self, *args, **kwargs):
        """
        Shows the window and load its position
        :param self:
        :param args:
        :param kwargs:
        """

        super(MainWindow, self).show()
        self.load_window_position()
        self.windowReady.emit()

        return self

    # ============================================================================================================
    # UI
    # ============================================================================================================

    def get_main_layout(self):
        """
        Returns the main layout being used by the window
        :return: QLayout
        """

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        """
        Function used to define UI of the window
        """

        self.setDockNestingEnabled(True)
        self.setDocumentMode(True)
        self.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)

        for r in self._resizers:
            r.setParent(self)

        # Central Widget

        central_widget = QWidget(parent=self)
        self.setCentralWidget(central_widget)
        central_layout = base.VerticalLayout(margins=(0, 0, 0, 0), spacing=0)
        central_widget.setLayout(central_layout)

        # Status Bar
        #
        # self.statusBar().showMessage('')
        # self.statusBar().setSizeGripEnabled(not self._fixed_size)
        # self._status_bar = self.STATUS_BAR_WIDGET(self)
        # self.statusBar().addWidget(self._status_bar)
        # self.statusBar().setVisible(self._show_status_bar)

        # Dragger and MenuBar

        top_widget = QWidget()
        top_layout = base.VerticalLayout(margins=(0, 0, 0, 0), spacing=0)
        top_widget.setLayout(top_layout)
        self._dragger = self.DRAGGER_CLASS(window=self)
        self._button_settings = QPushButton()
        self._button_settings.setIconSize(QSize(25, 25))
        self._button_settings.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_settings.setIcon(tp.ResourcesMgr().icon('winsettings', theme='window'))
        self._button_settings.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_settings.clicked.connect(self._on_show_preferences_dialog)
        self._dragger.buttons_layout.insertWidget(3, self._button_settings)

        self._menubar = QMenuBar()
        if self._init_menubar:
            self._has_main_menu = True
            self._file_menu = self.menuBar().addMenu('File')
            self._view_menu = self.menuBar().addMenu('View')
            self._exit_action = QAction(self)
            self._exit_action.setText('Close')
            self._exit_action.setShortcut('Ctrl + Q')
            self._exit_action.setIcon(tp.ResourcesMgr().resource.icon('close_window'))
            self._exit_action.setToolTip('Close application')
            self._file_menu.addAction(self._exit_action)
            self._exit_action.triggered.connect(self.fade_close)
            for i in self._docks:
                self._view_menu.addAction(i.toggleViewAction())

        top_layout.addWidget(self._dragger)
        top_layout.addWidget(self._menubar)

        self._base_window = QMainWindow(central_widget)
        self._base_window.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        # self._base_window.setWindowFlags(Qt.Widget)
        self._base_window.setAttribute(Qt.WA_TranslucentBackground)
        if qtutils.is_pyside2():
            self._base_window.setWindowFlags(
                self.windowFlags() | Qt.Widget | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        else:
            self._base_window.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self._base_window.setDockOptions(
            QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)
        window_layout = QVBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        self._base_window.setLayout(window_layout)
        self.main_widget = WindowContents()
        self.main_layout = self.get_main_layout()
        self.main_widget.setLayout(self.main_layout)
        self._base_window.setCentralWidget(self.main_widget)

        for r in self._resizers:
            r.windowResizedFinished.connect(self.windowResizedFinished)
        self.set_resize_directions()

        grid_layout = base.GridLayout()
        grid_layout.setHorizontalSpacing(0)
        grid_layout.setVerticalSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(top_widget, 1, 1, 1, 1)
        grid_layout.addWidget(self.main_widget, 2, 1, 1, 1)
        grid_layout.addWidget(self._top_left_resizer, 0, 0, 1, 1)
        grid_layout.addWidget(self._top_resizer, 0, 1, 1, 1)
        grid_layout.addWidget(self._top_right_resizer, 0, 2, 1, 1)
        grid_layout.addWidget(self._left_resizer, 1, 0, 2, 1)
        grid_layout.addWidget(self._right_resizer, 1, 2, 2, 1)
        grid_layout.addWidget(self._bottom_left_resizer, 3, 0, 1, 1)
        grid_layout.addWidget(self._bottom_resizer, 3, 1, 1, 1)
        grid_layout.addWidget(self._bottom_right_resizer, 3, 2, 1, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(2, 1)

        central_layout.addLayout(grid_layout)

        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(qtutils.dpi_scale(15))
        shadow_effect.setColor(QColor(0, 0, 0, 150))
        shadow_effect.setOffset(qtutils.dpi_scale(0))
        self.setGraphicsEffect(shadow_effect)

        for r in self._resizers:
            r.windowResizedFinished.connect(self.windowResizedFinished)

    # ============================================================================================================
    # SIGNALS
    # ============================================================================================================

    def setup_signals(self):
        """
        Override in derived class to setup signals
        This function is called after ui() function is called
        """

        pass

    def signal_connect(self, signal, fn, group=None):
        """
        Adds a new signal for the given group
        :param signal:
        :param fn:
        :param group:
        """

        self._signals[group].append((signal, fn))
        signal.connect(fn)

        return fn

    def signal_disconnect(self, group):
        """
        Disconnects and returns all functions for a current group
        :param group:
        :return: list
        """

        signals = list()
        for (signal, fn) in self._signals.pop(group, list()):
            try:
                signal.disconnect(fn)
            except RuntimeError:
                pass
            else:
                signals.append((signal, fn))

        return signals

    def signal_pause(self, *groups):
        """
        Pauses a certain set of signals during execution
        :param groups: list
        """

        if not groups:
            groups = self._signals

        signal_cache = dict()
        for group in groups:
            signal_cache[group] = self.signal_disconnect(group)

        yield

        for group in groups:
            for signal, fn in signal_cache[group]:
                self.signal_connect(signal, fn, group=group)

    def register_callback(self, callback_type, fn):
        """
        Registers the given callback with the given function
        :param callback_type: tpDccLib.DccCallbacks
        :param fn: Python function to be called when callback is emitted
        """

        if type(callback_type) in [list, tuple]:
            callback_type = callback_type[0]

        if callback_type not in tp.callbacks():
            tp.logger.warning('Callback Type: "{}" is not valid! Aborting callback creation ...'.format(callback_type))
            return

        from tpDcc.managers import callbacks
        return callbacks.CallbacksManager.register(callback_type=callback_type, fn=fn, owner=self)

    def unregister_callbacks(self):
        """
        Unregisters all callbacks registered by this window
        """

        from tpDcc.managers import callbacks
        callbacks.CallbacksManager.unregister_owner_callbacks(owner=self)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def exists(self):
        """
        Returns whether or not this window exists
        :return: bool
        """

        return True

    def is_loaded(self):
        """
        Returns whether or not this window has been already loaded
        :return: bool
        """

        return self._window_loaded and not self.is_closed()

    def is_closed(self):
        """
        Returns whether or not this window has been closed
        """

        return self._window_closed

    def process_events(self):
        """
        Forces Qt application to update GUI between calculations
        """

        QApplication.processEvents()

    def is_frameless(self):
        """
        Returns whether or not frameless functionality for this window is enable or not
        :return: bool
        """

        return self.window().windowFlags() & Qt.FramelessWindowHint == Qt.FramelessWindowHint

    def set_frameless(self, flag):
        """
        Sets whether frameless functionality is enabled or not
        :param flag: bool
        :param show: bool
        """

        window = self.window()

        if flag and not self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            if qtutils.is_pyside2() or qtutils.is_pyqt5():
                window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                window.setWindowFlags(window.windowFlags() ^ Qt.WindowMinMaxButtonsHint)
            else:
                window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                window.setWindowFlags(window.windowFlags() ^ Qt.WindowMinMaxButtonsHint)
            self.set_resizer_active(True)
        elif not flag and self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            if qtutils.is_pyside2() or qtutils.is_pyqt5():
                window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            else:
                self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            self.set_resizer_active(False)

        window.show()

    def center(self, width=None, height=None):
        """
        Centers window to the center of the desktop
        :param width: int
        :param height: int
        """

        geometry = self.frameGeometry()
        if width:
            geometry.setWidth(width)
        if height:
            geometry.setHeight(height)

        desktop = QApplication.desktop()
        pos = desktop.cursor().pos()
        screen = desktop.screenNumber(pos)
        center_point = desktop.screenGeometry(screen).center()
        geometry.moveCenter(center_point)
        self.window().setGeometry(geometry)

    def center_to_parent(self, parent_geometry=None, child_geometry=None):
        """
        Centers current window to its parent
        :param parent_geometry:
        :param child_geometry:
        """

        if parent_geometry is None or child_geometry is None:
            base_window = self
            if parent_geometry is None:
                try:
                    parent_geometry = base_window.parent().frameGeometry()
                except AttributeError:
                    parent_geometry = QApplication.desktop().screenGeometry()
            if child_geometry is None:
                child_geometry = base_window.frameGeometry()

        self.move(
            parent_geometry.x() + (parent_geometry.width() - child_geometry.width()) / 2,
            parent_geometry.y() + (parent_geometry.height() - child_geometry.height()) / 2
        )

    def fade_close(self):
        """
        Closes the window with a fade animation
        """

        animation.fade_window(start=1, end=0, duration=400, object=self, on_finished=self.close)

    def show_ok_message(self, message, msecs=None):
        """
        Set an ok message to be displayed in the status bar
        :param message: str
        :param msecs: int
        """

        self._status_bar.show_ok_message(message=message, msecs=msecs)

    def show_info_message(self, message, msecs=None):
        """
        Set an info message to be displayed in the status bar
        :param message: str
        :param msecs: int
        """

        self._status_bar.show_info_message(message=message, msecs=msecs)

    def show_warning_message(self, message, msecs=None):
        """
       Set a warning message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        self._status_bar.show_warning_message(message=message, msecs=msecs)

    def show_error_message(self, message, msecs=None):
        """
       Set an error message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        self._status_bar.show_error_message(message=message, msecs=msecs)

    # ============================================================================================================
    # RESIZERS
    # ============================================================================================================

    def set_resizer_active(self, flag):
        """
        Sets whether resizers are enable or not
        :param flag: bool
        """

        if flag:
            for r in self._resizers:
                r.show()
        else:
            for r in self._resizers:
                r.hide()

    def set_resize_directions(self):
        """
        Sets the resize directions for the resizer widget of this window
        """

        self._top_resizer.set_resize_direction(ResizeDirection.Top)
        self._bottom_resizer.set_resize_direction(ResizeDirection.Bottom)
        self._right_resizer.set_resize_direction(ResizeDirection.Right)
        self._left_resizer.set_resize_direction(ResizeDirection.Left)
        self._top_left_resizer.set_resize_direction(ResizeDirection.Left | ResizeDirection.Top)
        self._top_right_resizer.set_resize_direction(ResizeDirection.Right | ResizeDirection.Top)
        self._bottom_left_resizer.set_resize_direction(ResizeDirection.Left | ResizeDirection.Bottom)
        self._bottom_right_resizer.set_resize_direction(ResizeDirection.Right | ResizeDirection.Bottom)

    def get_resizers_height(self):
        """
        Returns the total height of the vertical resizers
        :return: float
        """

        resizers = [self._top_resizer, self._bottom_resizer]
        total_height = 0
        for r in resizers:
            if not r.isHidden():
                total_height += r.minimumSize().height()

        return total_height

    def get_resizers_width(self):
        """
        Returns the total widht of the horizontal resizers
        :return: float
        """

        resizers = [self._left_resizer, self._right_resizer]
        total_width = 0
        for r in resizers:
            if not r.isHidden():
                total_width += r.minimumSize().width()

        return total_width

    def _setup_resizers(self):
        """
        Internal function that setup window resizers
        """

        self._top_resizer = VerticalResizer()
        self._bottom_resizer = VerticalResizer()
        self._right_resizer = HorizontalResizer()
        self._left_resizer = HorizontalResizer()
        self._top_left_resizer = CornerResizer()
        self._top_right_resizer = CornerResizer()
        self._bottom_left_resizer = CornerResizer()
        self._bottom_right_resizer = CornerResizer()

        self._resizers = [
            self._top_resizer, self._top_right_resizer, self._right_resizer, self._bottom_right_resizer,
            self._bottom_resizer, self._bottom_left_resizer, self._left_resizer, self._top_left_resizer
        ]

    # ============================================================================================================
    # SETTINGS
    # ============================================================================================================

    def settings(self):
        """
        Returns window settings
        :return: QtSettings
        """

        return self._settings

    def preferences_settings(self):
        """
        Returns window preferences settings
        :return: QtSettings
        """

        return self._prefs_settings

    def set_preferences_settings(self, prefs_settings):
        """
        Sets window preference settings
        :param prefs_settings:
        """

        self._prefs_settings = prefs_settings

    def default_settings(self):
        """
        Returns default settings values
        :return: dict
        """

        # "accentColor": "rgb(0, 175, 240, 255)",

        return {
            "theme": {
                "accentColor": "rgb(80, 80, 80, 255)",
                "backgroundColor": "rgb(45, 45, 45, 255)",
            }
        }

    def set_settings(self, settings):
        """
        Set window settings
        :param settings:
        """

        self._settings = settings

        def_settings = self.default_settings()

        def_geometry = self.settings().get_default_value('geometry', self.objectName().upper())
        geometry = self.settings().getw('geometry', def_geometry)
        if geometry:
            self.restoreGeometry(geometry)

            # Reposition window in the center of the screen if the window is outside of the screen
            geometry = self.geometry()
            x = geometry.x()
            y = geometry.y()
            width = self._init_width or geometry.width()
            height = self._init_height or geometry.height()
            screen_geo = QApplication.desktop().screenGeometry()
            screen_width = screen_geo.width()
            screen_height = screen_geo.height()
            if x <= 0 or y <= 0 or x >= screen_width or y >= screen_height:
                self.center(width, height)

        def_window_state = self.settings().get_default_value('windowState', self.objectName().upper())
        window_state = self.settings().getw('windowState', def_window_state)
        if window_state:
            self.restoreState(window_state)

    def load_settings(self, settings=None):
        """
        Loads window settings from disk
        """

        settings = settings or self.settings()
        if not settings:
            settings = self._settings
            if not settings:
                self._settings = qt_settings.QtSettings(filename=self.get_settings_file(), window=self)
                self._settings.setFallbacksEnabled(False)
                if not self._pref_settings:
                    self._prefs_settings = self._settings
            return self.set_settings(self._settings)

        return self.set_settings(settings)

    def save_settings(self, settings=None):
        """
        Saves window settings
        """

        settings = settings or self.settings()
        if not settings:
            return

        settings.setw('geometry', self.saveGeometry())
        settings.setw('saveState', self.saveState())
        settings.setw('windowState', self.saveState())

        return settings

    def get_settings_path(self):
        """
        Returns path where window settings are stored
        :return: str
        """

        return path.clean_path(os.path.join(appdirs.user_data_dir(), self.WindowId))

    def get_settings_file(self):
        """
        Returns file path of the window settings file
        :return: str
        """

        return path.clean_path(os.path.expandvars(os.path.join(self.get_settings_path(), 'settings.cfg')))

    def register_preference_widget_class(self, widget_class):
        """
        Function used to registere preference widgets
        """

        if not hasattr(widget_class, 'CATEGORY'):
            qt.logger.warning(
                'Impossible to register Category Wigdet Class "{}" because it does not '
                'defines a CATEGORY attribute'.format(widget_class))
            return

        registered_prefs_categories = [pref.CATEGORY for pref in self._preference_widgets_classes]
        if widget_class.CATEGORY in registered_prefs_categories:
            qt.logger.warning(
                'Impossible to register Category Widget Class "{}" because its CATEGORY "{}" its '
                'already registered!'.format(widget_class, widget_class.CATEGORY))
            return

        self._preference_widgets_classes.append(widget_class)

    def enable_save_window_position(self, enable):
        """
        Enables or disables the storage of window position in settings
        :param enable: bool
        """

        self._enable_save_position = enable

    def load_window_position(self):
        pass
        # if self._initial_pos_override is not None:
        #     x, y = self._initial_pos_override()
        #     x, y =

    def save_window_position(self):
        print('Saving window position ...')

    # ============================================================================================================
    # DPI
    # ============================================================================================================

    def dpi(self):
        """
        Return the current dpi for the window
        :return: float
        """

        return float(self._dpi)

    def set_dpi(self, dpi):
        """
        Sets current dpi for the window
        :param dpi: float
        """

        self._dpi = dpi

    # ============================================================================================================
    # THEME
    # ============================================================================================================

    def load_theme(self):
        """
        Loads window theme
        """

        def_settings = self.default_settings()
        def_theme_settings = def_settings.get('theme')
        accent_color = self.settings().getw('theme/accentColor') or def_theme_settings['accentColor']
        background_color = self.settings().getw('theme/backgroundColor') or def_theme_settings['backgroundColor']
        accent_color = 'rgb(%d, %d, %d, %d)' % accent_color.getRgb() if isinstance(
            accent_color, QColor) else accent_color
        background_color = 'rgb(%d, %d, %d, %d)' % background_color.getRgb() if isinstance(
            background_color, QColor) else background_color

        theme_settings = {
            "accentColor": accent_color,
            "backgroundColor": background_color
        }
        self.set_theme_settings(theme_settings)

    def theme(self):
        """
        Returns the current theme
        :return: Theme
        """

        if not self._theme:
            self._theme = theme.Theme()

        return self._theme

    def set_theme(self, theme):
        """
        Sets current window theme
        :param theme: Theme
        """

        self._theme = theme
        self._theme.updated.connect(self.reload_stylesheet)
        self.reload_stylesheet()

    def set_theme_settings(self, settings):
        """
        Sets the theme settings from the given settings
        :param settings: dict
        """

        current_theme = self._settings.get('theme', 'default')
        new_theme = tp.ResourcesMgr().theme(current_theme)
        if not new_theme:
            new_theme = theme.Them()
        new_theme.set_settings(settings)
        self.set_theme(new_theme)

    def reload_stylesheet(self):
        """
        Reloads the stylesheet to the current theme
        """

        current_theme = self.theme()
        current_theme.set_dpi(self.dpi())
        options = current_theme.options()
        stylesheet = current_theme.stylesheet()

        all_widgets = self.main_layout.findChildren(QObject)

        text_color = color.Color.from_string(options["ITEM_TEXT_COLOR"])
        text_selected_color = color.Color.from_string(options["ITEM_TEXT_SELECTED_COLOR"])
        background_color = color.Color.from_string(options["ITEM_BACKGROUND_COLOR"])
        background_hover_color = color.Color.from_string(options["ITEM_BACKGROUND_HOVER_COLOR"])
        background_selected_color = color.Color.from_string(options["ITEM_BACKGROUND_SELECTED_COLOR"])

        self.setStyleSheet(stylesheet)

        for w in all_widgets:
            found = False
            if hasattr(w, 'set_text_color'):
                w.set_text_color(text_color)
                found = True
            if hasattr(w, 'set_text_selected_color'):
                w.set_text_selected_color(text_selected_color)
                found = True
            if hasattr(w, 'set_background_color'):
                w.set_background_color(background_color)
                found = True
            if hasattr(w, 'set_background_hover_color'):
                w.set_background_hover_color(background_hover_color)
                found = True
            if hasattr(w, 'set_background_selected_color'):
                w.set_background_selected_color(background_selected_color)
                found = True

            if found:
                w.update()

    # ============================================================================================================
    # TOOLBAR
    # ============================================================================================================

    def add_toolbar(self, name, area=Qt.TopToolBarArea):
        """
        Adds a new toolbar to the window
        :return:  QToolBar
        """

        new_toolbar = QToolBar(name)
        self._base_window.addToolBar(area, new_toolbar)
        return new_toolbar

    # ============================================================================================================
    # DOCK
    # ============================================================================================================

    def dockable(self, raw=False):
        """
        Returns whether or not the window is dockable
        :param raw: bool, If True, get current state of the window, otherwise get current setting
        :return: bool
        """

        if not raw and self._was_docked is not None:
            return self._was_docked

        return self._dockable

    def set_dockable(self, dockable, override=False):
        """
        Sets whether or not this window is dockable
        :param dockable: bool
        :param override: bool, If the dockable raw value should be set.
            Only should be used if the dock state has changed
        """

        if override:
            self._was_docked = self._dockable = dockable
        else:
            self._was_docked = self._dockable
            self._dockable = dockable
            self.save_window_position()

    def docked(self):
        """
        Returns whether or not this window is currently docked
        :return: bool
        """

        if not self.dockable():
            return False

        raise NotImplementedError('docked function is not implemented!')

    def is_floating(self):
        """
        Returns whether or not this window is floating
        :return: bool
        """

        return tp.Dcc.is_window_floating(self.WindowId)

    def add_dock(self, name, widget=None, pos=Qt.LeftDockWidgetArea, tabify=True):
        """
        Adds a new dockable widget to the window
        :param name: str, name of the dock widget
        :param widget: QWidget, widget to add to the dock
        :param pos: Qt.WidgetArea
        :param tabify: bool, Wheter the new widget should be tabbed to existing docks
        :return: QDockWidget
        """

        if widget:
            dock_name = ''.join([widget.objectName(), 'Dock'])
        else:
            dock_name = name + 'Dock'

        existing_dock = self.find_dock(dock_name)
        if existing_dock:
            existing_dock.raise_()

        dock = DockWidget(title=name, parent=self, floating=False)
        dock.setObjectName(dock_name)
        if widget is not None:
            dock.setWidget(widget)
        self.addDockWidget(pos, dock, tabify=tabify)

        return dock

    def set_active_dock_tab(self, dock_widget):
        """
        Sets the current active dock tab depending on the given dock widget
        :param dock_widget: DockWidget
        """

        tab_bars = self.findChildren(QTabBar)
        for bar in tab_bars:
            count = bar.count()
            for i in range(count):
                data = bar.tabData(i)
                widget = qtutils.to_qt_object(data, qobj=type(dock_widget))
                if widget == dock_widget:
                    bar.setCurrentIndex(i)

    def find_dock(self, dock_name):
        """
        Returns the dock widget based on the object name passed
        :param str dock_name: dock objectName to find
        :return: QDockWidget or None
        """

        for dock in self._docks:
            if dock.objectName() == dock_name:
                return dock

        return None

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _load_ui_from_file(self, ui_file):
        """
        Internal function that loads given UI file
        :param ui_file: str
        :return: QWidget or None
        """

        if not os.path.isfile(ui_file):
            return None

        loaded_ui = qtutils.load_ui(ui_file=ui_file)

        return loaded_ui

    def _settings_validator(self, **kwargs):
        """
        Validator used for the settings dialog
        :param kwargs: dict
        """

        fields = list()

        clr = kwargs.get("accentColor")
        if clr and self.theme().accent_color().to_string() != clr:
            self.theme().set_accent_color(clr)

        clr = kwargs.get("backgroundColor")
        if clr and self.theme().background_color().to_string() != clr:
            self.theme().set_background_color(clr)

        return fields

    def _settings_accepted(self, **kwargs):
        """
        Function that is called when window settings dialog are accepted
        :param kwargs: dict
        """

        if not self.settings():
            return

        theme_name = self.theme().name()
        accent_color = kwargs.get('accentColor', self.theme().accent_color().to_string())
        background_color = kwargs.get('backgroundColor', self.theme().background_color().to_string())
        if theme_name:
            self.settings().setw('theme/name', theme_name)
        self.settings().setw('theme/accentColor', accent_color)
        self.settings().setw('theme/backgroundColor', background_color)
        self.settings().sync()

        self.load_theme()

    def _setup_theme_preferences(self):

        from tpDcc.libs.qt.core import preferences
        from tpDcc.libs.qt.widgets import formwidget

        accent_color = self.theme().accent_color().to_string()
        background_color = self.theme().background_color().to_string()
        settings_validator = self._settings_validator
        settings_accepted = self._settings_accepted

        class ThemeCategoryWidget(preferences.CategoryWidgetBase, object):

            CATEGORY = 'Theme'

            def __init__(self, parent=None):
                super(ThemeCategoryWidget, self).__init__(parent=parent)

                self.main_layout = QVBoxLayout()
                self.main_layout.setContentsMargins(2, 2, 2, 2)
                self.main_layout.setSpacing(2)
                self.setLayout(self.main_layout)

                form = {
                    "title": "Theme",
                    "description": "Theme Colors",
                    "layout": "vertical",
                    "schema": [
                        {
                            "name": "accentColor",
                            "type": "color",
                            "value": accent_color,
                            "colors": [
                                "rgb(230, 80, 80, 255)",
                                "rgb(230, 125, 100, 255)",
                                "rgb(230, 120, 40)",
                                "rgb(240, 180, 0, 255)",
                                "rgb(80, 200, 140, 255)",
                                "rgb(50, 180, 240, 255)",
                                "rgb(110, 110, 240, 255)",
                            ]
                        },
                        {
                            "name": "backgroundColor",
                            "type": "color",
                            "value": background_color,
                            "colors": [
                                "rgb(40, 40, 40)",
                                "rgb(68, 68, 68)",
                                "rgb(80, 60, 80)",
                                "rgb(85, 60, 60)",
                                "rgb(60, 75, 75)",
                                "rgb(60, 64, 79)",
                                "rgb(245, 245, 255)",
                            ]
                        },
                    ],
                    "validator": settings_validator,
                    "accepted": settings_accepted
                }

                self._dlg = formwidget.FormDialog(parent=parent, form=form)
                self._dlg.setMinimumWidth(300)
                self._dlg.setMinimumHeight(300)
                self._dlg.setMaximumWidth(400)
                self._dlg.setMaximumHeight(400)
                self._dlg.accept_button().setText('Save')
                self._dlg.accept_button().setVisible(False)
                self._dlg.reject_button().setVisible(False)
                self._dlg.show()
                self.main_layout.addWidget(self._dlg)

        theme_prefs_widget = ThemeCategoryWidget(parent=self._preferences_window)

        return theme_prefs_widget

    def _parent_override(self):
        """
        Internal function that overrides parent functionality to make sure that proper parent attributes are used
        in dockable windows
        """

        # Make sure this function is inherited
        return super(MainWindow, self)

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_show_preferences_dialog(self):

        from tpDcc.libs.qt.widgets import lightbox
        from tpDcc.libs.qt.core import preferences
        self._lightbox = lightbox.Lightbox(self)
        self._lightbox.closed.connect(self._on_close_lightbox)
        self._preferences_window = preferences.PreferencesWidget(settings=self.preferences_settings())
        self._preferences_window.setFixedHeight(500)
        self._preferences_window.closed.connect(self._on_close_preferences_window)
        self._lightbox.set_widget(self._preferences_window)
        for pref_widget in self._preference_widgets_classes:
            pref_widget = pref_widget()
            self._preferences_window.add_category(pref_widget.CATEGORY, pref_widget)
        self._theme_widget = self._setup_theme_preferences()
        self._preferences_window.add_category(self._theme_widget.CATEGORY, self._theme_widget)
        self._lightbox.show()

    def _on_close_preferences_window(self, save_widget=False):
        self._on_close_lightbox(save_widget)
        self._lightbox.blockSignals(True)
        self._lightbox.close()
        self._lightbox.blockSignals(False)

    def _on_close_lightbox(self, save_widgets=False):
        if not save_widgets:
            self._settings_accepted(**self._theme_widget._dlg._form_widget.default_values())
        else:
            self._settings_accepted(**self._theme_widget._dlg._form_widget.values())


class DetachedWindow(QMainWindow):
    """
    Class that incorporates functionality to create detached windows
    """

    windowClosed = Signal(object)

    class DetachPanel(QWidget, object):
        widgetVisible = Signal(QWidget, bool)

        def __init__(self, parent=None):
            super(DetachedWindow.DetachPanel, self).__init__(parent=parent)

            self.main_layout = QVBoxLayout()
            self.setLayout(self.main_layout)

        def set_widget_visible(self, widget, visible):
            self.setVisible(visible)
            self.widgetVisible.emit(widget, visible)

        def set_widget(self, widget):
            qtutils.clear_layout(self.main_layout)
            self.main_layout.addWidget(widget)
            widget.show()

    class SettingGroup(object):
        global_group = ''

        def __init__(self, name):
            self.name = name
            self.settings = QSettings()

        def __enter__(self):
            if self.global_group:
                self.settings.beginGroup(self.global_group)
            self.settings.beginGroup(self.name)
            return self.settings

        def __exit__(self, *args):
            if self.global_group:
                self.settings.endGroup()
            self.settings.endGroup()
            self.settings.sync()

        @staticmethod
        def load_basic_window_settings(window, window_settings):
            window.restoreGeometry(window_settings.value('geometry', QByteArray()))
            window.restoreState(window_settings.value('windowstate', QByteArray()))
            try:
                window.split_state = window_settings.value('splitstate', '')
            except TypeError:
                window.split_state = ''

    def __init__(self, title, parent):
        self.tab_idx = -1
        super(DetachedWindow, self).__init__(parent=parent)

        self.main_widget = self.DetachPanel()
        self.setCentralWidget(self.main_widget)

        self.setWindowTitle(title)
        self.setWindowModality(Qt.NonModal)
        self.sgroup = self.SettingGroup(title)
        with self.sgroup as config:
            self.SettingGroup.load_basic_window_settings(self, config)

        self.statusBar().hide()

    def closeEvent(self, event):
        with self.sgroup as config:
            config.setValue('detached', False)
        self.windowClosed.emit(self)
        self.deleteLater()

    def moveEvent(self, event):
        super(DetachedWindow, self).moveEvent(event)
        self.save_settings()

    def resizeEvent(self, event):
        super(DetachedWindow, self).resizeEvent(event)
        self.save_settings()

    def set_widget_visible(self, widget, visible):
        self.setVisible(visible)

    def set_widget(self, widget):
        self.main_widget.set_widget(widget=widget)

    def save_settings(self, detached=True):
        with self.sgroup as config:
            config.setValue('detached', detached)
            config.setValue('geometry', self.saveGeometry())
            config.setValue('windowstate', self.saveState())


class DockWindow(QMainWindow, object):
    """
    Class that with dock functionality. It's not intended to use as main window (use MainWindow for that) but for
    being inserted inside a window and have a widget with dock functionality in the main layout of that window
    """

    class DockWidget(QDockWidget, object):
        def __init__(self, name, parent=None, window=None):
            super(DockWindow.DockWidget, self).__init__(name, parent)

            self.setWidget(window)

        # region Override Functions
        def setWidget(self, widget):
            """
            Sets the window instance of the dockable main window
            """

            super(DockWindow.DockWidget, self).setWidget(widget)

            if widget and issubclass(widget.__class__, MainWindow):
                # self.setFloating(True)
                self.setWindowTitle(widget.windowTitle())
                self.visibilityChanged.connect(self._visibility_changed)

                widget.setWindowFlags(Qt.Widget)
                widget.setParent(self)
                widget.windowTitleChanged.connect(self._window_title_changed)

        # endregion

        # region Private Functions
        def _visibility_changed(self, state):
            """
            Process QDockWidget's visibilityChanged signal
            """

            # TODO: Implement export widget properties functionality
            # widget = self.widget()
            # if widget:
            #     widget.export_settings()

        def _window_title_changed(self, title):
            """
            Process BaseWindow's windowTitleChanged signal
            :param title: str, new title
            """

            self.setWindowTitle(title)

    _last_instance = None

    def __init__(self, name='BaseWindow', title='DockWindow', use_scrollbar=False, parent=None):
        self.main_layout = self.get_main_layout()
        self.__class__._last_instance = self
        super(DockWindow, self).__init__(parent)

        self.docks = list()
        self.connect_tab_change = True
        self.use_scrollbar = use_scrollbar

        self.setObjectName(name)
        self.setWindowTitle(title)
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().hide()

        self.ui()

        self.tab_change_hide_show = True

    def keyPressEvent(self, event):
        return

    def get_main_layout(self):
        """
        Function that generates the main layout used by the widget
        Override if necessary on new widgets
        :return: QLayout
        """

        return QVBoxLayout()

    def ui(self):
        """
        Function that sets up the ui of the widget
        Override it on new widgets (but always call super)
        """

        main_widget = QWidget()
        if self.use_scrollbar:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(main_widget)
            self._scroll_widget = scroll
            main_widget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
            self.setCentralWidget(scroll)
        else:
            self.setCentralWidget(main_widget)

        main_widget.setLayout(self.main_layout)
        self.main_widget = main_widget

        self.main_layout.expandingDirections()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ==========================================================================================

        # TODO: Check if we should put this on constructor
        # self.main_widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        # self.centralWidget().hide()

        self.setTabPosition(Qt.TopDockWidgetArea, QTabWidget.West)
        self.setDockOptions(self.AnimatedDocks | self.AllowTabbedDocks | self.AllowNestedDocks)

    def set_active_dock_tab(self, dock_widget):
        """
        Sets the current active dock tab depending on the given dock widget
        :param dock_widget: DockWidget
        """

        tab_bars = self.findChildren(QTabBar)
        for bar in tab_bars:
            count = bar.count()
            for i in range(count):
                data = bar.tabData(i)
                widget = qtutils.to_qt_object(data, qobj=type(dock_widget))
                if widget == dock_widget:
                    bar.setCurrentIndex(i)

    def add_dock(self, widget, name, pos=Qt.TopDockWidgetArea, tabify=True):
        docks = self._get_dock_widgets()
        for dock in docks:
            if dock.windowTitle() == name:
                dock.deleteLater()
                dock.close()
        dock_widget = self.DockWidget(name=name, parent=self)
        # dock_widget.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum))
        dock_widget.setAllowedAreas(pos)
        dock_widget.setWidget(widget)

        self.addDockWidget(pos, dock_widget)

        if docks and tabify:
            self.tabifyDockWidget(docks[-1], dock_widget)

        dock_widget.show()
        dock_widget.raise_()

        tab_bar = self._get_tab_bar()
        if tab_bar:
            if self.connect_tab_change:
                tab_bar.currentChanged.connect(self._on_tab_changed)
                self.connect_tab_change = False

        return dock_widget

    def _get_tab_bar(self):
        children = self.children()
        for child in children:
            if isinstance(child, QTabBar):
                return child

    def _get_dock_widgets(self):
        found = list()
        for child in self.children():
            if isinstance(child, QDockWidget):
                found.append(child)

        return found

    def _on_tab_changed(self, index):
        if not self.tab_change_hide_show:
            return

        docks = self._get_dock_widgets()

        docks[index].hide()
        docks[index].show()


class SubWindow(MainWindow, object):
    """
    Class to create sub windows
    """

    def __init__(self, parent=None, **kwargs):
        super(SubWindow, self).__init__(parent=parent, show_dragger=False, **kwargs)


class DirectoryWindow(MainWindow, object):
    """
    Window that stores variable to store current working directory
    """

    def __init__(self, parent=None, **kwargs):
        self.directory = None
        super(DirectoryWindow, self).__init__(parent=parent, show_dragger=False, **kwargs)

    def set_directory(self, directory):
        """
        Sets the directory of the window. If the given folder does not exists, it will created automatically
        :param directory: str, new directory of the window
        """

        self.directory = directory

        if not path.is_dir(directory=directory):
            folder.create_folder(name=None, directory=directory)


class ResizeDirection:
    Left = 1
    Top = 2
    Right = 4
    Bottom = 8


class WindowResizer(QFrame, object):
    windowResized = Signal()
    windowResizedStarted = Signal()
    windowResizedFinished = Signal()

    def __init__(self, parent):
        super(WindowResizer, self).__init__(parent)

        self._init()

        self._direction = 0
        self._widget_mouse_pos = None
        self._widget_geometry = None
        self._frameless = None

        self.setStyleSheet('background: transparent;')

        self.windowResizedStarted.connect(self._on_window_resize_started)

    def paintEvent(self, event):
        """
        Overrides base QFrame paintEvent function
        Override to make mouse events work in transparent widgets
        :param event: QPaintEvent
        """

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 0, 0, 1))
        painter.end()

    def leaveEvent(self, event):
        """
        Overrides base QFrame leaveEvent function
        :param event: QEvent
        """

        QApplication.restoreOverrideCursor()

    def mousePressEvent(self, event):
        """
        Overrides base QFrame mousePressEvent function
        :param event: QEvent
        """

        self.windowResizedStarted.emit()

    def mouseMoveEvent(self, event):
        """
        Overrides base QFrame mouseMoveEvent function
        :param event: QEvent
        """

        self.windowResized.emit()

    def mouseReleaseEvent(self, event):
        """
        Overrides base QFrame mouseReleaseEvent function
        :param event: QEvent
        """

        self.windowResizedFinished.emit()

    def setParent(self, parent):
        """
        Overrides base QFrame setParent function
        :param event: QWidget
        """

        self._frameless = parent
        super(WindowResizer, self).setParent(parent)

    def set_resize_direction(self, direction):
        """
        Sets the resize direction

        .. code-block:: python

            setResizeDirection(ResizeDirection.Left | ResizeDireciton.Top)

        :param direction: ResizeDirection
        :return: ResizeDirection
        :rtype: int
        """
        self._direction = direction

    def _init(self):
        """
        Internal function that initializes reisizer
        Override in custom resizers
        """

        self.windowResized.connect(self._on_window_resized)

    def _on_window_resized(self):
        """
        Internal function that resizes the frame based on the mouse position and the current direction
        """

        pos = QCursor.pos()
        new_geo = self.window().frameGeometry()

        min_width = self.window().minimumSize().width()
        min_height = self.window().minimumSize().height()

        if self._direction & ResizeDirection.Left == ResizeDirection.Left:
            left = new_geo.left()
            new_geo.setLeft(pos.x() - self._widget_mouse_pos.x())
            if new_geo.width() <= min_width:
                new_geo.setLeft(left)
        if self._direction & ResizeDirection.Top == ResizeDirection.Top:
            top = new_geo.top()
            new_geo.setTop(pos.y() - self._widget_mouse_pos.y())
            if new_geo.height() <= min_height:
                new_geo.setTop(top)
        if self._direction & ResizeDirection.Right == ResizeDirection.Right:
            new_geo.setRight(pos.x() + (self.minimumSize().width() - self._widget_mouse_pos.x()))
        if self._direction & ResizeDirection.Bottom == ResizeDirection.Bottom:
            new_geo.setBottom(pos.y() + (self.minimumSize().height() - self._widget_mouse_pos.y()))

        x = new_geo.x()
        y = new_geo.y()
        w = max(new_geo.width(), min_width)
        h = max(new_geo.height(), min_height)

        self.window().setGeometry(x, y, w, h)

    def _on_window_resize_started(self):
        self._widget_mouse_pos = self.mapFromGlobal(QCursor.pos())
        self._widget_geometry = self.window().frameGeometry()


class CornerResizer(WindowResizer, object):
    """
    Resizer for window corners
    """

    def __init__(self, parent=None):
        super(CornerResizer, self).__init__(parent)

    def enterEvent(self, event):
        """
        Overrides base QFrame enterEvenet function
        :param event: QEvent
        """

        if self._direction == ResizeDirection.Left | ResizeDirection.Top or \
                self._direction == ResizeDirection.Right | ResizeDirection.Bottom:
            QApplication.setOverrideCursor(Qt.SizeFDiagCursor)
        elif self._direction == ResizeDirection.Right | ResizeDirection.Top or \
                self._direction == ResizeDirection.Left | ResizeDirection.Bottom:
            QApplication.setOverrideCursor(Qt.SizeBDiagCursor)

    def _init(self):
        """
        Overrides base WindowResizer _int function
        """

        super(CornerResizer, self)._init()

        self.setFixedSize(qtutils.size_by_dpi(QSize(10, 10)))


class VerticalResizer(WindowResizer, object):
    """
    Resize for top and bottom sides of the window
    """

    def __init__(self, parent=None):
        super(VerticalResizer, self).__init__(parent)

    def enterEvent(self, event):
        """
        Overrides base QFrame enterEvenet function
        :param event: QEvent
        """

        QApplication.setOverrideCursor(Qt.SizeVerCursor)

    def _init(self):
        """
        Overrides base WindowResizer _int function
        """

        super(VerticalResizer, self)._init()
        self.setFixedHeight(qtutils.dpi_scale(8))


class HorizontalResizer(WindowResizer, object):
    """
    Resize for left and right sides of the window
    """

    def __init__(self, parent=None):
        super(HorizontalResizer, self).__init__(parent)

    def enterEvent(self, event):
        """
        Overrides base QFrame enterEvenet function
        :param event: QEvent
        """

        QApplication.setOverrideCursor(Qt.SizeHorCursor)

    def _init(self):
        """
        Overrides base WindowResizer _int function
        """

        super(HorizontalResizer, self)._init()
        self.setFixedWidth(qtutils.dpi_scale(8))


class DockWidget(QDockWidget, object):
    """
    Base docked widget
    """

    def __init__(self, title, parent=None, floating=False):
        super(DockWidget, self).__init__(title, parent)

        self.setFloating(floating)
        self.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)


class DockWindowContainer(DockWidget, object):
    """
    Docked Widget used to dock windows inside other windows
    """

    def __init__(self, title):
        super(DockWindowContainer, self).__init__(title)

    def closeEvent(self, event):
        if self.widget():
            self.widget().close()
        super(DockWindowContainer, self).closeEvent(event)


register.register_class('Window', MainWindow)
