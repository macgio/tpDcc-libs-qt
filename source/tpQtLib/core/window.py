#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Collapsible accordion widget similar to Maya Attribute Editor
"""

from __future__ import print_function, division, absolute_import

import os

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *

import tpDccLib as tp
from tpPyUtils import path, folder
from tpQtLib.core import qtutils, settings


class MainWindow(QMainWindow, object):
    """
    Base class to create windows
    """

    windowClosed = Signal()

    DOCK_CONTROL_NAME = 'my_workspcae_control'
    DOCK_LABEL_NAME = 'my workspcae control'

    class DockWindowContainer(QDockWidget, object):
        """
        Docked Widget used to dock windows inside other windows
        """

        def __init__(self, title):
            super(MainWindow.DockWindowContainer, self).__init__(title)

        def closeEvent(self, event):
            if self.widget():
                self.widget().close()
            super(MainWindow.DockWindowContainer, self).closeEvent(event)

    def __init__(self, name, parent=None, **kwargs):

        # Remove previous windows
        main_window = tp.Dcc.get_main_window()
        if main_window:
            wins = tp.Dcc.get_main_window().findChildren(QWidget, name) or []
            for w in wins:
                w.close()
                w.deleteLater()

        if parent is None:
            parent = tp.Dcc.get_main_window()
        super(MainWindow, self).__init__(parent=parent)

        self.setProperty('saveWindowPref', True)
        self.setObjectName(name)
        # self.setWindowFlags(Qt.Window)
        self.setWindowTitle(kwargs.pop('title', 'Maya Window'))

        self._theme = None
        self._kwargs = dict()

        has_settings = kwargs.pop('has_settings', True)
        win_settings = kwargs.pop('settings', None)
        if win_settings:
            self.settings = win_settings
        else:
            if has_settings:
                self.settings = settings.QtSettings(filename=self.get_settings_file(), window=self)
                self.settings.setFallbacksEnabled(False)
            else:
                self.settings = None

        self.ui()
        self.setup_signals()

    def closeEvent(self, event):
        self.windowClosed.emit()
        self.deleteLater()

    def set_kwargs(self, kwargs):
        """
        Set the keyword arguments used to open the library window
        :param kwargs: dict
        """

        self._kwargs.update(kwargs)

    def add_toolbar(self, name, area=Qt.TopToolBarArea):
        """
        Adds a new toolbar to the window
        :return:  QToolBar
        """

        # self._toolbar = toolbar.ToolBar()
        new_toolbar = QToolBar(name)
        self._base_window.addToolBar(area, new_toolbar)
        return new_toolbar

    def get_settings_path(self):
        """
        Returns path where window settings are stored
        :return: str
        """

        return os.path.join(os.getenv('APPDATA'), 'tpRigToolkit', self.objectName())

    def get_settings_file(self):
        """
        Returns file path of the window settings file
        :return: str
        """

        return os.path.expandvars(os.path.join(self.get_settings_path(), 'settings.cfg'))

    def get_main_layout(self):
        """
        Returns the main layout being used by the window
        :return: QLayout
        """

        return QVBoxLayout()

    def ui(self):
        """
        Function used to define UI of the window
        """

        from tpQtLib.widgets import statusbar

        self._base_layout = QVBoxLayout()
        self._base_layout.setContentsMargins(0, 0, 0, 0)
        self._base_layout.setSpacing(0)
        self._base_layout.setAlignment(Qt.AlignTop)
        base_widget = QFrame()
        base_widget.setFrameStyle(QFrame.StyledPanel)
        base_widget.setLayout(self._base_layout)
        self.setCentralWidget(base_widget)

        self.statusBar().showMessage('')
        # self.statusBar().setSizeGripEnabled(not self._fixed_size)

        self._status_bar = statusbar.StatusWidget()
        self.statusBar().setStyleSheet("QStatusBar::item { border: 0px}")
        self.statusBar().addWidget(self._status_bar)

        self.menubar = QMenuBar()
        self._base_layout.addWidget(self.menubar)

        self._base_window = QMainWindow(base_widget)
        self._base_window.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self._base_window.setWindowFlags(Qt.Widget)
        self._base_window.setDockOptions(
            QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)
        self._base_layout.addWidget(self._base_window)
        window_layout = QVBoxLayout()
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(2)
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

    def setup_signals(self):
        """
        Override in derived class to setup signals
        This function is called after ui() function is called
        """

        pass

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

    def dock(self):
        """
        Docks window into main DCC window
        """

        self._dock_widget = MainWindow.DockWindowContainer(self.windowTitle())
        self._dock_widget.setWidget(self)
        tp.Dcc.get_main_window().addDockWidget(Qt.LeftDockWidgetArea, self._dock_widget)
        self.main_title.setVisible(False)

    def add_dock(self, name, widget, pos=Qt.LeftDockWidgetArea, tabify=True):
        """
        Adds a new dockable widet to the window
        :param name: str, name of the dock widget
        :param widget: QWidget, widget to add to the dock
        :param pos: Qt.WidgetArea
        :param tabify: bool, Wheter the new widget should be tabbed to existing docks
        :return: QDockWidget
        """

        # Avoid duplicated docks
        docks = self.get_docks()
        for d in docks:
            if d.windowTitle() == name:
                d.deleteLater()
                d.close()

        dock = QDockWidget()
        dock.setWindowTitle(name)
        dock.setObjectName(name+'Dock')
        dock.setWindowFlags(Qt.Widget)
        dock.setParent(self)
        if widget is not None:
            dock.setWidget(widget)
        self.addDockWidget(pos, dock)

        if docks and tabify:
            self.tabifyDockWidget(docks[-1], dock)

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

    def get_docks(self):
        """
        Returns a list of docked widget
        :return: list<QDockWidget>
        """

        docks = list()
        for child in self.children():
            if isinstance(child, QDockWidget):
                docks.append(child)

        return docks


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
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(2)

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
        super(SubWindow, self).__init__(parent=parent, **kwargs)


class DirectoryWindow(MainWindow, object):
    """
    Window that stores variable to store current working directory
    """

    def __init__(self, parent=None, **kwargs):
        self.directory = None
        super(DirectoryWindow, self).__init__(parent=parent, **kwargs)

    def set_directory(self, directory):
        """
        Sets the directory of the window. If the given folder does not exists, it will created automatically
        :param directory: str, new directory of the window
        """

        self.directory = directory

        if not path.is_dir(directory=directory):
            folder.create_folder(name=None, directory=directory)


