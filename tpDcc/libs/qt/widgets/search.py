#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with search functionality
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.widgets import buttons
from tpDcc.libs.qt.core import resource


class SearchFindWidget(QWidget, object):

    textChanged = Signal(str)
    editingFinished = Signal(str)
    returnPressed = Signal()

    def __init__(self, parent=None):
        super(SearchFindWidget, self).__init__(parent=parent)

        self.setObjectName('SearchFindWidget')

        self.text = ''
        self._placeholder_text = ''

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)

        self._search_line = QLineEdit(self)
        self._search_menu = QMenu()
        self._search_menu.addAction('Test')

        icon_size = self.style().pixelMetric(QStyle.PM_SmallIconSize)

        delete_icon = resource.Resource.icon('delete', extension='png')
        search_icon = resource.Resource.icon('search', extension='png')

        self._clear_btn = buttons.IconButton(delete_icon, icon_padding=2, parent=self)
        self._clear_btn.setIconSize(QSize(icon_size, icon_size))
        self._clear_btn.setFixedSize(QSize(icon_size, icon_size))
        self._clear_btn.hide()

        self._search_btn = buttons.IconButton(search_icon, icon_padding=2, parent=self)
        self._search_btn.setIconSize(QSize(icon_size, icon_size))
        self._search_btn.setFixedSize(QSize(icon_size, icon_size))
        # self._search_btn.setStyleSheet('border: none;')
        # self._search_btn.setPopupMode(QToolButton.InstantPopup)
        self._search_btn.setEnabled(True)

        self._search_line.setStyleSheet(
            """
            QLineEdit { padding-left: %spx; padding-right: %spx; border-radius:10px; border:2px; border-color:red; }
            """ % (self._search_button_padded_width(), self._clear_button_padded_width())
        )
        self._search_line.setMinimumSize(
            max(
                self._search_line.minimumSizeHint().width(),
                self._clear_button_padded_width() + self._search_button_padded_width()),
            max(
                self._search_line.minimumSizeHint().height(),
                max(self._clear_button_padded_width(), self._search_button_padded_width()))
        )

        main_layout.addWidget(self._search_line)

        self._search_line.setFocus()

        self._search_line.textChanged.connect(self.textChanged)
        self._search_line.textChanged.connect(self.set_text)
        # self._search_line.editingFinished.connect(self.editingFinished)
        # self._search_line.returnPressed.connect(self.returnPressed)
        self._clear_btn.clicked.connect(self.clear)
        self._search_btn.clicked.connect(self._popup_menu)

    # def get_text(self):
    #     return self._text
    #
    # def set_text(self, text):
    #     self._text = text
    #
    # text = property(get_text, set_text)

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange:
            enabled = self.isEnabled()
            self._search_btn.setEnabled(enabled and self._search_menu)
            self._search_line.setEnabled(enabled)
            self._clear_btn.setEnabled(enabled)
        super(SearchFindWidget, self).changeEvent(event)

    def resizeEvent(self, event):
        if not (self._clear_btn and self._search_line):
            return
        super(SearchFindWidget, self).resizeEvent(event)
        x = self.width() - self._clear_button_padded_width() * 0.85
        y = (self.height() - self._clear_btn.height()) * 0.5
        self._clear_btn.move(x - 3, y)
        self._search_btn.move(self._search_line_frame_width() * 2, (self.height() - self._search_btn.height()) * 0.5)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.clear()
        super(SearchFindWidget, self).keyPressEvent(event)

    def get_text(self):
        if not self._search_line:
            return ''
        return self._search_line.text()

    def set_text(self, text):
        if not (self._clear_btn and self._search_line):
            return

        self._clear_btn.setVisible(not (len(text) == 0))
        if text != self.get_text():
            self._search_line.setText(text)

    def get_placeholder_text(self):
        if not self._search_line:
            return ''

        return self._search_line.text()

    def set_placeholder_text(self, text):
        if not self._search_line:
            return
        self._search_line.setPlaceholderText(text)

    def get_menu(self):
        search_icon = resource.icon('search')
        self._search_btn.setIcon(search_icon)
        self._search_btn.setEnabled(self.isEnabled() and self._menu)

    def set_focus(self, reason=Qt.OtherFocusReason):
        if self._search_line:
            self._search_line.setFocus(reason)
        else:
            self.setFocus(Qt.OtherFocusReason)

    def clear(self):
        if not self._search_line:
            return
        self._search_line.clear()
        self.set_focus()

    def select_all(self):
        if not self._search_line:
            return
        self._search_line.selectAll()

    def _search_line_frame_width(self):
        return self._search_line.style().pixelMetric(QStyle.PM_DefaultFrameWidth)

    def _clear_button_padded_width(self):
        return self._clear_btn.width() + self._search_line_frame_width() * 2

    def _clear_button_padded_height(self):
        return self._clear_btn.height() + self._search_line_frame_width() * 2

    def _search_button_padded_width(self):
        return self._search_btn.width() + self._search_line_frame_width() * 2

    def _search_button_padded_height(self):
        return self._search_btn.height() + self._search_line_frame_width() * 2

    def _popup_menu(self):
        if self._search_menu:
            screen_rect = QApplication.desktop().availableGeometry(self._search_btn)
            size_hint = self._search_menu.sizeHint()
            rect = self._search_btn.rect()
            top_diff = rect.top() - size_hint.height()
            x = rect.right() - size_hint.width() if self._search_btn.isRightToLeft() else rect.left()
            y = rect.bottom() if self._search_btn.mapToGlobal(
                QPoint(0, rect.bottom())).y() + size_hint.height() <= screen_rect.height() else top_diff
            point = self._search_btn.mapToGlobal(QPoint(x, y))
            point.setX(max(screen_rect.left(), min(point.x(), screen_rect.right() - size_hint.width())))
            point.setY(point.y() + 1)
            print('pop up on {}'.format(point))
            self._search_menu.popup(point)
