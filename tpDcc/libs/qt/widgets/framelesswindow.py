#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for frameless windows
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc import register
from tpDcc.libs.qt.core import qtutils, base, window, dragger
from tpDcc.libs.qt.widgets import overlay


class FramelessWindow(window.MainWindow, object):

    dockChanged = Signal(object)
    windowResizedFinished = Signal()
    framelessChanged = Signal(object)

    DRAGGER_CLASS = None

    def __init__(self, title='', width=100, height=100, frameless_checked=True, parent=None):
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

        super(FramelessWindow, self).__init__(
            title=title, width=width, height=height, show_on_initialize=False, transparent=True, parent=parent)

        self._frameless_checked = frameless_checked
        self._current_docked = None
        self._prev_geometry_window = None

        for r in self._resizers:
            r.setParent(self)

        if not frameless_checked:
            self.set_resizers_active(False)
        else:
            self.set_frameless(True)

        self.setProperty('framelessWindow', True)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def setWindowTitle(self, title):
        super(FramelessWindow, self).setWindowTitle(title)
        if hasattr(self, '_dragger'):
            self._dragger.set_title(title)

    def get_main_layout(self):
        main_layout = base.GridLayout()
        main_layout.setHorizontalSpacing(0)
        main_layout.setVerticalSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(FramelessWindow, self).ui()

        self.setMouseTracking(True)

        if self.DRAGGER_CLASS:
            self._dragger = self.DRAGGER_CLASS(window=self)
        else:
            self._dragger = dragger.WindowDragger(window=self)
        self._overlay = FramelessOverlay(
            parent=self, dragger=self._dragger, top_left=self._top_left_resizer, top_right=self._top_right_resizer,
            bottom_left=self._bottom_left_resizer, bottom_right=self._bottom_right_resizer)
        self._overlay.setEnabled(False)
        self._window_contents = FramelessWindowContents()

        for r in self._resizers:
            r.windowResizedFinished.connect(self.windowResizedFinished)
        self.set_resize_directions()

        self.main_layout.addWidget(self._dragger, 1, 1, 1, 1)
        self.main_layout.addWidget(self._window_contents, 2, 1, 1, 1)
        self.main_layout.addWidget(self._top_left_resizer, 0, 0, 1, 1)
        self.main_layout.addWidget(self._top_resizer, 0, 1, 1, 1)
        self.main_layout.addWidget(self._top_right_resizer, 0, 2, 1, 1)
        self.main_layout.addWidget(self._left_resizer, 1, 0, 2, 1)
        self.main_layout.addWidget(self._right_resizer, 1, 2, 2, 1)
        self.main_layout.addWidget(self._bottom_left_resizer, 3, 0, 1, 1)
        self.main_layout.addWidget(self._bottom_resizer, 3, 1, 1, 1)
        self.main_layout.addWidget(self._bottom_right_resizer, 3, 2, 1, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setRowStretch(2, 1)

        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(qtutils.dpi_scale(15))
        shadow_effect.setColor(QColor(0, 0, 0, 150))
        shadow_effect.setOffset(qtutils.dpi_scale(0))
        self.setGraphicsEffect(shadow_effect)

        # self.dockChanged.connect(self.dockEvent)

    def setup_signals(self):
        pass

    # ============================================================================================================
    # BASE
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
        """

        window = self.window()

        if flag and not self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            window.setWindowFlags(window.windowFlags() ^ Qt.WindowMinMaxButtonsHint)
            self.set_resizer_active(True)
        elif not flag and self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            window.setWindowFlags(window.WindowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            self.set_resizer_active(False)

        window.show()

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_window_resized_finished(self):
        pass


class FramelessWindowContents(QFrame, object):
    """
    Widget that defines the core contents of frameless window
    Can be used to custom CSS for frameless windows contents
    """

    def __init__(self, parent=None):
        super(FramelessWindowContents, self).__init__(parent=parent)


class FramelessOverlay(overlay.OverlayWidget, object):
    def __init__(self, parent, dragger, top_left=None, top_right=None, bottom_left=None, bottom_right=None):
        super(FramelessOverlay, self).__init__(parent=parent)

        self._dragger = dragger
        self._top_left = top_left
        self._top_right = top_right
        self._bottom_left = bottom_left
        self._bottom_right = bottom_right
        self._resize_direction = 0


class ResizeDirection:
    """
    Attributes that defines the resizer direction
    """

    Left = 1
    Top = 2
    Right = 4
    Bottom = 8


class WindowResizer(QFrame, object):
    """
    Resizer widgets for windows. Those allow to resize windows from any of their borders
    """

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


register.register_class('FramelessWindow', FramelessWindow)
