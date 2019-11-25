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

import tpQtLib
from tpQtLib.core import qtutils


class WindowDragger(QFrame, object):
    """
    Class to create custom window dragger for Solstice Tools
    """

    DEFAULT_LOGO_ICON_SIZE = 22

    def __init__(self, parent=None, on_close=None):
        super(WindowDragger, self).__init__()

        self._parent = parent
        self._mouse_press_pos = None
        self._mouse_move_pos = None
        self._dragging_threshold = 5
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
        self._title_text = QLabel(self._parent.windowTitle())
        self._title_text.setStyleSheet('background-color: transparent')

        main_layout.addWidget(self._logo_button)
        main_layout.addWidget(self._title_text)
        main_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

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
        self._button_minimized.setIcon(tpQtLib.resource.icon('minimize', theme='window'))
        self._button_minimized.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_maximized = QPushButton()
        self._button_maximized.setIcon(tpQtLib.resource.icon('maximize', theme='window'))
        # self._button_maximized.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_maximized.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_maximized.setIconSize(QSize(25, 25))
        self._button_restored = QPushButton()
        # self._button_restored.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_restored.setVisible(False)
        self._button_restored.setIcon(tpQtLib.resource.icon('restore', theme='window'))
        self._button_restored.setStyleSheet('QWidget {background-color: rgba(255, 255, 255, 0); border:0px;}')
        self._button_restored.setIconSize(QSize(25, 25))
        self._button_closed = QPushButton()
        # button_closed.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self._button_closed.setIcon(tpQtLib.resource.icon('close', theme='window'))
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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mouse_press_pos = event.globalPos()
            self._mouse_move_pos = event.globalPos() - self._parent.pos()
        super(WindowDragger, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            global_pos = event.globalPos()
            if self._mouse_press_pos:
                moved = global_pos - self._mouse_press_pos
                if moved.manhattanLength() > self._dragging_threshold:
                    diff = global_pos - self._mouse_move_pos
                    self._parent.move(diff)
                    self._mouse_move_pos = global_pos - self._parent.pos()
        super(WindowDragger, self).mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._button_maximized.isVisible():
            self._on_maximize_window()
        else:
            self._on_restore_window()

    def mouseReleaseEvent(self, event):
        if self._mouse_press_pos is not None:
            if event.button() == Qt.LeftButton:
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
            self._logo_button.set_icons(
                [icon], colors=[None], tint_composition=QPainter.CompositionMode_Plus, size=size,
                icon_scaling=[1], color_offset=0, grayscale=True)
        else:
            self._logo_button.set_icons([icon], colors=[None, None], size=size, icon_scaling=[1], color_offset=0)

        self._logo_button.set_icon_idle(icon)

        # self._lbl_icon.setPixmap(icon.pixmap(icon.actualSize(QSize(24, 24))))

    def set_title(self, title):
        """
        Sets the title of the window dragger
        :param title: str
        """

        self._title_text.setText(title)

    def _setup_logo_button(self):
        from tpQtLib.widgets import buttons
        logo_button = buttons.IconMenuButton(parent=self)
        logo_button.setIconSize(QSize(24, 24))
        logo_button.setFixedSize(QSize(30, 30))
        # toggle_frameless = logo_button.addAction('Toggle Frameless Mode', connect=self._on_toggle_frameless_mode,  checkable=True)

        return logo_button

    def _on_toggle_frameless_mode(self, action):
        pass

    def _on_maximize_window(self):
        self._button_restored.setVisible(True)
        self._button_maximized.setVisible(False)
        self._parent.setWindowState(Qt.WindowMaximized)

    def _on_minimize_window(self):
        self._parent.setWindowState(Qt.WindowMinimized)

    def _on_restore_window(self):
        self._button_restored.setVisible(False)
        self._button_maximized.setVisible(True)
        self._parent.setWindowState(Qt.WindowNoState)

    def _on_close_window(self):
        self._parent.fade_close()


class DialogDragger(WindowDragger, object):
    def __init__(self, parent=None, on_close=None):
        super(DialogDragger, self).__init__(parent=parent, on_close=on_close)

        for btn in [self._button_maximized, self._button_minimized, self._button_restored]:
            btn.setEnabled(False)
            btn.setVisible(False)

    def mouseDoubleClickEvent(self, event):
        return
