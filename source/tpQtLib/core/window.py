#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for custom PySide/PyQt windows
"""

from __future__ import print_function, division, absolute_import

import os

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpQtLib
import tpDccLib as tp
from tpPyUtils import path, folder
from tpQtLib.core import qtutils, settings, animation, color, theme, statusbar, dragger


class MainWindow(QMainWindow, object):
    """
    Main class to create windows
    """

    windowClosed = Signal()
    dockChanged = Signal(object)
    windowResizedFinished = Signal()
    framelessChanged = Signal(object)

    STATUS_BAR_WIDGET = statusbar.StatusWidget
    DRAGGER_CLASS = dragger.WindowDragger

    class DockWidget(QDockWidget, object):
        """
        Baes docked widget
        """

        def __init__(self, title, parent=None, floating=False):
            super(MainWindow.DockWidget, self).__init__(title, parent)

            self.setFloating(floating)
            self.setFeatures(
                QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)

    class DockWindowContainer(DockWidget, object):
        """
        Docked Widget used to dock windows inside other windows
        """

        def __init__(self, title):
            super(MainWindow.DockWindowContainer, self).__init__(title)

        def closeEvent(self, event):
            if self.widget():
                self.widget().close()
            super(MainWindow.DockWindowContainer, self).closeEvent(event)

    def __init__(self, parent=None, **kwargs):

        name = kwargs.get('name', '')
        title = kwargs.get('title', '')
        name = name or title or self.__class__.__name__

        # Remove previous windows
        main_window = tp.Dcc.get_main_window()
        if main_window:
            wins = tp.Dcc.get_main_window().findChildren(QWidget, name) or list()
            for w in wins:
                w.close()
                w.deleteLater()
        if parent is None:
            parent = main_window

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

        super(MainWindow, self).__init__(parent=parent)

        self._theme = None
        self._docks = list()
        self._toolbars = dict()
        self._has_main_menu = False
        self._dpi = kwargs.get('dpi', 1.0)
        self._transparent = kwargs.get('transparent', False)
        self._frameless = kwargs.get('frameless', True)
        self._show_dragger = kwargs.get('show_dragger', self._frameless)
        self._fixed_size = kwargs.get('fixed_size', False)
        self._show_status_bar = kwargs.pop('show_statusbar', True)
        self._init_menubar = kwargs.pop('init_menubar', False)
        win_settings = kwargs.pop('settings', None)
        auto_load = kwargs.get('auto_load', True)
        show_on_initialize = kwargs.get('show_on_initialize', False)
        width = kwargs.get('width', 600)
        height = kwargs.get('height', 800)

        for r in self._resizers:
            r.setParent(self)

        self.setObjectName(name)

        if self._transparent or self._frameless and self._show_dragger:
            self.setAttribute(Qt.WA_TranslucentBackground)

        if self._frameless:
            if qtutils.is_pyside2():
                self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            else:
                self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        if win_settings:
            self._settings = win_settings
        else:
            self._settings = settings.QtSettings(filename=self.get_settings_file(), window=self)
            self._settings.setFallbacksEnabled(False)

        if auto_load:
            self.load()

        self.ui()
        self.setup_signals()

        self.setWindowTitle(title)
        self.resize(width, height)

        if auto_load:
            self.load_theme()

        if show_on_initialize:
            self.center(width, height)
            self.show()

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def widget(self):
        """
        Returns widget
        """

        return self._widget

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def menuBar(self):
        return self._menubar

    def closeEvent(self, event):
        self.save_settings()
        self.unregister_callbacks()
        self.windowClosed.emit()
        self.setParent(None)
        self.deleteLater()

    def setWindowIcon(self, icon):
        if self._frameless:
            self._dragger.set_icon(icon)
        super(MainWindow, self).setWindowIcon(icon)

    def setWindowTitle(self, title):
        if self._frameless:
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
                    return

        super(MainWindow, self).addDockWidget(area, dock_widget, orientation)

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

        # self.setDockNestingEnabled(True)
        # self.setDocumentMode(True)
        # self.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        # self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)

        self._base_layout = QVBoxLayout()
        self._base_layout.setContentsMargins(0, 0, 0, 0)
        self._base_layout.setSpacing(0)
        self._base_layout.setAlignment(Qt.AlignTop)

        base_widget = QFrame()
        base_widget.setObjectName('mainFrame')
        base_widget.setFrameStyle(QFrame.NoFrame)
        base_widget.setFrameShadow(QFrame.Plain)
        base_widget.setStyleSheet("""
           QFrame#mainFrame
           {
           background-color: rgb(35, 35, 35);
           border-radius: 25px;
           }""")
        base_widget.setLayout(self._base_layout)
        self.setCentralWidget(base_widget)

        self._dragger = self.DRAGGER_CLASS(parent=self)
        if not self._show_dragger:
            self._dragger.setVisible(False)
        else:
            self._dragger.setVisible(self._frameless)
        self._base_layout.addWidget(self._dragger)

        if self._settings:
            self._button_settings = QPushButton()
            self._button_settings.setIconSize(QSize(25, 25))
            self._button_settings.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
            self._button_settings.setIcon(tpQtLib.resource.icon('winsettings', theme='window'))
            self._button_settings.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
            self._button_settings.clicked.connect(self._on_show_settings_dialog)
            self._dragger.buttons_layout.insertWidget(3, self._button_settings)

        self.statusBar().showMessage('')
        self.statusBar().setSizeGripEnabled(not self._fixed_size)
        self._status_bar = self.STATUS_BAR_WIDGET(self)
        self.statusBar().addWidget(self._status_bar)
        self.statusBar().setVisible(self._show_status_bar)

        self._menubar = QMenuBar()
        self._base_layout.addWidget(self._menubar)
        if self._init_menubar:
            self._has_main_menu = True
            self._file_menu = self.menuBar().addMenu('File')
            self._view_menu = self.menuBar().addMenu('View')
            self._exit_action = QAction(self)
            self._exit_action.setText('Close')
            self._exit_action.setShortcut('Ctrl + Q')
            self._exit_action.setIcon(tpQtLib.resource.icon('close_window'))
            self._exit_action.setToolTip('Close application')
            self._file_menu.addAction(self._exit_action)
            self._exit_action.triggered.connect(self.fade_close)
            for i in self._docks:
                self._view_menu.addAction(i.toggleViewAction())

        self._base_window = QMainWindow(base_widget)
        self._base_window.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self._base_window.setWindowFlags(Qt.Widget)
        self._base_window.setDockOptions(
            QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)
        self._base_layout.addWidget(self._base_window)
        window_layout = QVBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        self._base_window.setLayout(window_layout)

        self.main_layout = self.get_main_layout()

        # TODO: Add functionality to scrollbar
        self.main_widget = QWidget()
        self._base_window.setCentralWidget(self.main_widget)

        # self.main_widget = QScrollArea(self)
        # self.main_widget.setWidgetResizable(True)
        # self.main_widget.setFocusPolicy(Qt.NoFocus)
        # self.main_widget.setMinimumHeight(1)
        # self.main_widget.setLayout(self.main_layout)
        # self._base_window.setCentralWidget(self.main_widget)

        self.main_widget.setLayout(self.main_layout)

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

        from tpDccLib.core import callbackmanager
        return callbackmanager.CallbacksManager.register(callback_type=callback_type, fn=fn, owner=self)

    def unregister_callbacks(self):
        """
        Unregisters all callbacks registered by this window
        """

        from tpDccLib.core import callbackmanager
        callbackmanager.CallbacksManager.unregister_owner_callbacks(owner=self)

    # ============================================================================================================
    # SETTINGS
    # ============================================================================================================

    def load(self):
        self.load_settings()

    def settings(self):
        """
        Returns window settings
        :return: QtSettings
        """

        return self._settings

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
            width = geometry.width()
            height = geometry.height()
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

        self.set_settings(settings)

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

        return os.path.join(os.getenv('APPDATA'), self.objectName())

    def get_settings_file(self):
        """
        Returns file path of the window settings file
        :return: str
        """

        return os.path.expandvars(os.path.join(self.get_settings_path(), 'settings.cfg'))

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
        def_settings = self.default_settings()
        def_theme_settings = def_settings.get('theme')
        theme_settings = {
            "accentColor": self.settings().getw('theme/accentColor') or def_theme_settings['accentColor'],
            "backgroundColor": self.settings().getw('theme/backgroundColor') or def_theme_settings['backgroundColor']
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

        new_theme = theme.Theme()
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

        # self._toolbar = toolbar.ToolBar()
        new_toolbar = QToolBar(name)
        self._base_window.addToolBar(area, new_toolbar)
        return new_toolbar

    # ============================================================================================================
    # DOCK
    # ============================================================================================================

    def dock(self):
        """
        Docks window into main DCC window
        """

        self._dock_widget = MainWindow.DockWindowContainer(self.windowTitle())
        self._dock_widget.setWidget(self)
        tp.Dcc.get_main_window().addDockWidget(Qt.LeftDockWidgetArea, self._dock_widget)
        self.main_title.setVisible(False)

    def add_dock(self, name, widget=None, pos=Qt.LeftDockWidgetArea, tabify=True):
        """
        Adds a new dockable widet to the window
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

        dock = MainWindow.DockWidget(title=name, parent=self, floating=False)
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
    # BASE
    # ============================================================================================================

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
    # PRIVATE
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
        accent_color = self.theme().accent_color().to_string()
        background_color = self.theme().background_color().to_string()
        if theme_name:
            self.settings().setw('theme/name', theme_name)
        self.settings().setw('theme/accentColor', accent_color)
        self.settings().setw('theme/backgroundColor', background_color)

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_show_settings_dialog(self):

        from tpQtLib.widgets import formwidget, lightbox

        accent_color = self.theme().accent_color().to_string()
        background_color = self.theme().background_color().to_string()

        form = {
            "title": "Settings",
            "description": "Your local settings",
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
            "validator": self._settings_validator,
            "accepted": self._settings_accepted
        }

        widget = formwidget.FormDialog(form=form)
        widget.setMinimumWidth(300)
        widget.setMinimumHeight(300)
        widget.setMaximumWidth(400)
        widget.setMaximumHeight(400)
        widget.accept_button().setText('Save')

        self._lightbox = lightbox.Lightbox(self)
        self._lightbox.set_widget(widget)
        self._lightbox.show()


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
            window.restoreGeometry(window_settings.value('geometry', ''))
            window.restoreState(window_settings.value('windowstate', ''))
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

    def __init__(self, name='BaseWindow', title='DockWindow',  use_scrollbar=False, parent=None):
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
        self.setFixedHeight(qtutils.dpi_scale(8))


tpQtLib.register_class('Window', MainWindow)
