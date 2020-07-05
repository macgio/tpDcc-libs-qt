#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets to to drag PySide windows and dialogs
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpoveda@cgart3d.com"

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc
from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import label


class WindowDragger(QFrame, object):
    """
    Class to create custom window dragger for Solstice Tools
    """

    DEFAULT_LOGO_ICON_SIZE = 22

    def __init__(self, window=None, on_close=None):
        super(WindowDragger, self).__init__(window)

        self._window = window
        self._dragging_enabled = True
        self._lock_window_operations = False
        self._mouse_press_pos = None
        self._mouse_move_pos = None
        self._dragging_threshold = 5
        self._minimize_enabled = True
        self._maximize_enabled = True
        self._on_close = on_close

        self.setObjectName('titleFrame')

        self.ui()

    def ui(self):

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(35, 35, 35))
        self.setPalette(palette)

        self.setFixedHeight(qtutils.dpi_scale(40))
        self.setAutoFillBackground(True)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 0, 15, 0)
        main_layout.setSpacing(5)
        self.setLayout(main_layout)

        self._logo_button = self._setup_logo_button()
        self._title_text = label.ClippedLabel(text=self._window.windowTitle())
        self._title_text.setObjectName('WindowDraggerLabel')
        self._contents_layout = QHBoxLayout()
        self._corner_contents_layout = QHBoxLayout()

        main_layout.addWidget(self._logo_button)
        main_layout.addWidget(self._title_text)
        main_layout.addItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        main_layout.addLayout(self._contents_layout)
        main_layout.addLayout(self._corner_contents_layout)

        buttons_widget = QWidget()
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setAlignment(Qt.AlignRight)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(0)
        buttons_widget.setLayout(self.buttons_layout)
        main_layout.addWidget(buttons_widget)

        self._button_minimized = QPushButton()
        self._button_minimized.setIconSize(QSize(25, 25))
        # self._button_minimized.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_minimized.setIcon(tpDcc.ResourcesMgr().icon('minimize', theme='window'))
        self._button_minimized.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_maximized = QPushButton()
        self._button_maximized.setIcon(tpDcc.ResourcesMgr().icon('maximize', theme='window'))
        # self._button_maximized.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_maximized.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_maximized.setIconSize(QSize(25, 25))
        self._button_restored = QPushButton()
        # self._button_restored.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_restored.setVisible(False)
        self._button_restored.setIcon(tpDcc.ResourcesMgr().icon('restore', theme='window'))
        self._button_restored.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_restored.setIconSize(QSize(25, 25))
        self._button_closed = QPushButton()
        # button_closed.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_closed.setIcon(tpDcc.ResourcesMgr().icon('close', theme='window'))
        self._button_closed.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_closed.setIconSize(QSize(25, 25))

        self.buttons_layout.addWidget(self._button_minimized)
        self.buttons_layout.addWidget(self._button_maximized)
        self.buttons_layout.addWidget(self._button_restored)
        self.buttons_layout.addWidget(self._button_closed)

        self._button_maximized.clicked.connect(self._on_maximize_window)
        self._button_minimized.clicked.connect(self._on_minimize_window)
        self._button_restored.clicked.connect(self._on_restore_window)
        self._button_closed.clicked.connect(self._on_close_window)

    @property
    def contents_layout(self):
        return self._contents_layout

    @property
    def corner_contents_layout(self):
        return self._corner_contents_layout

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging_enabled:
            self._mouse_press_pos = event.globalPos()
            self._mouse_move_pos = event.globalPos() - self._window.pos()
        super(WindowDragger, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            global_pos = event.globalPos()
            if self._mouse_press_pos and self._dragging_enabled:
                moved = global_pos - self._mouse_press_pos
                if moved.manhattanLength() > self._dragging_threshold:
                    diff = global_pos - self._mouse_move_pos
                    self._window.move(diff)
                    self._mouse_move_pos = global_pos - self._window.pos()
        super(WindowDragger, self).mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._lock_window_operations:
            return
        if self._button_maximized.isVisible():
            self._on_maximize_window()
        else:
            self._on_restore_window()

    def mouseReleaseEvent(self, event):
        if self._mouse_press_pos is not None:
            if event.button() == Qt.LeftButton and self._dragging_enabled:
                moved = event.globalPos() - self._mouse_press_pos
                if moved.manhattanLength() > self._dragging_threshold:
                    event.ignore()
                self._mouse_press_pos = None
        super(WindowDragger, self).mouseReleaseEvent(event)

    def set_icon(self, icon, highlight_color=None):
        """
        Sets the icon of the window dragger
        :param icon: QIcon
        """

        if not icon or icon.isNull():
            return

        size = self.DEFAULT_LOGO_ICON_SIZE

        if highlight_color is not None:
            self._logo_button.set_icon(
                [icon], colors=[None], tint_composition=QPainter.CompositionMode_Plus, size=size,
                icon_scaling=[1], color_offset=0, grayscale=True)
        else:
            self._logo_button.set_icon([icon], colors=None, size=size, icon_scaling=[1], color_offset=0)

        self._logo_button.set_icon_idle(icon)

        # self._lbl_icon.setPixmap(icon.pixmap(icon.actualSize(QSize(24, 24))))

    def set_height(self, value):
        """
        Sets the size of the dragger and updates icon
        :param value: float
        """

        self.setFixedHeight(qtutils.dpi_scale(value))

    def set_title(self, title):
        """
        Sets the title of the window dragger
        :param title: str
        """

        self._title_text.setText(title)

    def set_dragging_enabled(self, flag):
        """
        Sets whether or not drag functionality is enabled
        :param flag: bool
        """

        self._dragging_enabled = flag

    def set_minimize_enabled(self, flag):
        """
        Sets whether dragger shows minimize button or not
        :param flag: bool
        """

        self._minimize_enabled = flag
        self._button_minimized.setVisible(flag)

    def set_maximized_enabled(self, flag):
        """
        Sets whether dragger shows maximize button or not
        :param flag: bool
        """

        self._maximize_enabled = flag
        self._button_maximized.setVisible(flag)

    def show_logo(self):
        """
        Shows window logo
        """

        self._logo_button.setVisible(True)

    def hide_logo(self):
        """
        Hides window logo
        """

        self._logo_button.setVisible(False)

    def set_window_buttons_state(self, state):
        """
        Sets the state of the dragger buttons
        :param enabled: bool
        :param visible: bool
        """

        self._lock_window_operations = not state
        self._button_closed.setEnabled(state)
        self._button_closed.setVisible(state)

        if self._maximize_enabled:
            self._button_maximized.setEnabled(state)
            self._button_maximized.setVisible(state)
        else:
            self._button_maximized.setEnabled(False)
            self._button_maximized.setVisible(False)

        if self._minimize_enabled:
            self._button_minimized.setEnabled(state)
            self._button_minimized.setVisible(state)
        else:
            self._button_minimized.setEnabled(False)
            self._button_minimized.setVisible(False)

        if not state:
            self._button_restored.setEnabled(state)
            self._button_restored.setVisible(state)
        else:
            if self.isMaximized():
                self._button_restored.setEnabled(state)
                self._button_restored.setVisible(state)

    def set_frameless_enabled(self, frameless=False):
        """
        Enables/Disables frameless mode or OS system default
        :param frameless: bool
        """

        tool_inst = tpDcc.ToolsMgr().get_tool_by_plugin_instance(self._window)

        offset = QPoint()

        if self._window.docked():
            rect = self._window.rect()
            pos = self._window.mapToGlobal(QPoint(-10, -10))
            rect.setWidth(rect.width() + 21)
            self._window.close()
        else:
            rect = self.window().rect()
            pos = self.window().pos()
            offset = QPoint(3, 15)
            self.window().close()

        tool_inst._launch(launch_frameless=frameless)

        new_tool = tool_inst.latest_tool()

        QTimer.singleShot(
            0, lambda: new_tool.window().setGeometry(
                pos.x() + offset.x(), pos.y() + offset.y(), rect.width(), rect.height()))
        new_tool.framelessChanged.emit(frameless)
        QApplication.processEvents()

        return new_tool

    def _setup_logo_button(self):
        """
        Internal function that setup window dragger button logo
        :return: IconMenuButton
        """

        from tpDcc.libs.qt.widgets import buttons
        logo_button = buttons.IconMenuButton(parent=self)
        logo_button.setIconSize(QSize(24, 24))
        logo_button.setFixedSize(QSize(30, 30))
        self._toggle_frameless = logo_button.addAction(
            'Toggle Frameless Mode', connect=self._on_toggle_frameless_mode, checkable=True)
        self._toggle_frameless.setChecked(self._window.is_frameless())
        logo_button.set_menu_align(Qt.AlignLeft)

        return logo_button

    def _on_toggle_frameless_mode(self, action):
        """
        Internal callback function that is called when switch frameless mode button is pressed by user
        :param flag: bool
        """

        self.set_frameless_enabled(action.isChecked())

    def _on_maximize_window(self):
        """
        Internal callback function that is called when the user clicks on maximize button
        """

        self._button_restored.setVisible(True)
        self._button_maximized.setVisible(False)
        self._window.setWindowState(Qt.WindowMaximized)

    def _on_minimize_window(self):
        """
        Internal callback function that is called when the user clicks on minimize button
        """

        self._window.setWindowState(Qt.WindowMinimized)

    def _on_restore_window(self):
        """
        Internal callback function that is called when the user clicks on restore button
        """

        self._button_restored.setVisible(False)
        self._button_maximized.setVisible(True)
        self._window.setWindowState(Qt.WindowNoState)

    def _on_close_window(self):
        """
        Internal callback function that is called when the user clicks on close button
        """

        closed = False
        if hasattr(self._window, 'WindowId'):
            closed = tpDcc.ToolsMgr().close_tool(self._window.WindowId, force=False)

        if not closed:
            if hasattr(self._window, 'docked'):
                if self._window.docked():
                    self._window.fade_close()
                else:
                    self.window().fade_close()
            else:
                self._window.fade_close()


class DialogDragger(WindowDragger, object):
    def __init__(self, parent=None, on_close=None):
        super(DialogDragger, self).__init__(window=parent, on_close=on_close)

        for btn in [self._button_maximized, self._button_minimized, self._button_restored]:
            btn.setEnabled(False)
            btn.setVisible(False)

    def mouseDoubleClickEvent(self, event):
        return

    def _setup_logo_button(self):
        """
        Internal function that setup window dragger button logo
        :return: IconMenuButton
        """

        from tpDcc.libs.qt.widgets import buttons
        logo_button = buttons.IconMenuButton(parent=self)
        logo_button.setIconSize(QSize(24, 24))
        logo_button.setFixedSize(QSize(30, 30))

        return logo_button
